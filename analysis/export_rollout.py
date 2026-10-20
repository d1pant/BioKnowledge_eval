"""Render one Inspect sample as a readable Markdown rollout. Reads logs only."""

from __future__ import annotations

import argparse
from pathlib import Path

from inspect_ai.log import read_eval_log

REPO_ROOT = Path(__file__).resolve().parents[1]


def _text(content) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for item in content or []:
        parts.append(getattr(item, "text", None) or getattr(item, "reasoning", "") or "")
    return "\n".join(p for p in parts if p)


def render(log_path: str, sample_id: str) -> str:
    log = read_eval_log(log_path)
    sample = next((s for s in (log.samples or []) if str(s.id) == str(sample_id)), None)
    if sample is None:
        ids = ", ".join(str(s.id) for s in (log.samples or []))
        raise SystemExit(f"sample {sample_id!r} not in log. available: {ids}")

    score = next(iter((sample.scores or {}).values()), None)
    meta = sample.metadata or {}
    config = log.eval.model_generate_config
    lines = [
        f"# Rollout: {log.eval.task} / {sample.id}",
        "",
        "Real agent trajectory, exported verbatim from the Inspect log with",
        "`python -m analysis.export_rollout`. Nothing here is constructed or mocked.",
        "",
        f"- Model: `{log.eval.model}`",
        f"- Log: `{Path(log_path).name}`",
        f"- Run id: `{log.eval.run_id}`",
        f"- max_tokens: {getattr(config, 'max_tokens', None)}",
        f"- Score: `{score.value if score else 'none'}`",
    ]
    if score is not None and score.metadata:
        lines.append(f"- Score metadata: `{score.metadata}`")
    if meta:
        shown = {k: v for k, v in meta.items() if k != "accepted_starts"}
        lines.append(f"- Sample metadata: `{shown}`")
        if "accepted_starts" in meta:
            lines.append(f"- Accepted starts (answer key, not shown to the model): `{meta['accepted_starts']}`")
    lines += ["", "## Transcript", ""]

    for message in sample.messages or []:
        role = message.role
        body = _text(message.content).strip()
        if role == "system":
            lines += ["### system", "", "```", body, "```", ""]
        elif role == "user":
            lines += ["### user", "", "```", body, "```", ""]
        elif role == "assistant":
            lines += ["### assistant", ""]
            if body:
                lines += ["```", body, "```", ""]
            for call in getattr(message, "tool_calls", None) or []:
                lines += [f"**tool call** `{call.function}({call.arguments})`", ""]
        elif role == "tool":
            lines += [f"**tool result** `{body}`", ""]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log")
    parser.add_argument("sample_id")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(args.log, args.sample_id))
    print(out)


if __name__ == "__main__":
    main()
