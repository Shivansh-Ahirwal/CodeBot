from agent import run_agent
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the autonomous coding agent.")
    parser.add_argument(
        "task",
        nargs="?",
        help="Task for the agent to execute. If omitted, interactive mode is used."
    )
    args = parser.parse_args()

    task = args.task or input("Enter task: ").strip()
    if not task:
        raise SystemExit("Task cannot be empty.")

    run_agent(task)