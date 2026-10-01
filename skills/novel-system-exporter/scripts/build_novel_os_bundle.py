#!/usr/bin/env python3
"""Build and verify a portable, dependency-relative Novel OS skill bundle."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
import py_compile
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

VERSION = "2.10.1"
CORE = [
    "long-form-novel-writer", "novel-character-deep-digger", "human-behavior-personality-consultant",
    "novel-worldbuilding-architect", "novel-style-craft-director", "novel-human-voice-editor",
    "knowledge-relationship-graph", "character-database-builder", "immersive-interactive-fiction",
    "unfinished-novel-completion", "novel-world-database-builder", "special-object-database-builder",
    "novel-reality-state-engine", "novel-model-capability-compatibility", "novel-sensory-sound-prose",
    "public-web-research",
]
PACKAGE_SKILLS = ["novel-operating-system", *CORE]
IGNORE_PARTS = {".git", ".DS_Store", "__pycache__", "node_modules", "dist", "build", "payload", "backups"}
IGNORE_SUFFIXES = {".pyc", ".pyo"}
# Deliberately enumerate approved distribution documents, never export docs/*.
# The discussion draft is not an operative license and is not in this list.
REQUIRED_ROOT_NOTICES = ("LICENSE", "THIRD_PARTY.md", "docs/COMMERCIAL_TERMS.md")
REQUIRED_SKILL_NOTICES = ("skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt",)
ROOT_NOTICE_PATHS = (*REQUIRED_ROOT_NOTICES, "LICENSE.md", "LICENSE.txt",
                     "NOTICE", "NOTICE.md", "NOTICE.txt", "docs/COMMERCIAL_LICENSE.md")
NOTICE_NAMES = {"LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.md",
                "COPYING.txt", "NOTICE", "NOTICE.md", "NOTICE.txt", "THIRD_PARTY.md"}
PORTABILITY_DOCUMENTS = ("portable-install.md", "platform-compatibility.md", "host-adapter-contract.md", "bundle-contract.md")
RELEASE_SCRIPTS = ("build_novel_os_bundle.py", "install_novel_os.py", "verify_novel_os.py")

HERE = Path(__file__).resolve().parent
EXPORTER_ROOT = HERE.parent
DEFAULT_SOURCE = EXPORTER_ROOT.parent

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()

def ignored(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    return any(p in IGNORE_PARTS for p in rel.parts) or path.suffix in IGNORE_SUFFIXES or path.name.startswith(".env")

def safe_relative_path(value) -> bool:
    return (isinstance(value, str) and bool(value) and "\\" not in value
            and ":" not in value and "\0" not in value
            and not PurePosixPath(value).is_absolute()
            and all(p not in ("", ".", "..") for p in value.split("/")))

def allowed_payload_path(rel: str) -> bool:
    parts = PurePosixPath(rel).parts
    return (rel in ROOT_NOTICE_PATHS
            or (len(parts) == 2 and parts[0] == "references" and parts[1] in PORTABILITY_DOCUMENTS)
            or (len(parts) == 2 and parts[0] == "scripts" and parts[1] in RELEASE_SCRIPTS)
            or (len(parts) >= 3 and parts[0] == "skills" and parts[1] in PACKAGE_SKILLS))

def regular_file(root: Path, rel: str) -> bool:
    """Do not follow symlinks when reading distributable notices or payloads."""
    if not safe_relative_path(rel): return False
    path = root
    for part in rel.split("/"):
        path = path / part
        if path.is_symlink(): return False
    return path.is_file()

def root_notices(root: Path) -> list[str]:
    selected = []
    for rel in ROOT_NOTICE_PATHS:
        path = root / rel
        if path.exists() or path.is_symlink() or rel in REQUIRED_ROOT_NOTICES:
            if not regular_file(root, rel):
                raise ValueError(f"missing or unsafe distribution notice: {rel}")
            selected.append(rel)
    return sorted(selected)

def is_skill_notice(rel: str) -> bool:
    parts = PurePosixPath(rel).parts
    return (len(parts) >= 3 and parts[0] == "skills" and parts[1] in PACKAGE_SKILLS
            and (parts[-1] in NOTICE_NAMES or "THIRD_PARTY_LICENSES" in parts[2:-1]))

def distribution_notices(root: Path) -> list[str]:
    notices = root_notices(root)
    for rel in REQUIRED_SKILL_NOTICES:
        if not regular_file(root, rel):
            raise ValueError(f"missing or unsafe distribution notice: {rel}")
    for path in root.glob("skills/**/*"):
        rel = path.relative_to(root).as_posix()
        if is_skill_notice(rel) and (path.is_file() or path.is_symlink()):
            if not regular_file(root, rel) or ignored(path, root):
                raise ValueError(f"unsafe or excluded skill notice: {rel}")
            notices.append(rel)
    return sorted(notices)

def notice_errors(root: Path, manifest: dict, expected: dict) -> list[str]:
    errors = []
    declared = manifest.get("distribution_notices")
    if (not isinstance(declared, list) or not declared
            or any(not safe_relative_path(p) for p in declared)
            or len(set(declared)) != len(declared)):
        return ["missing or invalid distribution notice inventory"]
    for rel in (*REQUIRED_ROOT_NOTICES, *REQUIRED_SKILL_NOTICES):
        if rel not in declared: errors.append(f"required distribution notice not declared: {rel}")
    for rel in declared:
        if rel not in ROOT_NOTICE_PATHS and not is_skill_notice(rel):
            errors.append(f"unapproved distribution notice path: {rel}")
        if rel not in expected: errors.append(f"distribution notice not hashed: {rel}")
        if not regular_file(root, rel): errors.append(f"missing or unsafe distribution notice: {rel}")
    try:
        if set(distribution_notices(root)) != set(declared):
            errors.append("distribution notice inventory mismatch")
    except ValueError as error:
        errors.append(str(error))
    return errors

def remove_tree(path: Path) -> None:
    """Remove directories even when the app exposes a link-like virtual path."""
    if path.is_symlink():
        path.unlink()
        return
    if not path.exists():
        return
    # The iSH/App filesystem can reject shutil.rmtree at the directory root
    # with a misleading symbolic-link error. A bounded child-first walk avoids
    # following links and works for both ordinary and virtual directories.
    for child in list(path.iterdir()):
        if child.is_symlink() or not child.is_dir():
            child.unlink()
        else:
            remove_tree(child)
    path.rmdir()


def validate_source_tree(src: Path) -> None:
    if src.is_symlink(): raise SystemExit(f"Source symlink is not distributable: {src}")
    if not src.is_dir():
        raise SystemExit(f"Missing required skill: {src}")
    for path in src.rglob("*"):
        if path.is_symlink(): raise SystemExit(f"Source symlink is not distributable: {path}")

def copy_tree(src: Path, dst: Path) -> None:
    validate_source_tree(src)
    # Never dereference a link even if the source changes after preflight.
    # manifest_for rejects any such copied link before reading file bytes.
    shutil.copytree(src, dst, symlinks=True, ignore=lambda root, names: [n for n in names if ignored(Path(root) / n, src)], dirs_exist_ok=True)

def package_root(value: str | None) -> Path:
    """Resolve an existing package root for verify/build/install use."""
    root = Path(value).expanduser().resolve() if value else EXPORTER_ROOT
    if root.name == "payload": return root
    if (root / "MANIFEST.json").is_file() and (root / "skills").is_dir(): return root
    if (root / "payload").is_dir(): return root / "payload"
    return root

def refresh_root(value: str | None) -> Path:
    """Refresh always writes to a payload directory, never into source skills."""
    base = Path(value).expanduser().resolve() if value else EXPORTER_ROOT
    return base if base.name == "payload" else base / "payload"

def runtime_build(root: Path) -> str:
    """Read the packaged runtime's version without executing its Python code."""
    source = root / "skills/immersive-interactive-fiction/scripts/novel_judge/runtime_versioning.py"
    if not regular_file(root, source.relative_to(root).as_posix()):
        raise ValueError("missing or unsafe packaged runtime version")
    module = ast.parse(source.read_text(encoding="utf-8"))
    values = [node.value for node in module.body
              if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == "RUNTIME_BUILD"
                      for target in node.targets)]
    if len(values) != 1 or not isinstance(values[0], ast.Constant):
        raise ValueError("packaged RUNTIME_BUILD must be one literal string")
    value = values[0].value
    if not isinstance(value, str) or not value.startswith("novel-judge/"):
        raise ValueError("invalid packaged RUNTIME_BUILD")
    return value

