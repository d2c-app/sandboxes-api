.PHONY: build-api build-worker load-api load-worker deploy-api deploy-worker

# Build Docker images
build-api:
	docker build -f docker/Dockerfile.api -t sandboxes-api:latest .

build-worker:
	docker build -f docker/Dockerfile.worker -t sandboxes-worker:latest .

# Load images into kind cluster
load-api: build-api
	kind load docker-image sandboxes-api:latest --name d2c-cluster

load-worker: build-worker
	kind load docker-image sandboxes-worker:latest --name d2c-cluster

# Deploy to Kubernetes
deploy-api: load-api
	kubectl rollout restart deployment sandboxes-api

deploy-worker: load-worker
	kubectl rollout restart deployment sandboxes-worker
