class MissionGate:
    def __init__(self, config):
        self.checkpoints = config["execution"]["critical_checkpoints"]

    async def approve_mission(self, plan, ui_callback):
        return await ui_callback(plan)

    def is_checkpoint(self, task):
        return task.get("risk") in self.checkpoints