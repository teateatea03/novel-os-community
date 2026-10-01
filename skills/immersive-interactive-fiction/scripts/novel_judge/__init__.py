"""Novel OS deterministic narrative judge core."""
from .agent import run_agent_turn
from .capacity import capacity_budget, capacity_summary
from .contracts import STATE_SCHEMA, INTENT_SCHEMA, DELTA_SCHEMA, TURN_SCHEMA, BRANCH_SCHEMA
from .state import empty_state, normalize_state, validate_state
from .intent import normalize_intent, make_intent, parse_player_text
from .preflight import preflight_intent
from .delta import propose_delta, apply_operations, validate_delta_paths
from .engine import commit_turn, replay_events, recover_store
from .store import FileStore
from .turn import run_turn
from .context import build_context
from .reality import build_reality_card, gate_reality, reality_gate
from .repetition import detect_repetition, validate_no_repetition
from .authority_layers import build_authority_report, classify_findings, LAYERS as AUTHORITY_LAYERS
from .narrative_qa import inspect_prose, validate_generated_output_qa
from .editorial_diagnosis import diagnose_text, diagnose_chapter_file, diagnose_manuscript, make_ticket
from .author_decision import record_author_decision, normalize_author_decision_payload, require_scene_author_decision
from .pairwise_judge import compare_pair, swap_consistency, evaluate_fixture_set, DEFAULT_ADVERSARIAL_FIXTURES
from .cold_read import cold_read_text, record_reader_reaction, open_beta_session, build_beta_questionnaire, summarize_reader_consensus
from .scene_review import review_scene_text
from .scene_goals import inspect_scene_goals
from .playtest_coverage import analyze_playtest_coverage
from .epistemic import visible_facts, knowledge_gate, build_permission_report
from .storylets import available_storylets, storylet_candidates
from .world_tick import candidate_ticks, validate_tick_candidate
from .narrative import validate_prose
from .branches import fork_branch, rewind_branch, promote_branch, branch_affected
from .graph import propose_patch, validate_patch
from .graph_projector import project_events, rebuild_projection
from .memory import make_episode, add_episode, retrieve_memories, compile_memory_context, validate_reflection
from .model_tasks import compile_model_task, validate_model_result
from .migrations import migrate_state, migrate_state_file, migration_path
from .input_router import classify_input, resolve_extractor_candidates
from .plans import make_plan, evaluate_plan, transition_plan, select_ready_plans
from .memory import add_reflection, consolidate_memory, memory_health
from .structured_output import json_schema_for_task, adapter_contract
from .context_budget import (
    estimate_tokens, admit_sources, render_admitted_sources, admit_context_dict,
    CONTEXT_WINDOW_64K, CONTEXT_WINDOW_LARGE, POLICY_LOSSY, POLICY_LOSSLESS,
    DEFAULT_CONTEXT_POLICY, context_policy_for_window, default_context_window,
    default_context_policy,
)
from .fallback_executor import execute_host_fallback
from .longform import init_longform_state, longform_store, longform_adapter, initialize_longform_production, commit_scene_event
from .production import ProjectRuntimeAdapter, production_store, make_candidate_binding, AUTHORITY_SCHEMA, AUTHORITY_MODE, COMMIT_API
from .command_executor import make_author_command, write_author_command, load_author_command, claim_author_command, execute_author_command, fail_author_command, recover_author_commands, author_command_health
from .gate_authority import (
    GATE_ENVELOPE_SCHEMA, GATE_AUTHORIZATION_SCHEMA, GATE_POLICY_VERSION,
    default_gate_policy, make_gate_envelope, make_trusted_gate_envelope, make_author_override,
    validate_gate_envelope, evaluate_gate_bundle, validate_authorization_record,
)
from .observability import runtime_metrics
from .event_log import build_event_index, repair_corrupt_tail, compact_event_log, inspect_jsonl, inspect_jsonl_bytes, verify_event_log_integrity
from .temporal_graph import project_temporal_relations
from .longform_projector import project_longform_markdown, projection_status
from .author_console import author_console_report, render_author_console_markdown
from .author_console_html import render_author_console_html, write_author_console_html
from .project_readiness import project_readiness_report
from .production_inputs import bind_generation_root, record_used_sources, read_used_sources, resolve_writing_inputs_manifest
from .author_feedback import append_author_feedback, read_author_feedback, feedback_status
from .author_corrections import append_correction, read_corrections, recommend_action, active_guards, render_preflight_notes, attach_author_corrections, infer_project_root
from .author_workbench import build_workbench_report, create_command_request, record_author_decision_action
from .author_resume import build_resume_card, load_project_adapter
from .scene_studio import list_scenes, preview_context, inspect_scene_file, save_scene_draft, diff_scene_draft, accept_scene_draft, studio_status, write_workbench_projection
from .manuscript_export import export_manuscript
from .author_quality_eval import build_project_fixtures, evaluate_fixture_dir, production_quality_telemetry, refresh_quality_evaluation
from .semantic_events import compile_semantic_delta, validate_semantic_delta
from .temporal_graph import query_relations_at, relation_history
from .runtime_versioning import RUNTIME_BUILD, replay_compatibility_report, require_replay_compatible, make_replay_fixture
from .model_activities import schedule_model_activity, claim_model_activity, complete_model_activity, cancel_model_activity, recover_model_activities, model_activity_health
from .story_solver import solve_storylets
from .random_events import (
    default_settings as default_random_event_settings,
    load_random_event_settings, set_random_event_mode, validate_random_event_pool,
    suggest_random_event, request_random_suggestion, make_adoption_handoff,
    recover_random_event_audit, random_event_health, calibrate_random_event_pool,
)

