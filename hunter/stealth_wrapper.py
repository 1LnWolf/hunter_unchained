import subprocess
import random
import time
import os

class StealthWrapper:
    def __init__(self, config):
        self.config = config
        self.masquerade = config["stealth"]["process_masquerade"]

    def wrap_execute(self, executable, args, risk):
        if risk not in ("high", "critical"):
            time.sleep(random.uniform(1, 10))
        cmd = [executable]
        if "nmap" in executable:
            cmd += ["-f", "--randomize-hosts", "--scan-delay", f"{random.randint(10, 30)}s"]
        cmd.extend(args)
        if self.masquerade and os.name == "posix":
            fake_name = random.choice(["kworker/u0:0", "jbd2/sda1-8", "systemd-logind"])
            wrapper = ["bash", "-c", f'exec -a "{fake_name}" {" ".join(cmd)}']
            return subprocess.run(wrapper, capture_output=True, text=True, timeout=600)
        return subprocess.run(cmd, capture_output=True, text=True, timeout=600)