import aiohttp
import re
import os
from pathlib import Path
from urllib.parse import quote_plus
from trafilatura import fetch_url, extract

class TopicResearcher:
    def __init__(self, config, kb):
        self.kb = kb
        learning_cfg = config.get("learning", {})
        self.search_provider = learning_cfg.get("search_provider", "duckduckgo")
        self.max_results = learning_cfg.get("max_results", 10)
        self.search_api_key = learning_cfg.get("search_api_key", "")
        self.google_cse_id = learning_cfg.get("google_cse_id", "")
        self.timeout = learning_cfg.get("search_timeout", 10)

    async def search(self, query, num_results=None):
        if num_results is None:
            num_results = self.max_results
        if self.search_provider == "duckduckgo":
            return await self._search_duckduckgo(query, num_results)
        elif self.search_provider == "google":
            return await self._search_google(query, num_results)
        else:
            raise ValueError(f"Unsupported search provider: {self.search_provider}")

    async def _search_duckduckgo(self, query, num_results):
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=self.timeout) as resp:
                html = await resp.text()
        links = re.findall(r'href="(https?://[^"]+)"', html)
        links = [l for l in links if "duckduckgo.com" not in l]
        seen = set()
        unique = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique.append(link)
        return unique[:num_results]

    async def _search_google(self, query, num_results):
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.search_api_key,
            "cx": self.google_cse_id,
            "q": query,
            "num": min(num_results, 10),
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=self.timeout) as resp:
                data = await resp.json()
        return [item["link"] for item in data.get("items", [])]

    async def learn_topic(self, topic: str) -> int:
        links = await self.search(topic)
        docs = []
        for link in links:
            try:
                downloaded = fetch_url(link)
                if downloaded:
                    text = extract(downloaded)
                    if text and len(text) > 100:
                        docs.append((text, {"source": link, "topic": topic}))
            except Exception as e:
                print(f"[!] Failed to process {link}: {e}")
        if docs:
            for text, meta in docs:
                self.kb.add_documents([text], [meta])
        return len(docs)

    async def ingest_local_files(self, directory_path):
        docs = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                full_path = Path(root) / file
                try:
                    if file.endswith(".txt") or file.endswith(".md"):
                        text = full_path.read_text(errors="ignore")
                        docs.append((text, {"source": str(full_path), "type": "local_file"}))
                    elif file.endswith(".pdf"):
                        import pdfplumber
                        with pdfplumber.open(full_path) as pdf:
                            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                        if text:
                            docs.append((text, {"source": str(full_path), "type": "local_file"}))
                except Exception as e:
                    print(f"[!] Failed to read {full_path}: {e}")
        for text, meta in docs:
            self.kb.add_documents([text], [meta])
        return len(docs)