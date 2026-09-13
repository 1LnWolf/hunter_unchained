import yaml

def load_config(path: str) -> dict:
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    required = ["master", "scope", "model", "execution"]
    for sec in required:
        if sec not in config:
            raise ValueError(f"Missing config section: {sec}")
    if "provider" not in config["model"]:
        config["model"]["provider"] = "auto"
    if "reporting" not in config:
        config["reporting"] = {"enabled": False, "output_dir": "data/reports/", "format": "markdown"}
    if "learning" not in config:
        config["learning"] = {
            "search_provider": "duckduckgo",
            "max_results": 10,
            "search_api_key": "",
            "google_cse_id": "",
            "search_timeout": 10,
            "auto_research": False,
            "custom_scrape_urls": [],
        }
    if "debugging" not in config:
        config["debugging"] = {"enabled": True, "auto_apply_fixes": False, "collect_system_logs": True}
    if "discovery" not in config:
        config["discovery"] = {
            "static_analysis": True,
            "symbolic_execution": False,
            "llm_code_review": True,
            "patch_diffing": False,
            "taint_analysis": False,
            "max_fuzz_time": 3600,
            "max_symbolic_time": 600,
            "max_static_files": 1000,
        }
    return config