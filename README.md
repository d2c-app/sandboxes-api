# Sandboxes API

> Microservice API for managing sandboxes lifecycle

## Prerequisites

- [uv](https://github.com/astral-sh/uv)

## Setup

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   ```

## Running the app

```bash
uv run api
```

## Testing locally

### Prerequisites

You need a local Kubernetes cluster with the SandboxClaim CRD and operator installed. The example below uses kind:

```bash
# Check if you have a cluster running
kind get clusters

# Verify kubectl is connected
kubectl config current-context

# Check available sandbox templates
kubectl get sandboxtemplates
```

### Testing workflow

1. Start the API:
   ```bash
   uv run api
   ```

2. In another terminal, watch Kubernetes resources:
   ```bash
   kubectl get sandboxclaims,pods -w
   ```

3. Create a sandbox:
   ```bash
   curl -X POST http://localhost:8000/api/v1/sandboxes \
     -H "Content-Type: application/json" \
     -d '{"sandbox_type": "postgres"}'
   ```

   You should see a SandboxClaim and pod being created in your watch terminal.

4. Delete a sandbox:
   ```bash
   curl -X DELETE http://localhost:8000/api/v1/sandboxes/sb-xxxxxxxx
   ```

   You should see the resources being terminated. (Replace sb-xxxxxxxx with the actual sandbox id)

### Important note

The `template` and `expose_ports` variables in `_create_sandbox()` (in [src/sandboxes_api/services/sandboxes.py](src/sandboxes_api/services/sandboxes.py)) are hardcoded for POC purposes and must match what's available in your Kubernetes cluster. Check available templates with `kubectl get sandboxtemplates` and update these variables accordingly.
