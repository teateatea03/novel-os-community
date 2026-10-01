from __future__ import annotations

"""Source-faithful production history reconstruction and cutover support.

Step 3 migration only: rebuilds legacy candidate/checkpoint history as current
runtime events without inventing semantic operations. Each migrated event is a
full-state transition to a source checkpoint and carries legacy provenance.
Normal post-cutover writes still use ProjectRuntimeAdapter.commit().
"""
import copy, hashlib, json, os, shutil, tempfile
from pathlib import Path
from typing import Any

from .canonical import canonical_json, now_iso, refresh_state_hash, sha256_json, stable_id
from .event_log import build_event_index, refresh_active_segment_manifest, verify_event_log_integrity
from .gate_authority import default_gate_policy, make_gate_envelope, evaluate_gate_bundle
from .production import AUTHORITY_SCHEMA, AUTHORITY_MODE, COMMIT_API, LEGACY_WRITER_MODE, ProjectRuntimeAdapter
from .runtime_versioning import stamp_event_contract
from .state import normalize_state

MIGRATION_SCHEMA = "minis.production-history-migration.v1"
PROVENANCE_STATUS = {"ORIGINAL", "ARTIFACT_REVISION", "CANONICAL_CORRECTION", "RECONSTRUCTED_CHECKPOINT", "UNKNOWN"}

def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=f".{path.name}.",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f: f.write(text); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def full_state_operation(target: dict[str, Any]) -> dict[str, Any]:
    value=copy.deepcopy(target)
    for key in ("schema","project_id","session_id","branch_id","canon_scope","revision","state_hash","events_head","last_turn_id"):
        value.pop(key,None)
    return {"op":"replace_snapshot","path":"/","value":value}

def apply_migration_operations(state: dict[str, Any], operations: list[dict[str, Any]]) -> dict[str, Any]:
    from .delta import apply_operations
    out=copy.deepcopy(state); regular=[]
    for op in operations:
        if op.get("op")=="replace_snapshot" and op.get("path")=="/" and isinstance(op.get("value"),dict):
            identity={k:out.get(k) for k in ("schema","project_id","session_id","branch_id","canon_scope")}
            out={**copy.deepcopy(op["value"]),**identity}
        else: regular.append(op)
    if regular: out=apply_operations(out,regular,source="replay")
    return out

