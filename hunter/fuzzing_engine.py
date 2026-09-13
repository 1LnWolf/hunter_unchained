import asyncio
import docker
import subprocess

class FuzzingEngine:
    def __init__(self, config, gate):
        self.config = config
        self.gate = gate
        self.client = docker.from_env() if config["fuzzing"]["use_docker"] else None

    async def run_fuzzer(self, target_binary, input_corpus, ui_callback):
        task = {
            "tool": "afl-fuzz",
            "arguments": ["-i", input_corpus, "-o", "/tmp/fuzz_out", target_binary, "@@"],
            "reason": f"Fuzzing {target_binary} for new vulnerabilities",
            "risk": "critical"
        }
        if not await self.gate.approve_mission([task], ui_callback):
            return None
        if self.client:
            container = self.client.containers.run(
                "hunter-fuzzer:latest",
                command=f"afl-fuzz -i /input -o /output {target_binary} @@",
                volumes={
                    input_corpus: {'bind': '/input', 'mode': 'ro'},
                    '/tmp/fuzz_out': {'bind': '/output', 'mode': 'rw'}
                },
                detach=True, remove=True
            )
            while True:
                await asyncio.sleep(30)
                status = container.exec_run("ls /output/crashes | wc -l")
                if int(status.output.decode().strip()) > 0:
                    break
            container.kill()
            return "/tmp/fuzz_out/crashes"
        else:
            subprocess.run(
                ["afl-fuzz", "-i", input_corpus, "-o", "/tmp/fuzz_out", target_binary, "@@"],
                timeout=self.config["fuzzing"]["max_campaign_time"]
            )
            return "/tmp/fuzz_out/crashes"