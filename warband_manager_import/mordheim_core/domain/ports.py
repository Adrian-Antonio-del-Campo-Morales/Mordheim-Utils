from __future__ import annotations

from typing import Protocol, Any


class KnowledgePort(Protocol):
    """UI-independent access to Mordheim reference data.

    The existing KnowledgeRepository is a natural future adapter for this port.
    The prototype does not call it yet.
    """

    def profile(self, band_id: str, profile_id: str) -> dict[str, Any]: ...


class CampaignStorePort(Protocol):
    """Persistence boundary for campaign state.

    Deliberately unspecified at prototype stage: JSON, SQLite or another store
    can implement this later without changing the GUI layer.
    """

    def load(self, campaign_id: str) -> object: ...
    def save(self, campaign: object) -> None: ...
