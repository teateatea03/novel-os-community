"""Validate explicit project speaker configuration without built-in characters."""
from __future__ import annotations


def registry_errors(registry: object, *, require_aliases: bool = False) -> list[str]:
    if not isinstance(registry, dict):
        return ['registry must be an object']
    errors = []
    player_id = registry.get('player_id')
    if not isinstance(player_id, str) or not player_id.strip():
        errors.append('player_id must be an explicit non-empty string')
    actors = registry.get('actors')
    if not isinstance(actors, dict):
        errors.append('actors must be an object')
        actors = {}
    for actor, entry in actors.items():
        if not isinstance(actor, str) or not actor.strip() or not isinstance(entry, dict):
            errors.append('each registered actor must have a non-empty ID and object configuration')
    aliases = registry.get('speaker_aliases')
    if aliases is None and not require_aliases:
        return errors
    if not isinstance(aliases, dict) or not aliases:
        errors.append('speaker_aliases must be a non-empty alias-to-actor mapping')
        return errors
    for label, actor in aliases.items():
        if not isinstance(label, str) or not label.strip() or label != label.strip():
            errors.append('speaker aliases must be non-empty trimmed strings')
        if not isinstance(actor, str) or (actor != player_id and actor not in actors):
            errors.append('every speaker alias must target player_id or a registered actor')
    return errors
