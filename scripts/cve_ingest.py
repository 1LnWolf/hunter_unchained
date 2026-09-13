#!/usr/bin/env python3
import sys, gzip, json, requests
sys.path.append(".")
from hunter.config_loader import load_config
from hunter.knowledge_base import KnowledgeBase

def main():
    config = load_config("hunter_unchained.yaml")
    kb = KnowledgeBase(config)
    url = "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-modified.json.gz"
    print("[*] Downloading NVD modified feed...")
    resp = requests.get(url, timeout=120)
    data = gzip.decompress(resp.content)
    feed = json.loads(data)
    docs = []
    for item in feed.get("CVE_Items", []):
        desc = item["cve"]["description"]["description_data"][0]["value"]
        docs.append(desc)
    if docs:
        kb.add_documents(docs)
        print(f"[+] Ingested {len(docs)} CVEs.")

if __name__ == "__main__":
    main()