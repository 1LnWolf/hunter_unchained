import subprocess
import os
import yaml
from hunter.stealth_wrapper import StealthWrapper
from hunter.safety import validate_scope
from hunter.tool_installer import ToolInstaller
from hunter.self_defense import SelfDefense

DISCOVERABLE_TOOLS = {
    "nmap": {"safe_flags": ["-sV", "-sC", "-p-", "-oX", "-sn", "-f", "--scan-delay"], "dangerous": False},
    "gobuster": {"safe_flags": ["dir", "-u", "-w", "-t", "-o"], "dangerous": False},
    "msfconsole": {"safe_flags": ["-q", "-x", "-r"], "dangerous": True},
    "hydra": {"safe_flags": ["-l", "-P", "-t", "-o"], "dangerous": True},
    "sqlmap": {"safe_flags": ["-u", "--batch", "--level"], "dangerous": True},
    "impacket-secretsdump": {"safe_flags": [], "dangerous": True},
    "curl": {"safe_flags": [], "dangerous": False},
    "wget": {"safe_flags": [], "dangerous": False},
    "python3": {"safe_flags": [], "dangerous": False},
    "msfvenom": {"safe_flags": [], "dangerous": True},
    "bash": {"safe_flags": [], "dangerous": True},
    "systemctl": {"safe_flags": [], "dangerous": True},
    "journalctl": {"safe_flags": [], "dangerous": False},
    "ps": {"safe_flags": [], "dangerous": False},
    "gdb": {"safe_flags": [], "dangerous": False},
}

class ToolOrchestrator:
    def __init__(self, config, gate, self_defense=None):
        self.config = config
        self.gate = gate
        self.stealth = StealthWrapper(config) if config["stealth"]["enable"] else None
        self.self_defense = self_defense or SelfDefense(config)
        self.registry = self._load_registry()
        if config["tools"].get("auto_discover", True):
            self._discover_all_path_tools()
        self.installer = ToolInstaller(config)

    def _load_registry(self):
        with open(self.config["tools"]["registry"], "r") as f:
            return yaml.safe_load(f)

    def _discover_all_path_tools(self):
        risk = self.config["tools"].get("auto_discover_risk", "low")
        for dirpath in os.environ.get("PATH", "").split(os.pathsep):
            if not os.path.isdir(dirpath):
                continue
            for entry in os.listdir(dirpath):
                fullpath = os.path.join(dirpath, entry)
                if os.path.isfile(fullpath) and os.access(fullpath, os.X_OK):
                    if entry not in self.registry:
                        self.registry[entry] = {
                            "path": fullpath,
                            "safe_flags": [],
                            "dangerous": False,
                            "risk": risk,
                            "output_parser": "generic_text"
                        }

    def is_tool_available(self, tool_name: str) -> bool:
        if tool_name in self.registry:
            return os.path.isfile(self.registry[tool_name]["path"])
        return False

    async def install_missing_tools(self, missing_tools, ui_callback):
        if not missing_tools:
            return True
        install_task = {
            "tool": "package_install",
            "arguments": list(missing_tools),
            "reason": f"Missing tools required: {', '.join(missing_tools)}",
            "risk": "critical"
        }
        approved = await ui_callback(install_task)
        if not approved:
            print("[!] Tool installation denied.")
            return False
        for tool in missing_tools:
            if self._try_system_install(tool):
                continue
            repo_url = await self.installer.find_tool_repo(tool, ui_callback)
            if repo_url:
                await self.installer.install_from_github(repo_url, ui_callback)
        return True

    def _try_system_install(self, tool_name):
        try:
            subprocess.run(["sudo", "apt", "install", "-y", tool_name], check=True, timeout=300)
            return True
        except Exception:
            try:
                subprocess.run(["pip", "install", tool_name], check=True, timeout=300)
                return True
            except Exception:
                return False

    def _extract_target(self, args):
        for i, arg in enumerate(args):
            if arg in ("-H", "--host", "-t"):
                if i + 1 < len(args):
                    return args[i + 1]
            elif not arg.startswith("-") and i == len(args) - 1:
                return arg
        return None

    async def execute_task(self, task: dict, ui_callback=None) -> dict:
        tool_name = task["tool"]
        if tool_name == "github_install":
            repo_url = task["arguments"][0]
            success = await self.installer.install_from_github(repo_url, ui_callback)
            return {"stdout": "Installation " + ("successful" if success else "failed"),
                    "returncode": 0 if success else 1}
        if tool_name == "package_install":
            return {"stdout": "Installation handled", "returncode": 0}

        if not self.is_tool_available(tool_name):
            if self.config["tools"].get("allow_dynamic_install", True) and ui_callback:
                can_install = await self.install_missing_tools({tool_name}, ui_callback)
                if not can_install or not self.is_tool_available(tool_name):
                    return {"error": f"Tool {tool_name} not available and could not be installed."}
            else:
                return {"error": f"Tool {tool_name} not available."}

        target = self._extract_target(task.get("arguments", []))
        if not self.self_defense.is_safe_target(target):
            return {"error": "Self-defense blocked target"}

        args = task.get("arguments", [])
        if not validate_scope(task, self.config):
            return {"error": "Out of scope"}

        tool_info = self.registry[tool_name]
        cmd_path = tool_info["path"]
        if self.stealth:
            result = self.stealth.wrap_execute(cmd_path, args, task.get("risk"))
        else:
            result = subprocess.run([cmd_path] + args, capture_output=True, text=True, timeout=600)
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}