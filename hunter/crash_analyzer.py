import subprocess
import tempfile

class CrashAnalyzer:
    def analyze_crash(self, crash_file, binary_path):
        gdb_script = f"""
        file {binary_path}
        run < {crash_file}
        exploitable
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gdb') as f:
            f.write(gdb_script)
            f.flush()
            result = subprocess.run(
                ["gdb", "-batch", "-x", f.name],
                capture_output=True, text=True, timeout=60
            )
        output = result.stdout
        if "EXPLOITABLE" in output:
            return {"exploitability": "high", "details": output}
        elif "PROBABLY_EXPLOITABLE" in output:
            return {"exploitability": "medium", "details": output}
        else:
            return {"exploitability": "low", "details": output}