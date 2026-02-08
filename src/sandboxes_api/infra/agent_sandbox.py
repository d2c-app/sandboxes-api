import logging
import time
from typing import Any, Dict, cast
from dataclasses import dataclass

from kubernetes import client, config, watch

_logger = logging.getLogger(__name__)


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

        self._wait_for_ready(sandbox_id)

        # The Sandbox controller creates a Service named after the sandbox ID,
        # so use it as the hostname (DNS-resolvable within the cluster).
        hostname = sandbox_id

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

    def _wait_for_ready(self, sandbox_id: str) -> None:
        """Wait for the SandboxClaim to become Ready."""
        w = watch.Watch()

        for event in w.stream(
            self._custom_api.list_namespaced_custom_object,
            group="extensions.agents.x-k8s.io",
            version="v1alpha1",
            namespace=self._namespace,
            plural="sandboxclaims",
            field_selector=f"metadata.name={sandbox_id}",
        ):
            claim = cast(Dict[str, Any], event)["object"]
            conditions = claim.get("status", {}).get("conditions", [])

            is_ready = any(
                c.get("type") == "Ready" and c.get("status") == "True"
                for c in conditions
            )
            if is_ready:
                w.stop()
                return

        raise RuntimeError(
            f"Watch stream ended without sandbox claim '{sandbox_id}' becoming ready"
        )
