import json
from llm import ask_llm

PLANNER_PROMPT = """
You are a task planning AI for an autonomous agent.

The agent has ONLY the following tools:
- shell (execute shell commands)
- read_file (read file contents)

Break the user's task into an ordered list of executable steps
that can be completed using ONLY these tools.
You are planning modifications for a Django project.

Rules:
- Always read a file before modifying it.
- Use write_file tool to modify files.
- Do not overwrite entire project.
- Modify only necessary parts.
- Use shell only for manage.py commands.
- Do NOT include human steps like "open editor".
- Do NOT include explanations.
- Each step must be achievable using shell or read_file.
- Steps must be concrete and executable.
- Return valid JSON only.
- Do NOT use echo -e.
- Use printf for newline formatting.
- Output format:

{
  "plan": [
    "step 1",
    "step 2",
    "step 3"
  ]
}

Before modifying any Django file:
- First locate manage.py.
- Then locate the target app directory.
- Then confirm models.py exists.
- Use full correct relative paths.

Environment constraints:
- Shell is /bin/sh (not bash).
- 'bc' is NOT installed.
- Process substitution (<(...)) is NOT supported.
- Use only standard POSIX-compatible commands.
- awk is available.
- seq may or may not be available.
"""


def create_plan(task: str, repo_structure: str):
    messages = [
        {"role": "system", "content": PLANNER_PROMPT},
        {
            "role": "user",
            "content": f"""
    Repository Structure:
    {repo_structure}

    User Task:
    {task}
    """
        }
    ]

    response = ask_llm(messages)
    print("\n🧠 PLANNER RAW:\n", repr(response))  # use repr()

    try:
        parsed = json.loads(response)
        print("Parsed planner JSON:", parsed)
        return parsed.get("plan", [])
    except Exception as e:
        print("Planner JSON parse error:", e)
        return []
