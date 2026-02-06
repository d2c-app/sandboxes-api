# Kubernetes Deployment Manifests

This directory contains Kubernetes manifests for deploying the Sandboxes API and Worker.

## Files

- `serviceaccount.yaml` - ServiceAccount for API and Worker pods
- `role.yaml` - Role with permissions to manage SandboxClaim resources
- `rolebinding.yaml` - RoleBinding connecting ServiceAccount to Role
- `configmap.yaml` - Shared configuration for API and Worker
- `secret.yaml` - Secret containing sensitive values (AUTH_KEY)
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

# 3. Create Secret (see Secrets section below)
kubectl apply -f k8s/secret.yaml

# 4. Deploy Redis
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml

# 5. Deploy API and Worker
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

### Ingress & SSL (Recommended)

To expose the API publicly with HTTPS using a static IP and Managed Certificate:

1.  **Reserve a global static IP**:
    ```bash
    gcloud compute addresses create sandboxes-api-ip --global
    ```

2.  **Deploy the resources**:
    ```bash
    # Apply the Service (ClusterIP with NEG), ManagedCertificate, and Ingress
    kubectl apply -f k8s/api-service.yaml
    kubectl apply -f k8s/managed-certificate.yaml
    kubectl apply -f k8s/ingress.yaml
    ```

3.  **Update DNS**:
    Point your domain (`sandboxes.dev2.cloud`) to the static IP address.

4.  **Verify**:
    Wait for the certificate to provision (can take 15-60 minutes). Check status:
    ```bash
    kubectl get managedcertificate sandboxes-api-cert
    kubectl describe ingress sandboxes-api-ingress
    ```

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

### ConfigMap

Update non-sensitive environment variables in `configmap.yaml`:
- `LOG_LEVEL`
- `APP_HOST`
- `APP_PORT`
- `RQ_REDIS_URL`

### Secrets

Sensitive values like `AUTH_KEY` are stored in a Kubernetes Secret. The `secret.yaml` file is provided as a template, but **you should NOT commit actual secret values to git**.

#### Creating the Secret

**Option 1: Using kubectl (Recommended)**
```bash
kubectl create secret generic sandboxes-api-secrets \
  --from-literal=AUTH_KEY='your-actual-auth-key-value'
```

**Option 2: Using the YAML file**
1. Edit `secret.yaml` and replace the empty `AUTH_KEY` value
2. Apply it: `kubectl apply -f k8s/secret.yaml`

**Option 3: From a file**
```bash
kubectl create secret generic sandboxes-api-secrets \
  --from-file=AUTH_KEY=/path/to/auth-key-file
```

#### Updating the Secret

To update the secret value:
```bash
kubectl create secret generic sandboxes-api-secrets \
  --from-literal=AUTH_KEY='new-value' \
  --dry-run=client -o yaml | kubectl apply -f -
```

After updating, restart the pods to pick up the new secret:
```bash
kubectl rollout restart deployment/sandboxes-api
kubectl rollout restart deployment/sandboxes-worker
```

Both deployments are already configured to reference the secret:
```yaml
envFrom:
- configMapRef:
    name: sandboxes-api-config
- secretRef:
    name: sandboxes-api-secrets
```
