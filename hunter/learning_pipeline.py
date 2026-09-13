import asyncio
import aiohttp
import feedparser
import json
import gzip
from io import BytesIO
from trafilatura import fetch_url, extract

class LiveLearner:
    def __init__(self, config, kb):
        self.config = config
        self.kb = kb
        self.cve_feed = "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-modified.json.gz"
        self.cisa_kev_url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        self.github_advisories_url = "https://api.github.com/advisories?per_page=100"
        self.rss_feeds = [
            "https://feeds.feedburner.com/TheHackersNews",
            "https://portswigger.net/research/rss",
            "https://krebsonsecurity.com/feed/",
            "https://blog.talosintelligence.com/rss/",
            "https://googleprojectzero.blogspot.com/feeds/posts/default",
            "https://www.bleepingcomputer.com/feed/",
            "https://www.darkreading.com/rss.xml",
        ]
        self.custom_scrape_urls = config["learning"].get("custom_scrape_urls", [])

    async def start(self):
        while True:
            await asyncio.gather(
                self.ingest_cves(),
                self.ingest_cisa_kev(),
                self.ingest_github_advisories(),
                self.ingest_rss(),
                self.ingest_custom_scrapes(),
            )
            await asyncio.sleep(300)

    async def ingest_cves(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.cve_feed) as resp:
                    data = await resp.read()
            with gzip.GzipFile(fileobj=BytesIO(data)) as f:
                feed = json.loads(f.read().decode())
            docs, metas = [], []
            for item in feed.get("CVE_Items", []):
                desc = item["cve"]["description"]["description_data"][0]["value"]
                docs.append(desc)
                metas.append({"id": item["cve"]["CVE_data_meta"]["ID"], "source": "nvd"})
            self.kb.add_documents(docs, metas)
        except Exception as e:
            print(f"[!] CVE ingest error: {e}")

    async def ingest_cisa_kev(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.cisa_kev_url) as resp:
                    data = await resp.json()
            docs, metas = [], []
            for vuln in data.get("vulnerabilities", []):
                text = f"{vuln['cveID']} - {vuln['vulnerabilityName']} - {vuln['shortDescription']}"
                docs.append(text)
                metas.append({"id": vuln['cveID'], "source": "cisa_kev"})
            self.kb.add_documents(docs, metas)
        except Exception as e:
            print(f"[!] CISA KEV ingest error: {e}")

    async def ingest_github_advisories(self):
        try:
            headers = {}
            if self.config["tools"]["github"]["api_token"]:
                headers["Authorization"] = f"token {self.config['tools']['github']['api_token']}"
            async with aiohttp.ClientSession() as session:
                async with session.get(self.github_advisories_url, headers=headers) as resp:
                    data = await resp.json()
            docs, metas = [], []
            for adv in data:
                text = f"{adv['ghsa_id']} - {adv['summary']} - {adv.get('description','')}"
                docs.append(text)
                metas.append({"id": adv['ghsa_id'], "source": "github_advisory"})
            self.kb.add_documents(docs, metas)
        except Exception as e:
            print(f"[!] GitHub Advisories ingest error: {e}")

    async def ingest_rss(self):
        for url in self.rss_feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:5]:
                    text = entry.title + " " + (entry.summary or "")
                    self.kb.add_documents([text], [{"source": url, "type": "rss"}])
            except Exception:
                pass

    async def ingest_custom_scrapes(self):
        for url in self.custom_scrape_urls:
            try:
                downloaded = fetch_url(url)
                text = extract(downloaded)
                if text and len(text) > 100:
                    self.kb.add_documents([text], [{"source": url, "type": "custom_scrape"}])
            except Exception as e:
                print(f"[!] Custom scrape {url} error: {e}")