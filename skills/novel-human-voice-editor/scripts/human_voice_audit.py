#!/usr/bin/env python3
"""Low-risk heuristic audit for fiction prose; reports clusters, never AI probability."""
from __future__ import annotations
import argparse, json, re
from collections import Counter
from pathlib import Path

ZH = "視頻 質量 智能 賦能 落地 復盤 對標 打造 賦予 重磅 破圈 拉滿".split()
PACKAGING = "因此 然而 此外 同時 值得一提 總而言之 眾所周知 深入探討 扮演著至關重要的角色 彰顯 象徵著 見證了 標誌著".split()
EMOTION = "感到恐懼 感到害怕 感到悲傷 感到憤怒 感到緊張 心中充滿 他明白了 她明白了 他意識到 她意識到".split()

def mask(text: str) -> str:
    # Do not audit fenced code or block quotes as ordinary prose.
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"(?m)^\s*>.*$", "", text)
    return text

def sentence_lengths(text: str):
    return [len(s.strip()) for s in re.split(r"[。！？!?]+", text) if s.strip()]

def occurrences(text: str, terms):
    return {t: text.count(t) for t in terms if text.count(t)}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--format", choices=("json", "text"), default="text")
    a = p.parse_args()
    raw = Path(a.file).read_text(encoding="utf-8", errors="replace")
    text = mask(raw)
    lengths = sentence_lengths(text)
    runs = []
    for i in range(len(lengths) - 2):
        if max(lengths[i:i+3]) - min(lengths[i:i+3]) <= 3:
            runs.append(lengths[i:i+3])
    chars = re.findall(r"[\u3400-\u9fff]", text)
    grams = Counter("".join(chars[i:i+4]) for i in range(max(0, len(chars)-3)))
    report = {
        "file": a.file,
        "chars": len(raw),
        "sentences": len(lengths),
        "sentence_length": {
            "mean": round(sum(lengths) / max(1, len(lengths)), 1),
            "min": min(lengths) if lengths else 0,
            "max": max(lengths) if lengths else 0,
            "near_equal_runs": len(runs),
        },
        "signals": {
            "taiwan_localization_candidates": occurrences(text, ZH),
            "packaging_or_connector_candidates": occurrences(text, PACKAGING),
            "emotion_explanation_candidates": occurrences(text, EMOTION),
            "negative_parallelism": len(re.findall(r"不是[^。！？!?]{0,40}而是", text)),
            "halfwidth_chinese_punctuation": len(re.findall(r"[\u3400-\u9fff][,.!?;:]", text)),
            "em_dash": text.count("—"),
            "ellipsis": text.count("……") + text.count("..."),
            "repeated_4grams": [{"gram": g, "count": n} for g, n in grams.most_common(12) if n > 1],
        },
        "limits": [
            "Signals require contextual review; no AI probability is inferred.",
            "Short passages and quoted, code, or deliberately stylized text may produce false positives.",
            "Do not rewrite from this report alone; protect canon, POV, character voice, and genre.",
        ],
    }
    if a.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
