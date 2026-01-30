import time
from typing import Any, Dict, cast
from dataclasses import dataclass, field
from kubernetes import client, config, watch


@dataclass(frozen=True)
class SandboxClaim:
    id: str
    template: str
    hostname: str
    exposed_ports: list[int] = field(default_factory=list)


class AgentSandbox:
    def __init__(self, namespace: str = "default") -> None:
        self._namespace = namespace

        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        self._custom_api = client.CustomObjectsApi()
        self._v1_api = client.CoreV1Api()

    def claim_sandbox(
        self, sandbox_id: str, template: str, expose_ports: list[int]
    ) -> SandboxClaim:
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
                "networking": {
                    "service": {
                        "ports": [
                            {"name": f"port-{port}", "port": port, "targetPort": port}
                            for port in expose_ports
                        ]
                    }
                },
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
            exposed_ports=expose_ports,
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
