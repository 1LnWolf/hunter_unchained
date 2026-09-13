import docker
import subprocess
import tempfile
import os

def validate_exploit(code, lang, timeout=30):
    client = docker.from_env()
    try:
        container = client.containers.run(
            "hunter-sandbox:latest",
            command="sleep infinity",
            detach=True,
            network_mode="none",
            mem_limit="128m",
            remove=True
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix=f".{lang}", delete=False) as f:
            f.write(code)
            file_path = f.name
        subprocess.run(["docker", "cp", file_path, f"{container.id}:/tmp/exploit.{lang}"])
        exec_cmd = f"timeout {timeout} python3 /tmp/exploit.{lang}" if lang == "py" else f"timeout {timeout} bash /tmp/exploit.{lang}"
        exit_code, _ = container.exec_run(exec_cmd)
        container.kill()
        os.unlink(file_path)
        return exit_code == 0
    except Exception as e:
        print(f"Sandbox error: {e}")
        return False