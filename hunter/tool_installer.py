import os
import subprocess
import shutil
import tempfile
import yaml

class ToolInstaller:
    def __init__(self, config):
        self.config = config
        self.github_token = config["tools"]["github"]["api_token"]
        self.known_repos = self._load_known_repos()

    def _load_known_repos(self):
        path = self.config["tools"]["github"]["known_repos_file"]
        if os.path.exists(path):
            with open(path) as f:
                return yaml.safe_load(f)
        return {}

    async def find_tool_repo(self, tool_name_or_desc, ui_callback):
        for name, repo in self.known_repos.items():
            if tool_name_or_desc.lower() in name.lower() or tool_name_or_desc.lower() in repo.get("description", "").lower():
                return repo["url"]
        if self.github_token:
            import requests
            headers = {"Authorization": f"token {self.github_token}"}
            r = requests.get(f"https://api.github.com/search/repositories?q={tool_name_or_desc}",
                             headers=headers, timeout=10)
            if r.status_code == 200:
                items = r.json().get("items", [])
                if items:
                    return items[0]["clone_url"]
        url = await ui_callback(f"No repo found for '{tool_name_or_desc}'. Provide GitHub URL:")
        return url

    async def install_from_github(self, repo_url, ui_callback):
        task = {
            "tool": "github_install",
            "arguments": [repo_url],
            "reason": f"Install tool from {repo_url}",
            "risk": "critical"
        }
        if not await ui_callback(task):
            return False
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                ["git", "clone", "--depth",
                 str(self.config["tools"]["github"]["max_clone_depth"]),
                 repo_url, tmpdir],
                check=True, timeout=120
            )
            if os.path.exists(os.path.join(tmpdir, "setup.py")):
                subprocess.run(["pip", "install", "."], cwd=tmpdir, check=True,
                               timeout=self.config["tools"]["github"]["install_timeout"])
            elif os.path.exists(os.path.join(tmpdir, "Makefile")):
                subprocess.run(["make", "install"], cwd=tmpdir, check=True,
                               timeout=self.config["tools"]["github"]["install_timeout"])
            elif os.path.exists(os.path.join(tmpdir, "go.mod")):
                subprocess.run(["go", "install", "."], cwd=tmpdir, check=True,
                               timeout=self.config["tools"]["github"]["install_timeout"])
            else:
                for f in os.listdir(tmpdir):
                    if f.endswith((".py", ".sh")):
                        os.chmod(os.path.join(tmpdir, f), 0o755)
                        shutil.copy(os.path.join(tmpdir, f), "/usr/local/bin/")
            return True