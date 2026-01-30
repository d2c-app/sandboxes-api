import time
from typing import Any, Dict, cast
from dataclasses import dataclass

from kubernetes import client, config, watch


@dataclass(frozen=True)
class SandboxClaim:
    id: str
    template: str
    hostname: str


class AgentSandbox:
    _config_loaded: bool = False

    def __init__(self, namespace: str = "default") -> None:
        self._namespace = namespace

        if not AgentSandbox._config_loaded:
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()
            AgentSandbox._config_loaded = True

        self._custom_api = client.CustomObjectsApi()
        self._v1_api = client.CoreV1Api()

    def claim_sandbox(self, sandbox_id: str, template: str) -> SandboxClaim:
        claim_manifest = {
            "apiVersion": "extensions.agents.x-k8s.io/v1alpha1",
            "kind": "SandboxClaim",
            "metadata": {
                "name": sandbox_id,
                "namespace": self._namespace,
                "labels": {
                    "managed-by": "sandboxes-api",
                    "created-at": str(int(time.time())),
                },
            },
            "spec": {
                "sandboxTemplateRef": {"name": template},
            },
        }

        self._custom_api.create_namespaced_custom_object(
            group="extensions.agents.x-k8s.io",
            version="v1alpha1",
            namespace=self._namespace,
            plural="sandboxclaims",
            body=claim_manifest,
        )

        pod = self._wait_for_ready(sandbox_id)

        hostname = pod.status.pod_ip if pod.status else ""

        claim = SandboxClaim(
            id=sandbox_id,
            template=template,
            hostname=hostname,
        )

        return claim

    def release_sandbox(self, sandbox_id: str) -> None:
        # TODO: Use proper configuration instead of hardcoded values
        self._custom_api.delete_namespaced_custom_object(
            group="extensions.agents.x-k8s.io",
            version="v1alpha1",
            namespace=self._namespace,
            plural="sandboxclaims",
            name=sandbox_id,
        )

    def _wait_for_ready(self, sandbox_id: str) -> client.V1Pod:
        w = watch.Watch()

        for event in w.stream(
            self._v1_api.list_namespaced_pod,
            namespace=self._namespace,
            field_selector=f"metadata.name={sandbox_id}",
        ):
            pod = cast(client.V1Pod, cast(Dict[str, Any], event)["object"])

            if pod.status and pod.status.phase == "Running":
                conditions = pod.status.conditions or []
                is_ready = any(
                    c.type == "Ready" and c.status == "True" for c in conditions
                )
                if is_ready:
                    w.stop()
                    return pod

        raise RuntimeError(
            f"Watch stream ended without pod '{sandbox_id}' becoming ready"
        )
