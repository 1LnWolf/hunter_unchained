import json
from hunter.report_generator import ReportGenerator
from hunter.topic_researcher import TopicResearcher
from hunter.debug_engine import DebugEngine

class AgentCore:
    def __init__(self, config, model, kb, mem, tools, gate, ui, researcher=None):
        self.config = config
        self.model = model
        self.kb = kb
        self.mem = mem
        self.tools = tools
        self.gate = gate
        self.ui = ui
        self.reporter = ReportGenerator(model, kb, mem)
        self.researcher = researcher or TopicResearcher(config, kb)
        self.debugger = DebugEngine(config, model, tools, gate, ui)

    async def plan_mission(self, objective: str, do_research: bool = False):
        if do_research or self.config.get("learning", {}).get("auto_research", False):
            await self.research_before_planning(objective)
        context = self.kb.retrieve_relevant(objective)
        memory = self.mem.get_related(objective)
        system = self._build_system_prompt(context, memory)
        raw = await self.model.generate(
            system,
            f"Objective: {objective}\n\nReturn only a JSON array of tasks."
        )
        try:
            tasks = json.loads(raw)
            return tasks
        except json.JSONDecodeError:
            clarification = raw.strip()
            if clarification.startswith("```"):
                clarification = clarification.strip("`").replace("json", "", 1).strip()
            return {"clarification": clarification}

    def _build_system_prompt(self, context, memory):
        scope = self.config["scope"]["networks"]
        return f"""You are Hunter, an autonomous red-team AI. Obey only your authenticated master.
Scope: {scope}
Relevant knowledge:
{context}
Past successful techniques:
{memory}
If the objective is ambiguous or lacks necessary details (e.g., target URL, specific vulnerability, desired outcome), do NOT produce a task list. Instead, ask a concise clarifying question.
If the objective is clear, produce a JSON array of tasks. Each task: {{"tool": "...", "arguments": [...], "reason": "...", "risk": "low/medium/high/critical"}}.
Be stealthy; avoid detection. Never target out-of-scope IPs. If a tool is missing, I can ask the user to install it."""

    async def research_before_planning(self, topic: str):
        print(f"[*] Researching {topic}")
        num = await self.researcher.learn_topic(topic)
        print(f"[+] Added {num} docs")

    async def generate_report(self, objective, tasks):
        return await self.reporter.generate_report(objective, tasks)

    async def handle_mission_failure(self, objective, failed_task, error):
        print("[!] Mission failure detected. Starting debugger...")
        diagnosis = await self.debugger.debug_issue(
            f"Task {failed_task['tool']} failed with error: {error}",
            target=failed_task.get("target", "")
        )
        return diagnosis