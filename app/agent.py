from planner import create_plan
import json
import os
from llm import ask_llm
from tools import (ShellTool,
                   ReadFileTool,
                   WriteFileTool,
                   ListDirTool)


TOOLS = {
    "shell": ShellTool(),
    "read_file": ReadFileTool(),
    "write_file": WriteFileTool(),
    "list_dir": ListDirTool(),
}


SYSTEM_PROMPT = """
You are an autonomous AI agent.

Available tools:
- shell: Execute safe shell commands
- read_file: Read file contents

You MUST respond in valid JSON only.

Rules:
- Output must be a single JSON object.
- Do not wrap JSON in markdown.
- Do not add any explanation.
- Do not add extra keys.

If using a tool, respond EXACTLY like:

{
  "action": "tool_name",
  "input": "tool_input"
}

If task is complete, respond EXACTLY like:

{
  "final": "your final answer as a STRING"
}

You may ONLY execute shell commands that directly accomplish the current step.
Do NOT install packages.
Do NOT create virtual environments.
Do NOT modify global environment.
Only operate within the project directory.

IMPORTANT:
- The value of "final" MUST be a string.
- Even if returning multiple items, format them as a single string.
- You may only return ONE JSON object per response.
- If multiple steps are required, perform them one at a time.
- Do not output multiple JSON objects.
"""


# -----------------------------
# JSON helpers
# -----------------------------

def parse_json_response(response: str):
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return None


def validate_response(parsed: dict):
    if not isinstance(parsed, dict):
        return False, "Response is not a JSON object"

    if "final" in parsed:
        if len(parsed.keys()) != 1:
            return False, "Final response contains extra keys"
        if not isinstance(parsed["final"], str):
            return False, "Final value must be string"
        return True, None

    if "action" in parsed and "input" in parsed:
        if len(parsed.keys()) != 2:
            return False, "Tool call contains extra keys"
        if not isinstance(parsed["action"], str):
            return False, "Action must be string"
        if not isinstance(parsed["input"], str):
            return False, "Input must be string"
        return True, None

    return False, "Invalid JSON structure"


def discover_project_structure():

    structure = []
    for root, dirs, files in os.walk(".", topdown=True):
        # Limit depth for safety
        if root.count(os.sep) > 3:
            continue

        structure.append(f"\nDirectory: {root}")
        for d in dirs:
            structure.append(f"  [DIR] {d}")
        for f in files:
            structure.append(f"  [FILE] {f}")

    return "\n".join(structure)


# -----------------------------
# Agent Orchestrator
# -----------------------------

def run_agent(task: str):
    print("\n🔎 Discovering project structure...")

    discovery_info = discover_project_structure()

    print("\n🔍 Generating plan...")
    plan = create_plan(task, discovery_info)

    if not plan:
        print("❌ Failed to generate plan.")
        return

    print("\n📋 PLAN:")
    for i, step in enumerate(plan):
        print(f"{i+1}. {step}")

    task_state = {
        "step_results": [],
        "last_stdout": ""
    }

    for i, step in enumerate(plan):
        print(f"\n🚀 Executing step {i+1}: {step}")
        result = execute_step(step, task_state)

        if result is None:
            print("❌ Step failed. Aborting task.")
            return

        task_state["step_results"].append(result)
        task_state["last_stdout"] = result

    print("\n🎉 All steps executed successfully.")
    print("Final step result:", task_state["step_results"][-1])


# -----------------------------
# Step Executor
# -----------------------------

def execute_step(task: str, task_state: dict):

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""
Current task state:
Last step output:
{task_state.get("last_stdout", "")}

Execute this step:
{task}
"""
        },
    ]

    last_execution_successful = False
    retry_count = 0
    max_retries = 5

    while True:

        if retry_count >= max_retries:
            print("❌ Step exceeded retry limit.")
            return None

        response = ask_llm(messages)
        print("\nMODEL RAW:\n", response)

        parsed = parse_json_response(response)

        if not parsed:
            print("❌ Invalid JSON from model")
            return None

        valid, error = validate_response(parsed)
        if not valid:
            print("❌ Invalid JSON structure:", error)
            return None

        # -------------------------
        # FINAL CASE
        # -------------------------
        if "final" in parsed:
            if not last_execution_successful:
                print("❌ Cannot finalize without successful execution.")
                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": "You must successfully execute a tool before finalizing this step."
                })
                retry_count += 1
                continue

            print("\n✅ STEP COMPLETE:\n", parsed["final"])
            return parsed["final"]

        # -------------------------
        # TOOL CALL CASE
        # -------------------------
        action = parsed["action"]
        tool_input = parsed["input"]

        tool = TOOLS.get(action)
        if not tool:
            print("❌ Unknown tool requested")
            return None

        # 🔒 Enforce read-before-write
        if action == "write_file":
            try:
                data = json.loads(tool_input)
                path = data["path"]
            except Exception as e:
                print("❌ Invalid write_file input format:", e)
                return None

            if path not in task_state.get("files_read", {}):
                print("❌ Cannot write file before reading it.")
                return None
        if action == "shell":
            forbidden = ["pip", "venv", "apt", "yum", "brew", "install"]
            if any(word in tool_input for word in forbidden):
                print("❌ Forbidden system-level command.")
                return None
        print(f"Running tool {action} with input {tool_input}")
        execution_result = tool.run(tool_input)

        print("\n🔧 TOOL RESULT:")
        print(execution_result)

        # 🔁 If read_file succeeded, store content in memory
        if action == "read_file" and execution_result["returncode"] == 0:
            task_state.setdefault("files_read", {})
            task_state["files_read"][tool_input] = execution_result["stdout"]

        # -------------------------
        # FAILURE
        # -------------------------
        if execution_result["returncode"] != 0 or execution_result["stderr"]:
            print("❌ Tool execution failed or produced errors.")
            last_execution_successful = False

            messages.append({"role": "assistant", "content": response})
            messages.append({
                "role": "user",
                "content": f"""
Tool execution failed.

Return code: {execution_result['returncode']}
Stderr: {execution_result['stderr']}

Fix the command and try again.
"""
            })

            retry_count += 1
            continue

        # -------------------------
        # SUCCESS
        # -------------------------
        last_execution_successful = True

        messages.append({"role": "assistant", "content": response})
        messages.append({
            "role": "user",
            "content": f"""
Tool executed successfully.

Stdout:
{execution_result['stdout']}
"""
        })

        retry_count += 1
        continue