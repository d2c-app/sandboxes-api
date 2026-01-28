import time
import json
import subprocess
import yaml
from typing import Dict
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SandboxClaim:
    id: str
    template: str
    hostname: str
    exposed_ports: list[int] = field(default_factory=list)


class AgentSandbox:
    def __init__(self, namespace: str = "default", timeout: int = 60) -> None:
        self.namespace = namespace
        self.timeout = timeout
        self._active_sandboxes: Dict[str, SandboxClaim] = {}

    def claim_sandbox(
        self, sandbox_id: str, template: str, expose_ports: list[int]
    ) -> SandboxClaim:
        """Create a SandboxClaim and wait for it to become ready."""

        claim_manifest = {
            "apiVersion": "extensions.agents.x-k8s.io/v1alpha1",
            "kind": "SandboxClaim",
            "metadata": {
                "name": sandbox_id,
                "namespace": self.namespace,
                "labels": {
                    "managed-by": "sandboxes-api",
                    "created-at": str(int(time.time())),
                },
            },
            "spec": {"sandboxTemplateRef": {"name": template}},
        }

        try:
            manifest_yaml = yaml.dump(claim_manifest)
            subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=manifest_yaml,
                text=True,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to create SandboxClaim '{sandbox_id}': {e.stderr}"
            ) from e
            
        pod_info = self._wait_for_ready(sandbox_id)
        
        hostname = pod_info.get("status", {}).get("podIP", "")
        
        claim = SandboxClaim(
            id=sandbox_id,
            template=template,
            hostname=hostname,
            exposed_ports=expose_ports,
        )
        
        self._active_sandboxes[sandbox_id] = claim
        
        return claim 
        
    def release_sandbox(self, sandbox_id: str) -> None:
        """Delete a SandboxClaim and clean up resources."""
        if sandbox_id not in self._active_sandboxes:
            raise RuntimeError(f"Sandbox '{sandbox_id}' not found in active sandboxes")
        
        try:
            subprocess.run(
                [
                    "kubectl", "delete", "sandboxclaim", sandbox_id,
                    "-n", self.namespace
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to delete SandboxClaim '{sandbox_id}': {e.stderr}"
            ) from e
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"Timeout while deleting SandboxClaim '{sandbox_id}'"
            )
            
        del self._active_sandboxes[sandbox_id]

    def _wait_for_ready(self, sandbox_id: str) -> dict:
        """Poll until the sandbox pod is Running and Ready."""
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            try:
                result = subprocess.run(
                    [
                        "kubectl",
                        "get",
                        "pod",
                        sandbox_id,
                        "-n",
                        self.namespace,
                        "-o",
                        "json",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                pod_info = json.loads(result.stdout)
                phase = pod_info.get("status", {}).get("phase", "Unknown")

                if phase == "Running":
                    # Check if container is actually ready
                    conditions = pod_info.get("status", {}).get("conditions", [])
                    is_ready = any(
                        c.get("type") == "Ready" and c.get("status") == "True"
                        for c in conditions
                    )
                    if is_ready:
                        return pod_info

            except subprocess.CalledProcessError:
                # Pod doesn't exist yet, keep waiting
                pass

            time.sleep(1)

        raise RuntimeError(
            f"Sandbox '{sandbox_id}' did not become ready within {self.timeout}s"
        )