def migration_replay(initial_state: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    state=normalize_state(initial_state,verify_hash=False)
    for e in events:
        state=apply_migration_operations(state,e.get("operations",[]))
        state["revision"]=e.get("after_revision",int(state.get("revision",0))+1)
        state["last_turn_id"]=e.get("after_last_turn_id",e.get("turn_id"))
        state["events_head"]=e.get("after_events_head",e.get("event_id"))
        refresh_state_hash(state)
        if state["state_hash"]!=e.get("after_state_hash"): raise ValueError(f"migration replay hash mismatch: {e.get('migration_sequence')}")
    return state

def make_migration_event(*, sequence: int, turn_id: str, source_state: dict[str,Any], target_state: dict[str,Any],
                         provenance_status: str, source_paths: list[str], source_hashes: dict[str,str],
                         legacy_event: dict[str,Any]|None=None, scene_sha256: str|None=None, note: str="") -> dict[str,Any]:
    if provenance_status not in PROVENANCE_STATUS: raise ValueError(provenance_status)
    before=normalize_state(source_state,verify_hash=False); after=normalize_state(target_state,verify_hash=False)
    eid=stable_id("migration-event",sequence,turn_id,after["state_hash"],source_hashes)
    event={"schema":"minis.world-event.v1","event_id":eid,"turn_id":turn_id,
      "idempotency_key":f"step3-migration:{sequence:04d}:{turn_id}","verdict":"allow","intent_id":f"step3-migration-{sequence:04d}",
      "actor_id":str((legacy_event or {}).get("actor_id") or "migration"),"action_type":str((legacy_event or {}).get("action_type") or "reconstructed_checkpoint"),
      "branch_id":after.get("branch_id"),"source":"step3_history_migration","operations":[full_state_operation(after)],
      "scene":{"scene_id":turn_id,"chapter_id":None,"summary":note or None,"source_artifact_hash":scene_sha256,
      "source_artifact_path":(next((p for p in source_paths if p.endswith(f"/{turn_id}.md")),None))} if scene_sha256 else None,
      "costs":copy.deepcopy((legacy_event or {}).get("costs",[])),"delayed_effects":copy.deepcopy((legacy_event or {}).get("delayed_effects",[])),
      "gate_authorization_hash":None,"pre_state_hash":before["state_hash"],"after_state_hash":after["state_hash"],
      "after_revision":after.get("revision"),"after_events_head":after.get("events_head"),"after_last_turn_id":after.get("last_turn_id"),
      "created_at":now_iso(),"migration_sequence":sequence,"migration_provenance":{"schema":"minis.history-provenance.v1","status":provenance_status,
      "legacy_event_id":(legacy_event or {}).get("event_id"),"legacy_pre_state_hash":(legacy_event or {}).get("pre_state_hash"),
      "legacy_after_state_hash":(legacy_event or {}).get("after_state_hash"),"source_paths":source_paths,"source_hashes":source_hashes,"note":note}}
    return stamp_event_contract(event)

def migration_event_semantic_operations(event: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand a migration checkpoint into projector-readable replace ops.

    Only semantic slots are emitted. This is deterministic from the immutable
    target checkpoint and does not claim the original writer recorded each
    field as an individual operation.
    """
    snapshots=[op.get("value") for op in event.get("operations",[]) if isinstance(op,dict) and op.get("op")=="replace_snapshot" and isinstance(op.get("value"),dict)]
    if len(snapshots)!=1: return [op for op in event.get("operations",[]) if isinstance(op,dict) and op.get("op")!="replace_snapshot"]
    state=snapshots[0]; out=[]
    for actor_id, actor in sorted((state.get("actors") or {}).items()):
        if isinstance(actor,dict) and "location" in actor: out.append({"op":"replace","path":f"/actors/{actor_id}/location","value":copy.deepcopy(actor.get("location"))})
    for object_id,obj in sorted((state.get("world_truth",{}).get("objects") or {}).items()):
        if not isinstance(obj,dict): continue
        for key in ("holder","location"):
            if key in obj: out.append({"op":"replace","path":f"/world_truth/objects/{object_id}/{key}","value":copy.deepcopy(obj.get(key))})
    for group in ("player","npcs"):
        for actor_id,facts in sorted((state.get("knowledge",{}).get(group) or {}).items()):
            if isinstance(facts,dict):
                for key,value in sorted(facts.items()): out.append({"op":"replace","path":f"/knowledge/{group}/{actor_id}/{key}","value":copy.deepcopy(value)})
    for relation_id,value in sorted((state.get("relations") or {}).items()):
        out.append({"op":"replace","path":f"/relations/{relation_id}","value":copy.deepcopy(value)})
    return out


def install_reconstructed_history(adapter: ProjectRuntimeAdapter, *, baseline_id: str, baseline_state: dict[str,Any],
                                  events: list[dict[str,Any]], frozen_state: dict[str,Any], frozen_scene_sha256: str,
                                  frozen_turn: str, migration_manifest: dict[str,Any], active: bool=False) -> dict[str,Any]:
    store=adapter.store; baseline=normalize_state(baseline_state,verify_hash=False); frozen=normalize_state(frozen_state,verify_hash=False)
    replayed=migration_replay(baseline,events)
    if replayed["state_hash"]!=frozen["state_hash"]: raise ValueError("frozen state does not match reconstructed replay")
    policy=default_gate_policy(); scene_hash=str(frozen_scene_sha256)
    envelopes=[make_gate_envelope(gate_type=g,turn_id=frozen_turn,scene_sha256=scene_hash,source_state_hash=frozen["state_hash"],details={"migration":"Step 3 historical evidence migration; no retroactive authorization claim"}) for g in policy["required_gate_types"]]
    authorization=evaluate_gate_bundle(envelopes,overrides=[],policy=policy,turn_id=frozen_turn,scene_sha256=scene_hash,source_state_hash=frozen["state_hash"],project_root=adapter.project_root)
    events=copy.deepcopy(events); events[-1]["gate_authorization_hash"]=authorization["authorization_hash"]
    status="active" if active else "shadow"
    with store.transaction_lock():
        if store.authority_path.exists(): raise ValueError("authority already installed")
        # Archive the one-record legacy replacement log; it remains evidence, never authority.
        legacy_archive=store.events_dir/"legacy-replacement-events-pre-step3.jsonl"
        if store.events_path.exists(): shutil.copy2(store.events_path,legacy_archive)
        _atomic_text(store.events_path,"".join(canonical_json(e)+"\n" for e in events))
        refresh_active_segment_manifest(store); build_event_index(store)
        store.save_state(frozen,_authority_token=adapter._authority_token)
        store.write_checkpoint(baseline_id,baseline,_authority_token=adapter._authority_token)
        store.save_manifest({"schema":"minis.interactive-branch-manifest.v1","project_id":adapter.project_id,"session_id":adapter.session_id,"branch_id":adapter.branch_id,
          "baseline_checkpoint":f"state/checkpoints/{baseline_id}.json","baseline_state_hash":baseline["state_hash"],"head_event_id":frozen.get("events_head"),
          "head_state_hash":frozen["state_hash"],"status":"active","updated_at":now_iso()},_authority_token=adapter._authority_token)
        authority={"schema":AUTHORITY_SCHEMA,"mode":AUTHORITY_MODE,"status":status,"canonical_commit_api":COMMIT_API,"store_namespace":adapter.namespace,
          "project_id":adapter.project_id,"session_id":adapter.session_id,"branch_id":adapter.branch_id,"baseline_id":baseline_id,"baseline_state_hash":baseline["state_hash"],
          "legacy_writer_mode":LEGACY_WRITER_MODE,"cutover_performed":bool(active),"gate_policy_path":str(adapter.gate_policy_path.relative_to(adapter.project_root)),
          "gate_policy_hash":sha256_json(policy),"migration_manifest_path":str((store.base/'history-migration.json').relative_to(adapter.project_root)),
          "provenance":{"shadow":not active,"source":"Step 3 sourced history reconstruction","frozen_turn":frozen_turn},"created_at":now_iso()}
        store._atomic_json(store.authority_path,authority); adapter.configure_gate_policy(policy,_initializing=True)
        adapter.gate_bundle_dir.mkdir(parents=True,exist_ok=True); adapter.gate_authorization_dir.mkdir(parents=True,exist_ok=True)
        bundle={"schema":"minis.gate-bundle.v1","turn_id":frozen_turn,"scene_sha256":scene_hash,"source_state_hash":frozen["state_hash"],"envelopes":envelopes,"overrides":[],"authorization":authorization,"created_at":now_iso()}
        bundle_no_hash={k:v for k,v in bundle.items() if k!="bundle_hash"}
        bundle["bundle_hash"]=sha256_json(bundle_no_hash)
        store._atomic_json(adapter.gate_bundle_dir/f"{frozen_turn}.json",bundle);store._atomic_json(adapter.gate_authorization_dir/f"{frozen_turn}.json",authorization)
        migration_manifest={**migration_manifest,"schema":MIGRATION_SCHEMA,"baseline_state_hash":baseline["state_hash"],"frozen_state_hash":frozen["state_hash"],"event_count":len(events),"history_hash":sha256_json(events),"installed_at":now_iso()}
        store._atomic_json(store.base/'history-migration.json',migration_manifest)
        # Preserve the legacy canonical turn/audit files as migration evidence;
        # they are read-only and no longer authorize or receive writes.
        legacy_artifacts=store.base/'legacy-artifacts-pre-step3'
        for label,src in (("turns",store.turns_dir),("audit",store.audit_dir)):
            dst=legacy_artifacts/label
            if src.exists() and not dst.exists(): shutil.copytree(src,dst)
        adapter._sync_authority_projections(state=frozen,event=events[-1],status="recovered",gate_authorization=authorization)
    integrity=verify_event_log_integrity(store)
    return {"status":"installed","authority_status":status,"event_count":len(events),"state_hash":frozen["state_hash"],"integrity":integrity,"replay_state_hash":migration_replay(baseline,events)["state_hash"]}
