# Kubernetes Deployment Manifests

This directory contains Kubernetes manifests for deploying the Sandboxes API and Worker.

## Files

- `serviceaccount.yaml` - ServiceAccount for API and Worker pods
- `role.yaml` - Role with permissions to manage SandboxClaim resources
- `rolebinding.yaml` - RoleBinding connecting ServiceAccount to Role
- `configmap.yaml` - Shared configuration for API and Worker
- `api-deployment.yaml` - Deployment for the Sandboxes API
- `api-service.yaml` - Service exposing the API
- `worker-deployment.yaml` - Deployment for the background worker
- `redis-deployment.yaml` - Redis deployment
- `redis-service.yaml` - Redis service

## Prerequisites

1. Build and push Docker images to your container registry:
   ```bash
   # Build images
   docker build -f docker/Dockerfile.api -t your-registry/sandboxes-api:latest .
   docker build -f docker/Dockerfile.worker -t your-registry/sandboxes-worker:latest .
   
   # Push to registry
   docker push your-registry/sandboxes-api:latest
   docker push your-registry/sandboxes-worker:latest
   ```

2. Update image names in the deployment files:
   - `api-deployment.yaml`: Change `image: sandboxes-api:latest`
   - `worker-deployment.yaml`: Change `image: sandboxes-worker:latest`

## Deployment

### Option 1: Deploy all resources

```bash
kubectl apply -f k8s/
```

### Option 2: Deploy in order

```bash
# 1. Create RBAC resources (ServiceAccount, Role, RoleBinding)
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/role.yaml
kubectl apply -f k8s/rolebinding.yaml

# 2. Create ConfigMap
kubectl apply -f k8s/configmap.yaml

# 3. Deploy Redis
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml

# 4. Deploy API and Worker
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
kubectl apply -f k8s/worker-deployment.yaml
```

## Scaling

To scale the API or Worker, simply update the `replicas` field in the respective deployment:

```bash
# Scale API to 3 replicas
kubectl scale deployment sandboxes-api --replicas=3

# Scale Worker to 2 replicas
kubectl scale deployment sandboxes-worker --replicas=2
```

Or edit the deployment files and reapply:
```bash
kubectl apply -f k8s/api-deployment.yaml
```

## Redis

The `redis-deployment.yaml` provides a simple Redis instance suitable for development. It includes health checks and uses an emptyDir volume for data storage.

## Accessing the API

### ClusterIP (Default)

The service is exposed as ClusterIP by default. To access it:

1. **Port Forward**:
   ```bash
   kubectl port-forward service/sandboxes-api-service 8000:80
   ```
   Then access at `http://localhost:8000`

2. **Ingress**: Create an Ingress resource to expose the API externally

3. **LoadBalancer**: Change service type to `LoadBalancer` in `api-service.yaml`

4. **NodePort**: Change service type to `NodePort` in `api-service.yaml`

## Health Checks

The API deployment includes liveness and readiness probes using FastAPI's built-in `/docs` endpoint. For production, consider adding a dedicated `/health` endpoint and updating the probe paths in `api-deployment.yaml`.

## Configuration

Update environment variables in `configmap.yaml` or create a Secret for sensitive values:

```bash
kubectl create secret generic sandboxes-api-secrets \
  --from-literal=RQ_REDIS_URL='redis://redis-service:6379/0'
```

Then reference it in deployments:
```yaml
envFrom:
- configMapRef:
    name: sandboxes-api-config
- secretRef:
    name: sandboxes-api-secrets
```