__all__ = [
    "STATE_SCHEMA", "INTENT_SCHEMA", "DELTA_SCHEMA", "TURN_SCHEMA", "BRANCH_SCHEMA",
    "empty_state", "normalize_state", "validate_state", "normalize_intent", "make_intent",
    "parse_player_text", "preflight_intent", "propose_delta", "apply_operations",
    "validate_delta_paths", "commit_turn", "replay_events", "recover_store", "FileStore",
    "capacity_budget", "capacity_summary",
    "run_turn", "run_agent_turn", "build_context", "build_reality_card", "gate_reality", "reality_gate", "build_permission_report", "visible_facts",
    "knowledge_gate", "available_storylets", "storylet_candidates", "candidate_ticks",
    "detect_repetition", "validate_no_repetition",
    "build_authority_report", "classify_findings", "AUTHORITY_LAYERS",
    "inspect_prose", "validate_generated_output_qa",
    "diagnose_text", "diagnose_chapter_file", "diagnose_manuscript", "make_ticket",
    "record_author_decision", "normalize_author_decision_payload", "require_scene_author_decision",
    "compare_pair", "swap_consistency", "evaluate_fixture_set", "DEFAULT_ADVERSARIAL_FIXTURES",
    "cold_read_text", "record_reader_reaction", "open_beta_session", "build_beta_questionnaire", "summarize_reader_consensus",
    "review_scene_text",
    "inspect_scene_goals", "analyze_playtest_coverage",
    "validate_tick_candidate", "validate_prose", "fork_branch", "rewind_branch",
    "promote_branch", "branch_affected", "propose_patch", "validate_patch",
    "project_events", "rebuild_projection", "make_episode", "add_episode",
    "retrieve_memories", "compile_memory_context", "validate_reflection",
    "estimate_tokens", "admit_sources", "render_admitted_sources", "admit_context_dict",
    "CONTEXT_WINDOW_64K", "CONTEXT_WINDOW_LARGE", "POLICY_LOSSY", "POLICY_LOSSLESS",
    "DEFAULT_CONTEXT_POLICY", "context_policy_for_window", "default_context_window",
    "default_context_policy",
    "execute_host_fallback",
    "compile_model_task", "validate_model_result",
    "migrate_state", "migrate_state_file", "migration_path", "classify_input", "resolve_extractor_candidates",
    "make_plan", "evaluate_plan", "transition_plan", "select_ready_plans",
    "add_reflection", "consolidate_memory", "memory_health", "json_schema_for_task", "adapter_contract",
    "init_longform_state", "longform_store", "longform_adapter", "initialize_longform_production", "commit_scene_event", "runtime_metrics",
    "ProjectRuntimeAdapter", "production_store", "make_candidate_binding", "AUTHORITY_SCHEMA", "AUTHORITY_MODE", "COMMIT_API",
    "make_author_command", "write_author_command", "load_author_command", "claim_author_command", "execute_author_command", "fail_author_command", "recover_author_commands", "author_command_health",
    "GATE_ENVELOPE_SCHEMA", "GATE_AUTHORIZATION_SCHEMA", "GATE_POLICY_VERSION",
    "default_gate_policy", "make_gate_envelope", "make_trusted_gate_envelope", "make_author_override",
    "validate_gate_envelope", "evaluate_gate_bundle", "validate_authorization_record",
    "build_event_index", "repair_corrupt_tail", "compact_event_log", "inspect_jsonl", "inspect_jsonl_bytes", "verify_event_log_integrity",
    "project_temporal_relations", "project_longform_markdown", "projection_status",
    "author_console_report", "render_author_console_markdown", "render_author_console_html", "write_author_console_html", "project_readiness_report",
    "bind_generation_root", "record_used_sources", "read_used_sources", "resolve_writing_inputs_manifest",
    "append_author_feedback", "read_author_feedback", "feedback_status", "append_correction", "read_corrections", "recommend_action", "active_guards", "render_preflight_notes", "attach_author_corrections", "infer_project_root", "build_workbench_report", "create_command_request", "record_author_decision_action", "build_resume_card", "load_project_adapter", "list_scenes", "preview_context", "inspect_scene_file", "save_scene_draft", "diff_scene_draft", "accept_scene_draft", "studio_status", "write_workbench_projection", "export_manuscript", "build_project_fixtures", "evaluate_fixture_dir", "production_quality_telemetry", "refresh_quality_evaluation",
    "compile_semantic_delta", "validate_semantic_delta",
    "query_relations_at", "relation_history",
    "RUNTIME_BUILD", "replay_compatibility_report", "require_replay_compatible", "make_replay_fixture",
    "schedule_model_activity", "claim_model_activity", "complete_model_activity", "cancel_model_activity", "recover_model_activities", "model_activity_health",
    "solve_storylets",
    "default_random_event_settings", "load_random_event_settings", "set_random_event_mode", "validate_random_event_pool",
    "suggest_random_event", "request_random_suggestion", "make_adoption_handoff", "recover_random_event_audit", "random_event_health", "calibrate_random_event_pool",
]
__version__ = "0.13.8"
