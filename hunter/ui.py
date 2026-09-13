from datetime import datetime
import os
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

class ConsoleUI:
    def __init__(self, config, gate, researcher=None, fuzzing=None, innovation=None, self_defense=None):
        self.config = config
        self.gate = gate
        self.console = Console()
        self.researcher = researcher
        self.fuzzing = fuzzing
        self.innovation = innovation
        self.self_defense = self_defense
        self.mission_tasks = []

    async def run(self, agent):
        self.console.print("[bold red]Hunter Unchained[/]")
        self.console.print("[dim]Model backend auto-detected. Master authenticated.[/]")
        while True:
            user_input = Prompt.ask("Mission objective (or 'research <topic>', 'ingest <path>', 'exit')")
            if user_input.lower() == "exit":
                break
            if user_input.lower().startswith("research "):
                topic = user_input[9:]
                await agent.research_before_planning(topic)
                continue
            if user_input.lower().startswith("ingest "):
                path = user_input[7:]
                num = await agent.researcher.ingest_local_files(path)
                self.console.print(f"[green]Ingested {num} documents from {path}[/]")
                continue

            objective = user_input
            while True:
                if Confirm.ask("Research this topic before planning?", default=False):
                    await agent.research_before_planning(objective)
                plan = await agent.plan_mission(objective)
                if isinstance(plan, dict) and "clarification" in plan:
                    self.console.print(f"[yellow]Hunter needs clarification:[/]\n{plan['clarification']}")
                    answer = Prompt.ask("Your answer (type 'cancel' to abort mission)")
                    if answer.lower() == "cancel":
                        break
                    objective = f"{objective}\n\nClarification: {answer}"
                else:
                    break
            if isinstance(plan, dict) and "clarification" in plan:
                continue

            self.show_plan(plan)
            if not await self.gate.approve_mission(plan, self.approve_callback):
                self.console.print("[red]Mission aborted.[/]")
                continue

            self.mission_tasks = []
            for task in plan:
                if self.gate.is_checkpoint(task):
                    if not Confirm.ask(f"Critical checkpoint: {task['tool']}. Proceed?"):
                        continue
                result = await agent.tools.execute_task(task, ui_callback=self.install_callback)
                if result.get("returncode", 0) != 0 or "error" in result:
                    self.console.print(f"[red]Task failed: {result.get('error') or result.get('stderr')}[/]")
                    await agent.handle_mission_failure(objective, task, result)
                else:
                    self.console.print(f"[green]{task['tool']} done: {result.get('stdout','')[:200]}[/]")
                agent.mem.add_episode(objective, task, result, result.get("returncode", -1) == 0)
                self.mission_tasks.append({"task": task, "result": result})

            if self.config.get("reporting", {}).get("enabled", False):
                report = await agent.generate_report(objective, self.mission_tasks)
                out_dir = self.config["reporting"]["output_dir"]
                os.makedirs(out_dir, exist_ok=True)
                filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(os.path.join(out_dir, filename), "w") as f:
                    f.write(report)
                self.console.print(f"[green]Report saved to {out_dir}/{filename}[/]")

    def show_plan(self, plan):
        table = Table(title="Attack Plan")
        table.add_column("Step")
        table.add_column("Tool")
        table.add_column("Arguments")
        table.add_column("Risk")
        for i, task in enumerate(plan, 1):
            table.add_row(str(i), task["tool"], " ".join(task.get("arguments", [])), task.get("risk", "low"))
        self.console.print(table)

    async def approve_callback(self, plan):
        self.show_plan(plan)
        return Confirm.ask("Execute without further prompts (except checkpoints)?")

    async def install_callback(self, task):
        self.console.print(f"[yellow]Missing tool: {task['arguments']}. Install?[/]")
        return Confirm.ask("Install missing tools?")