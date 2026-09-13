from hunter.fuzzing_engine import FuzzingEngine
from hunter.crash_analyzer import CrashAnalyzer
from hunter.exploit_generator import ExploitGenerator

class VulnDiscoveryEngine:
    def __init__(self, config, kb, gate, tools, model, ui=None):
        self.config = config
        self.kb = kb
        self.gate = gate
        self.tools = tools
        self.model = model
        self.ui = ui
        self.fuzzer = FuzzingEngine(config, gate) if config["fuzzing"]["enabled"] else None
        self.crash_analyzer = CrashAnalyzer()
        self.exploit_gen = ExploitGenerator(config)

    async def discover(self, target_info):
        findings = []
        methods = self._select_methods(target_info)
        for method in methods:
            print(f"[*] Running {method} discovery...")
            result = await getattr(self, f"_run_{method}")(target_info)
            findings.extend(result)
        return findings

    def _select_methods(self, target_info):
        type_ = target_info.get("type")
        methods = []
        if type_ == "binary":
            if self.config["fuzzing"]["enabled"]:
                methods.append("fuzzing")
            if self.config.get("discovery", {}).get("static_analysis", True):
                methods.append("static_binary")
            if self.config.get("discovery", {}).get("symbolic", False):
                methods.append("symbolic")
        elif type_ == "webapp":
            methods.extend(["static_source", "llm_review"])
            if self.config["fuzzing"]["enabled"]:
                methods.append("web_fuzzing")
        elif type_ == "source":
            methods.extend(["static_source", "llm_review"])
        elif type_ == "protocol":
            methods.append("protocol_fuzzing")
        return methods

    async def _run_fuzzing(self, target_info):
        return []

    async def _run_static_binary(self, target_info):
        return []

    async def _run_static_source(self, target_info):
        return []

    async def _run_symbolic(self, target_info):
        return []

    async def _run_llm_review(self, target_info):
        return []

    async def _run_web_fuzzing(self, target_info):
        return []

    async def _run_protocol_fuzzing(self, target_info):
        return []

    async def _validate_findings(self, findings):
        return findings