from hunter.sandbox import validate_exploit

class InnovationEngine:
    def __init__(self, config, kb, model):
        self.config = config
        self.kb = kb
        self.model = model

    async def create_novel_technique(self, base_technique):
        mutated_code = await self._mutate_code(base_technique["code"])
        if self.config["innovation"]["sandbox_validation"]:
            if validate_exploit(mutated_code, lang="py"):
                return {"code": mutated_code, "validated": True}
            else:
                return None
        return {"code": mutated_code, "validated": False}

    async def _mutate_code(self, code):
        prompt = f"""Rewrite the following code to be functionally identical but use:
- Different variable names
- Add junk instructions (no-ops, useless loops)
- Change string literals (e.g., obfuscate URLs)
Return ONLY the new code, no explanations.

Original code:
{code}
"""
        new_code = await self.model.generate("You are an expert exploit developer.", prompt)
        new_code = new_code.strip()
        if new_code.startswith("```"):
            lines = new_code.split("\n")
            if len(lines) > 2:
                new_code = "\n".join(lines[1:-1])
        return new_code