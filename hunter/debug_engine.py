import subprocess
import json

class DebugEngine:
    def __init__(self, config, model, tools, gate, ui=None):
        self.config = config
        self.model = model
        self.tools = tools
        self.gate = gate
        self.ui = ui

    async def diagnose(self, error_context: str, extra_logs: str = "") -> dict:
        system_prompt = """You are an expert systems administrator and penetration tester.
Given the error context and log snippets, diagnose the problem and propose a concrete fix.
Your answer must be in JSON: {"diagnosis": "...", "fix_commands": ["cmd1", "cmd2"], "explanation": "..."}
Only suggest commands that are safe and within scope."""
        user_prompt = f"Error context: {error_context}\n\nAdditional logs:\n{extra_logs}"
        raw = await self.model.generate(system_prompt, user_prompt)
        try:
            return json.loads(raw)
        except Exception:
            return {"diagnosis": "Failed to parse model output", "fix_commands": [], "explanation": raw}

    async def run_diagnostics(self, target: str) -> str:
        commands = [
            f"systemctl status {target} --no-pager",
            f"journalctl -u {target} --since '10 minutes ago' --no-pager",
            f"ps aux | grep {target}",
        ]
        output = ""
        for cmd in commands:
            try:
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                output += f"$ {cmd}\n{res.stdout}\n{res.stderr}\n\n"
            except Exception as e:
                output += f"$ {cmd}\nError: {e}\n\n"
        return output

    async def debug_issue(self, issue_description: str, target: str = "") -> dict:
        logs = await self.run_diagnostics(target) if target else ""
        diagnosis = await self.diagnose(issue_description, logs)
        if self.ui and diagnosis.get("fix_commands"):
            print("Diagnosis:", diagnosis["diagnosis"])
            print("Proposed fix commands:")
            for cmd in diagnosis["fix_commands"]:
                print(f"  {cmd}")
            answer = input("Apply these commands? (y/n/modify) ").strip().lower()
            if answer == "y":
                for cmd in diagnosis["fix_commands"]:
                    task = {"tool": "bash", "arguments": [cmd], "reason": "Debugging fix", "risk": "high"}
                    result = await self.tools.execute_task(task, ui_callback=None)
                    print(result.get("stdout", ""))
            elif answer == "modify":
                with open("/tmp/hunter_fix.sh", "w") as f:
                    f.write("\n".join(diagnosis["fix_commands"]))
                print("Saved to /tmp/hunter_fix.sh")
            else:
                print("Fix not applied.")
        return diagnosis