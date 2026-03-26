# CodeBot

A lightweight autonomous coding agent that:
- Creates an execution plan for a user task
- Calls an LLM (Ollama API compatible)
- Executes file/shell tools step-by-step with validation and safety checks

## Production-Ready Structure

```
CodeBot/
  app/
    agent.py        # Orchestrator: runs plan + executes steps
    planner.py      # Plan generation prompt + parser
    llm.py          # LLM client (Ollama-compatible chat API)
    tools.py        # Tool implementations (shell/read/write/list)
    main.py         # CLI entrypoint
    requirements.txt
  Dockerfile
  docker-compose.yml
  .env.example
```

## Architecture

- `main.py` collects the task and starts execution.
- `agent.py` discovers repo structure, asks planner for steps, and executes each step through tool calls.
- `planner.py` asks the LLM for JSON plan output (`{"plan": [...]}`).
- `llm.py` sends chat requests to an Ollama-compatible endpoint.
- `tools.py` provides constrained local actions:
  - `shell`
  - `read_file`
  - `write_file`
  - `list_dir`

The execution loop validates model output JSON and only accepts strict tool/final response formats.

## Requirements

### Software

- Python `3.11+`
- pip `23+`
- Optional: Docker `24+` and Docker Compose plugin `2.20+`
- An LLM backend exposing Ollama chat API (`/api/chat`)

### PC Requirements (Recommended)

- **CPU:** 4 physical cores minimum (8 threads recommended)
- **RAM:** 8 GB minimum, 16 GB recommended
- **Disk:** 2 GB free for app + dependencies; additional space for local model files
- **Network:** required if your LLM endpoint is remote

### OS Support

This project is designed to work on:
- Linux
- macOS
- Windows (recommended via WSL2 for Docker/Ollama workflows)

## Configuration

Copy environment template:

```bash
cp .env.example .env
```

Environment variables:

- `OLLAMA_URL` (default: `http://host.docker.internal:11434/api/chat`)
- `OLLAMA_MODEL` (default: `qwen2.5:7b`)
- `OLLAMA_TIMEOUT_SECONDS` (default: `120`)

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r app/requirements.txt
python app/main.py "Describe and improve this repository safely"
```

If you skip the CLI argument:

```bash
python app/main.py
```

you will be prompted interactively.

## Run With Docker

```bash
docker compose up --build
```

The compose setup mounts `./app` into the container for live code iteration.

## Safety and Behavior Notes

- Shell commands are filtered to block destructive operations.
- File operations are restricted to paths inside the project directory.
- Step execution requires successful tool use before the model can finalize a step.
- Write operations require a read of that file first (enforced in state).

## Development Tips

- Keep prompts strict JSON-only to avoid parser failures.
- Prefer small, verifiable plan steps.
- Add tests for planner/agent JSON validation logic before major changes.

## Troubleshooting

- **Connection error to model endpoint**
  - Verify `OLLAMA_URL` and backend availability.
- **Timeout errors**
  - Increase `OLLAMA_TIMEOUT_SECONDS`.
- **Path access denied**
  - Ensure paths are inside project root and correctly resolved.
