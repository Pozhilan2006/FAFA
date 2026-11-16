"""Player identity remains a hypothesis until externally confirmed."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class IdentityHypothesis:
    global_player_id: str | None
    confidence: float


class PlayerIdentityResolver(Protocol):
    def resolve(self, track_id: str) -> IdentityHypothesis: ...
