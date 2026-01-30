# Sandboxes API

> Microservice API for managing sandboxes lifecycle

## Prerequisites

- [uv](https://github.com/astral-sh/uv)
- running Redis (for background job processing)
- running Kubernetes cluster with AgentSandbox controller (to spin up sandboxes)

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   ```

## Running

**API Server:**
```bash
uv run api
```

**Worker** (in separate terminal):
```bash
uv run worker
```

For higher concurrency, run multiple workers in separate terminals.