def manifest_for(root: Path) -> dict:
    files = []
    for p in sorted(root.rglob("*")):
        if p.is_symlink(): raise ValueError(f"Payload symlink is not distributable: {p.relative_to(root)}")
        if p.is_file() and p.name != "MANIFEST.json" and not ignored(p, root):
            files.append({"path": p.relative_to(root).as_posix(), "sha256": sha(p), "bytes": p.stat().st_size})
    source_versions = {}
    for name in PACKAGE_SKILLS:
        skill = root / "skills" / name / "SKILL.md"
        version = None
        if skill.is_file():
            for line in skill.read_text(encoding="utf-8", errors="replace").splitlines()[:12]:
                if line.startswith("version:"): version = line.split(":", 1)[1].strip(); break
        source_versions[name] = version
    return {"schema":"novel-os-portable.v1", "version":VERSION,
            "built_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "skills":PACKAGE_SKILLS, "skill_count":len(PACKAGE_SKILLS), "source_skill_versions":source_versions,
            "runtime_build":runtime_build(root),
            "runtime_requirements":{"baseline":"LLM skill/document loader","automated":"Python >=3.10 + persistent UTF-8 storage + process runner + branch-scoped cross-process lock (or explicit single-writer mode) + writable WORLD_DATABASE_ROOT/WORLD_DATABASE_WORK_ROOT and SPECIAL_OBJECT_DATABASE_ROOT/SPECIAL_OBJECT_DATABASE_WORK_ROOT when those databases are enabled","graph_optional":"networkx; graphifyy for HTML/community/Cypher export","host_adapter":"replace Minis-only model review adapter outside Minis; preserve behavior Prediction Lock/resolution, calibrated confidence gate, single production authority, seven Gates, candidate-bound TransitionAuthorization, typed semantic events, Quality Eval v2, project readiness, schema migrations, fail-closed routing, durable model activities, replay contracts, storylet solver, event integrity, memory/context and temporal Graph projection"},
            "python":"stdlib core; optional graph packages", "files":files,
            "distribution_notices":distribution_notices(root),
            "exclusions":["private projects", "databases", "secrets", ".git", ".env", "caches"]}

