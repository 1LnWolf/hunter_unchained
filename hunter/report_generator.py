class ReportGenerator:
    def __init__(self, model, kb, mem):
        self.model = model
        self.kb = kb
        self.mem = mem

    async def generate_report(self, objective: str, tasks: list) -> str:
        timeline = ""
        for i, entry in enumerate(tasks):
            task = entry["task"]
            result = entry.get("result", {})
            stdout = result.get("stdout", "")[:300] if isinstance(result, dict) else str(result)[:300]
            timeline += f"{i+1}. Tool: {task['tool']}, Args: {' '.join(task.get('arguments',[]))}\n"
            timeline += f"   Result: {stdout}...\n\n"

        remediation_context = self.kb.retrieve_relevant("remediation " + objective)

        system_prompt = f"""You are a senior penetration tester writing a technical report.
Include: Executive Summary, Methodology, Findings (with evidence), and Recommendations.
Use the provided mission data. Be specific: IPs, ports, CVEs, exploit outcomes.
Format your output in Markdown.

Current knowledge for recommendations:
{remediation_context}
"""
        user_prompt = f"""
Mission objective: {objective}

Timeline of actions:
{timeline}

Write a complete penetration test report in Markdown format.
"""
        return await self.model.generate(system_prompt, user_prompt)