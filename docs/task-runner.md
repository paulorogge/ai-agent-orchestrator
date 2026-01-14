# LM Studio Task Runner (ai-agent-orchestrator-lmstudio-task-runner)

This repository ships a task runner CLI that uses a real LLM via the LM Studio
OpenAI-compatible server.

## Install

From this repo:

```bash
pip install -e ".[dev,lmstudio]"
```

From another project, install the orchestration library via git and your app
dependencies:

```bash
pip install "ai-agent-orchestrator @ git+https://github.com/openai/ai-agent-orchestrator.git"
```

## Run LM Studio

1. Launch LM Studio and start the local OpenAI-compatible server.
2. Note the model name shown in LM Studio.
3. Export your environment variables (see `.env.example`).

```bash
export LMSTUDIO_MODEL="your-model-name"
export LMSTUDIO_BASE_URL="http://localhost:1234/v1"
export WORKSPACE_DIR="workspace"
```

## CLI examples

```bash
task-runner "Add a high priority task to draft the launch email."
```

```bash
task-runner "List my current tasks."
```