def refresh(args):
    source = Path(args.source_root).expanduser().absolute() if args.source_root else DEFAULT_SOURCE
    if any(path.is_symlink() for path in (source, *source.parents)):
        raise SystemExit("Source skills root must not use symlinks")
    source = source.resolve()
    # Check every skill before creating an output or replacing any old payload.
    for name in PACKAGE_SKILLS: validate_source_tree(source / name)
    root = refresh_root(args.bundle_root)
    # --source-root names the skills directory; legal documents belong to its
    # repository parent. Fail before changing a payload if any are absent.
    notice_source = source.parent
    try: notices = distribution_notices(notice_source)
    except ValueError as error: raise SystemExit(str(error))
    # Do not turn leftover output documents (including discussion drafts) into
    # a new approved manifest. Leave them untouched and request a clean output.
    for path in root.rglob("*"):
        rel = path.relative_to(root).as_posix()
        if (path.is_file() and path.name != "MANIFEST.json" and not ignored(path, root)
                and not allowed_payload_path(rel)):
            raise SystemExit(f"Unexpected existing payload file; use a clean bundle directory: {rel}")
    root.mkdir(parents=True, exist_ok=True)
    for rel in ROOT_NOTICE_PATHS:
        dest = root / rel
        if any(parent.is_symlink() for parent in dest.parents if parent != root.parent):
            raise SystemExit(f"Unsafe notice destination: {rel}")
        if dest.is_symlink() or dest.is_file(): dest.unlink()
        elif dest.exists(): raise SystemExit(f"Notice destination is not a file: {rel}")
        if rel in notices:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(notice_source / rel, dest)
    skills = root / "skills"; skills.mkdir(parents=True, exist_ok=True)
    refs = root / "references"; refs.mkdir(parents=True, exist_ok=True)
    for name in PORTABILITY_DOCUMENTS:
        src = EXPORTER_ROOT / "references" / name
        if not src.is_file(): raise SystemExit(f"Missing mandatory portability document: {src}")
        shutil.copy2(src, refs / name)
    # Refresh every packaged skill, including the coordinator, from the canonical source tree.
    for name in PACKAGE_SKILLS:
        dest = skills / name
        # pathlib's exists() may follow app-managed virtual links; unlink first
        # and only fall back to rmtree for a real directory.
        if dest.is_symlink():
            dest.unlink()
        elif dest.exists():
            remove_tree(dest)
        copy_tree(source / name, dest)
    entry = skills / "novel-operating-system" / "SKILL.md"
    if not entry.exists(): raise SystemExit(f"Missing coordinator entry: {entry}")
    root_scripts = root / "scripts"; root_scripts.mkdir(exist_ok=True)
    for name in RELEASE_SCRIPTS:
        src = EXPORTER_ROOT / "scripts" / name
        if not src.exists(): raise SystemExit(f"Missing exporter runtime: {src}")
        shutil.copy2(src, root_scripts / name)
    # Catch copy filters accidentally dropping or changing upstream notices.
    for rel in notices:
        if not regular_file(root, rel) or sha(root / rel) != sha(notice_source / rel):
            raise SystemExit(f"Distribution notice was not preserved: {rel}")
    (root / "MANIFEST.json").write_text(json.dumps(manifest_for(root), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok":True,"root":str(root),"skills":PACKAGE_SKILLS},ensure_ascii=False))

def verify_root(root: Path, *, compile_python: bool = True) -> list[str]:
    errors=[]; mp=root / "MANIFEST.json"
    if not mp.exists(): return [f"missing manifest: {mp}"]
    try: manifest=json.loads(mp.read_text(encoding="utf-8"))
    except Exception as e: return [f"invalid manifest: {e}"]
    if not isinstance(manifest, dict): return ["invalid manifest object"]
    if manifest.get("schema") != "novel-os-portable.v1": errors.append("unsupported manifest schema")
    entries = manifest.get("files")
    if (not isinstance(entries, list) or not entries
            or any(not isinstance(x, dict) or not safe_relative_path(x.get("path")) for x in entries)):
        return errors + ["invalid payload file inventory"]
    expected={x["path"]:x for x in entries}
    if len(expected) != len(entries): errors.append("duplicate payload file entry")
    actual={p.relative_to(root).as_posix():p for p in root.rglob("*") if p.is_file() and p.name!="MANIFEST.json" and not ignored(p,root)}
    for rel in expected:
        if not regular_file(root, rel): errors.append(f"missing or unsafe payload file: {rel}")
    for rel in set(expected) | set(actual):
        if not allowed_payload_path(rel): errors.append(f"unapproved payload path: {rel}")
    for path in sorted(set(expected)-set(actual)): errors.append(f"missing payload file: {path}")
    for path in sorted(set(actual)-set(expected)): errors.append(f"unexpected payload file: {path}")
    for path, meta in expected.items():
        p=actual.get(path)
        if p and regular_file(root, path) and (sha(p)!=meta.get("sha256") or p.stat().st_size!=meta.get("bytes")): errors.append(f"hash mismatch: {path}")
    errors.extend(notice_errors(root, manifest, expected))
    if manifest.get("skills") != PACKAGE_SKILLS: errors.append("skill manifest mismatch")
    if manifest.get("skill_count") != len(PACKAGE_SKILLS): errors.append("skill count mismatch")
    try:
        if manifest.get("runtime_build") != runtime_build(root): errors.append("runtime build drift")
    except (OSError, UnicodeError, SyntaxError, ValueError):
        errors.append("cannot read packaged runtime build")
    if set((manifest.get("source_skill_versions") or {})) != set(PACKAGE_SKILLS): errors.append("source skill version set mismatch")
    requirements=manifest.get("runtime_requirements",{})
    if not isinstance(requirements,dict) or not requirements.get("automated") or not requirements.get("host_adapter"): errors.append("missing runtime dependency declaration")
    for name in PACKAGE_SKILLS:
        if not (root/"skills"/name/"SKILL.md").is_file(): errors.append(f"missing SKILL.md: {name}")
    for name in PORTABILITY_DOCUMENTS:
        if not (root/"references"/name).is_file(): errors.append(f"missing portability document: references/{name}")
    for name in RELEASE_SCRIPTS:
        if not (root/"scripts"/name).is_file(): errors.append(f"missing release script: scripts/{name}")
    for p in actual.values():
        if compile_python and p.suffix==".py" and regular_file(root, p.relative_to(root).as_posix()):
            try: py_compile.compile(str(p), doraise=True)
            except py_compile.PyCompileError as e: errors.append(f"compile error: {p.relative_to(root)}: {e.msg}")
    return errors

def verify(args):
    root=package_root(args.bundle_root); errors=verify_root(root)
    print(json.dumps({"ok":not errors,"root":str(root),"errors":errors},ensure_ascii=False,indent=2))
    return 0 if not errors else 1

def build(args):
    root=package_root(args.bundle_root)
    if args.refresh:
        refresh(argparse.Namespace(source_root=args.source_root, bundle_root=args.bundle_root))
        root=refresh_root(args.bundle_root)
    errors=verify_root(root)
    if errors:
        print(json.dumps({"ok":False,"errors":errors},ensure_ascii=False,indent=2)); return 1
    output=Path(args.output).expanduser().resolve(); output.parent.mkdir(parents=True,exist_ok=True)
    top=f"novel-os-portable-v{VERSION}"
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(root.rglob("*")):
            if p.is_file() and not ignored(p,root): z.write(p, f"{top}/{p.relative_to(root).as_posix()}")
    print(json.dumps({"ok":True,"output":str(output),"files":len(manifest_for(root)["files"])},ensure_ascii=False)); return 0

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(required=True)
    for cmd in ("refresh",):
        x=sub.add_parser(cmd); x.add_argument("--source-root"); x.add_argument("--bundle-root"); x.set_defaults(func=refresh)
    x=sub.add_parser("verify"); x.add_argument("--bundle-root"); x.set_defaults(func=verify)
    x=sub.add_parser("build"); x.add_argument("--bundle-root"); x.add_argument("--output",required=True); x.add_argument("--refresh",action="store_true"); x.add_argument("--source-root"); x.set_defaults(func=build)
    a=p.parse_args(); result=a.func(a); raise SystemExit(result if isinstance(result,int) else 0)
if __name__=="__main__": main()
