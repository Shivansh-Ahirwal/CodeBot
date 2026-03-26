import subprocess
import os
from pathlib import Path
from typing import Dict


class Tool:
    name = ""
    description = ""

    def run(self, input: str):
        raise NotImplementedError


class ShellTool(Tool):
    name = "shell"
    description = "Execute safe shell commands"

    def run(self, input: str):
        blocked = ["rm ", "shutdown", "reboot", "mkfs", "dd ", ":(){", "poweroff"]

        if any(cmd in input for cmd in blocked):
            return {
                "stdout": "",
                "stderr": "Command blocked for safety.",
                "returncode": 1
            }

        project_root = Path.cwd().resolve()
        try:
            result = subprocess.run(
                input,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(project_root),
                timeout=60
            )
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Command timed out after 60 seconds.",
                "returncode": 1
            }

        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }


class ReadFileTool(Tool):
    name = "read_file"
    description = "Read file contents"

    def run(self, input: str) -> Dict[str, object]:
        target = Path(input).resolve()
        project_root = Path.cwd().resolve()

        if project_root not in target.parents and target != project_root:
            return {
                "stdout": "",
                "stderr": "Access denied. Path must be inside project directory.",
                "returncode": 1
            }

        if not os.path.exists(target):
            return {
                "stdout": "",
                "stderr": "File not found.",
                "returncode": 1
            }

        with open(target, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "stdout": content.strip(),
            "stderr": "",
            "returncode": 0
        }


class WriteFileTool:
    def run(self, input_str: str) -> Dict[str, object]:
        try:
            import json
            data = json.loads(input_str)
            path = Path(data["path"]).resolve()
            content = data["content"]
            project_root = Path.cwd().resolve()

            if project_root not in path.parents and path != project_root:
                return {
                    "stdout": "",
                    "stderr": "Access denied. Path must be inside project directory.",
                    "returncode": 1
                }

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return {"stdout": "File written", "stderr": "", "returncode": 0}

        except Exception as e:
            return {"stdout": "", "stderr": str(e), "returncode": 1}


class ListDirTool:
    def run(self, input_str: str) -> Dict[str, object]:
        try:
            path = Path(input_str.strip() or ".").resolve()
            project_root = Path.cwd().resolve()
            if project_root not in path.parents and path != project_root:
                return {
                    "stdout": "",
                    "stderr": "Access denied. Path must be inside project directory.",
                    "returncode": 1
                }

            items = os.listdir(path)
            return {"stdout": "\n".join(items), "stderr": "", "returncode": 0}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "returncode": 1}
