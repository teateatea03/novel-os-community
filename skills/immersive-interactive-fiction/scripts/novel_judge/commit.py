"""Backward-compatible commit facade."""
from .engine import commit_turn, recover_store, replay_events


class Judge:
    """Small compatibility facade around the standard-library judge engine."""
    def __init__(self, store):
        self.store = store

    def commit(self, intent, **kwargs):
        return commit_turn(self.store, intent, **kwargs)

    def recover(self):
        return recover_store(self.store)


__all__ = ["Judge", "commit_turn", "recover_store", "replay_events"]
