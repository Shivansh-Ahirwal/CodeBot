import subprocess
import os


class Tool:
    name = ""
    description = ""

    def run(self, input: str):
        raise NotImplementedError


class ShellTool(Tool):
    name = "shell"
    description = "Execute safe shell commands"

    def run(self, input: str):
        blocked = ["rm ", "shutdown", "reboot", "mkfs", "dd "]

        if any(cmd in input for cmd in blocked):
            return {
                "stdout": "",
                "stderr": "Command blocked for safety.",
                "returncode": 1
            }

        result = subprocess.run(
            input,
            shell=True,
            capture_output=True,
            text=True
        )

        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }


class ReadFileTool(Tool):
    name = "read_file"
    description = "Read file contents"

    def run(self, input: str):
        if not os.path.exists(input):
            return {
                "stdout": "",
                "stderr": "File not found.",
                "returncode": 1
            }

        with open(input, "r") as f:
            content = f.read()

        return {
            "stdout": content.strip(),
            "stderr": "",
            "returncode": 0
        }


class WriteFileTool:
    def run(self, input_str: str):
        try:
            import json
            data = json.loads(input_str)
            path = data["path"]
            content = data["content"]

            with open(path, "w") as f:
                f.write(content)

            return {"stdout": "File written", "stderr": "", "returncode": 0}

        except Exception as e:
            return {"stdout": "", "stderr": str(e), "returncode": 1}
