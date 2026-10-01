from __future__ import annotations

"""Export a read-only manuscript copy. Never rewrites canonical prose."""

import html
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from .canonical import now_iso, sha256_json

EXPORT_SCHEMA = "minis.manuscript-export.v1"
_MD_HEADING = re.compile(r"^#\s+(.+)$", re.M)


def _collect_documents(project_root: Path) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    chapter_dir = project_root / "chapters"
    scene_dir = project_root / "interactive" / "scenes"
    if chapter_dir.is_dir() and any(chapter_dir.glob("*.md")):
        paths = sorted(chapter_dir.glob("*.md"))
        kind = "chapter"
    elif scene_dir.is_dir():
        paths = sorted(scene_dir.glob("*.md"))
        kind = "scene"
    else:
        paths = sorted((project_root / "scenes").glob("*.md")) if (project_root / "scenes").is_dir() else []
        kind = "scene"
    for index, path in enumerate(paths, start=1):
        text = path.read_text(encoding="utf-8")
        title_match = _MD_HEADING.search(text)
        title = (title_match.group(1).strip() if title_match else path.stem)
        docs.append({
            "index": index,
            "id": path.stem,
            "kind": kind,
            "title": title,
            "path": str(path.relative_to(project_root)),
            "text": text,
            "chars": len(text),
        })
    return docs


def _markdown_book(title: str, docs: list[dict[str, Any]], *, frozen: bool) -> str:
    lines = [f"# {title}", "", f"_匯出複本，非正式正典。frozen={frozen}_", ""]
    for doc in docs:
        lines.append(f"## {doc['index']:04d} · {doc['title']}")
        lines.append("")
        body = doc["text"]
        if body.startswith("# "):
            body = body.split("\n", 1)[1] if "\n" in body else ""
        lines.append(body.rstrip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _xhtml(title: str, body: str) -> str:
    escaped = html.escape(body).replace("\n", "<br/>\n")
    return (
        "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
        "<html xmlns=\"http://www.w3.org/1999/xhtml\" xml:lang=\"zh-Hant\">"
        f"<head><title>{html.escape(title)}</title></head>"
        f"<body><h1>{html.escape(title)}</h1><p>{escaped}</p></body></html>"
    )


def _write_epub(path: Path, title: str, docs: list[dict[str, Any]]) -> None:
    container = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<container version=\"1.0\" xmlns=\"urn:oasis:names:tc:opendocument:xmlns:container\">"
        "<rootfiles><rootfile full-path=\"OEBPS/content.opf\" "
        "media-type=\"application/oebps-package+xml\"/></rootfiles></container>"
    )
    manifest_items = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>']
    spine = []
    nav_lis = []
    for doc in docs:
        item_id = f"doc{doc['index']:04d}"
        href = f"text/{item_id}.xhtml"
        manifest_items.append(f'<item id="{item_id}" href="{href}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{item_id}"/>')
        nav_lis.append(f'<li><a href="{href}">{html.escape(doc["title"])}</a></li>')
    opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">{html.escape(title)}</dc:identifier>
<dc:title>{html.escape(title)}</dc:title>
<dc:language>zh-Hant</dc:language>
</metadata>
<manifest>{''.join(manifest_items)}</manifest>
<spine>{''.join(spine)}</spine>
</package>
'''
    nav = (
        "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
        "<html xmlns=\"http://www.w3.org/1999/xhtml\" xmlns:epub=\"http://www.idpf.org/2007/ops\">"
        f"<head><title>{html.escape(title)}</title></head><body><nav epub:type=\"toc\"><ol>"
        f"{''.join(nav_lis)}</ol></nav></body></html>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container)
        zf.writestr("OEBPS/content.opf", opf)
        zf.writestr("OEBPS/nav.xhtml", nav)
        for doc in docs:
            item_id = f"doc{doc['index']:04d}"
            zf.writestr(f"OEBPS/text/{item_id}.xhtml", _xhtml(doc["title"], doc["text"]))


def export_manuscript(adapter: Any, *, output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(adapter.project_root)
    freeze = (root / "PROJECT-FROZEN.json").is_file()
    meta = {}
    pointer = root / "project.json"
    if pointer.is_file():
        try:
            meta = json.loads(pointer.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            meta = {}
    title = str(meta.get("title") or adapter.project_id)
    docs = _collect_documents(root)
    out = Path(output_dir) if output_dir else (root / "workbench" / "exports")
    out.mkdir(parents=True, exist_ok=True)
    md_path = out / f"{adapter.project_id}.md"
    epub_path = out / f"{adapter.project_id}.epub"
    md_path.write_text(_markdown_book(title, docs, frozen=freeze), encoding="utf-8")
    _write_epub(epub_path, title, docs)
    report = {
        "schema": EXPORT_SCHEMA,
        "generated_at": now_iso(),
        "project_id": adapter.project_id,
        "title": title,
        "frozen": freeze,
        "document_count": len(docs),
        "chars": sum(d["chars"] for d in docs),
        "markdown_path": str(md_path),
        "epub_path": str(epub_path),
        "canon_write": False,
        "note": "複本匯出；不修改 chapters／scenes／事件正典",
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    (out / "export-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
