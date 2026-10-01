#!/usr/bin/env python3
"""Validate Novel Character Deep Digger v1.7 profile JSON."""
import argparse, json, sys
from pathlib import Path

COMMON = ["subject_category", "character_importance", "work_stage", "profile_depth", "model_status", "story_questions", "identity_scope", "current_goal", "visible_obstacle", "agency", "behavior_anchors"]
L1 = ["strategy_cost", "relationship_variation", "voice_cues", "conditional_reactions", "capabilities_limits"]
L2 = ["competing_models", "state_distribution", "formation_history", "arc_candidates", "relationship_map", "source_families"]

def filled(v):
    return v is not None and v != "" and v != [] and v != {}

def validate(d):
    e, w = [], []
    for k in COMMON:
        if not filled(d.get(k)): e.append(f"missing:{k}")
    if d.get("subject_category") not in {"real","novel","anime","film","other"}: e.append("invalid:subject_category")
    if d.get("character_importance") not in {"lead","major_supporting","minor_functional"}: e.append("invalid:character_importance")
    if d.get("work_stage") not in {"discovery","draft_diagnostic","revision"}: e.append("invalid:work_stage")
    depth = d.get("profile_depth")
    if depth not in {"L0","L1","L2"}: e.append("invalid:profile_depth")
    tests = d.get("validation_tests", [])
    types = {x.get("type") for x in tests if isinstance(x, dict)}
    if depth in {"L1","L2"}:
        for k in L1:
            if not filled(d.get(k)): e.append(f"missing:{k}")
        if len(tests) < 1: e.append("gate:L1_requires_validation_test")
    if depth == "L2":
        for k in L2:
            if not filled(d.get(k)): e.append(f"missing:{k}")
        if len(d.get("competing_models", [])) < 2: e.append("gate:L2_requires_two_competing_models")
        if len(tests) < 3: e.append("gate:L2_requires_three_validation_tests")
        if "counterexample" not in types: e.append("gate:L2_requires_counterexample_test")
        if not ({"contrast_scene", "voice_blind"} & types): e.append("gate:L2_requires_contrast_or_voice_test")
    if depth in {"L1","L2"} and d.get("model_status") == "MODEL_DRAFT":
        e.append("gate:tested_depth_cannot_remain_MODEL_DRAFT")
    if d.get("model_status") not in {"MODEL_DRAFT","SCENE_TESTED","REVISION_CALIBRATED"}: e.append("invalid:model_status")
    questions = d.get("story_questions", [])
    if isinstance(questions, list) and not 1 <= len(questions) <= 3: e.append("gate:story_questions_must_be_1_to_3")
    reactions = d.get("conditional_reactions", [])
    if depth in {"L1","L2"} and len(reactions) < 2: e.append("gate:L1_requires_two_conditional_reactions")
    seen = {}
    for sf in d.get("source_families", []):
        sid, url = sf.get("source_family_id"), sf.get("original_source_url")
        if not sid or not url: e.append("missing:source_family_id_or_original_source_url"); continue
        if url in seen and seen[url] != sid: e.append(f"gate:duplicate_original_split_across_families:{url}")
        seen[url] = sid
    if depth == "L0" and not tests: w.append("MODEL_DRAFT allowed: L0 has no scene validation")
    return e, w

def main():
    p=argparse.ArgumentParser(); p.add_argument("profile"); a=p.parse_args()
    d=json.loads(Path(a.profile).read_text(encoding="utf-8")); e,w=validate(d)
    print(json.dumps({"valid":not e,"errors":e,"warnings":w},ensure_ascii=False,indent=2))
    return 1 if e else 0
if __name__ == "__main__": sys.exit(main())
