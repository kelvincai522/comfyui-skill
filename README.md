# ComfyUI Skill for OpenClaw

Run local ComfyUI workflows via the HTTP API. The agent edits workflow JSON (prompt, style, seed) then queues and polls using the bundled script.

## Prerequisites

- **ComfyUI** installed and runnable (e.g. `~/ComfyUI` with a venv). The skill can guide the user to install it if the server is not reachable.
- **Python 3** with the ComfyUI venv (use `~/ComfyUI/venv/bin/python`; do not rely on bare `python` on PATH).

## What this skill does

- Instructs the agent to read workflow JSON, find prompt/style/sampler nodes, edit them, and write a temp workflow file.
- Runs `comfyui_run.py` to queue the workflow and poll until completion.
- Tells the agent to send generated images back to the user and how to recover if the ComfyUI server is not running.

## Layout

```
comfyui/
├── SKILL.md           # Main instructions for the agent
├── README.md          # This file
├── CONTRIBUTING.md    # Where to report issues
├── .clawhub/
│   └── origin.json    # ClawHub slug and version
├── scripts/
│   ├── comfyui_run.py       # Queue workflow, poll, print images
│   └── download_weights.py  # Download model weight URLs to ComfyUI/models/
└── assets/
    ├── default-workflow.json  # Example workflow
    └── tmp-workflow.json      # Written by agent (editable)
```

## Publishing to ClawHub

The skill **only appears on ClawHub after you publish it**. Until then it exists only locally.

1. Install the CLI: `npm i -g clawhub`
2. Log in: `clawhub login` (GitHub account must be at least one week old to publish)
3. From the workspace root (parent of `skills/`):
   ```bash
   clawhub publish ./skills/comfyui --slug comfyui --name "ComfyUI" --version 1.0.1 --changelog "Describe changes"
   ```
4. For later updates, bump the version (e.g. `1.0.2`) and run the same command with a new `--changelog`.

**Finding your skill:** Open [clawhub.ai](https://clawhub.ai), search for **comfyui** or **ComfyUI**, or check your profile for published skills. Install with: `clawhub install comfyui`
