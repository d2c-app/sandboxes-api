from dataclasses import dataclass, field


@dataclass
class SandboxClaim:
    id: str
    template: str
    hostname: str
    exposed_ports: list[int] = field(default_factory=list)


class AgentSandbox:
    def __init__(self):
        # TODO: Configure access to Kubernetes
        pass

    def claim_sandbox(
        self, sandbox_id: str, template: str, expose_ports: list[int]
    ) -> SandboxClaim:
        # TODO: Claim sandbox
        pass

    def release_sandbox(self, sandbox_id: str) -> None:
        # TODO: Release sandbox
        pass
