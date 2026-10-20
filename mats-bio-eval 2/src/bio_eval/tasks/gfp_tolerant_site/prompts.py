"""Model-facing prompts for the tolerant-site task.

``USER_TEMPLATE`` is filled with ``str.format``. Literal JSON braces are
doubled. The rendered string is stored on ``Sample.input`` and is not passed
through ``prompt_template()`` or ``user_message()``.
"""

from __future__ import annotations

SYSTEM_PROMPT = (
    "You are an expert protein engineer. Use your own knowledge. "
    "You may call residue_orientation. Do not search the web. "
    "Your final reply is one JSON object and nothing else."
)

USER_TEMPLATE = """\
GFP from Aequorea victoria, 238 amino acids.

Amino acids in this protein were changed one at a time, and each change was scored by whether the protein still fluoresced.

Residues {start}-{end}: {bracket_sequence}

Which three residues in a row, inside this range, each tolerated change? Tolerated means at least one change there still fluoresced, and no change there went dark.

You may call residue_orientation(position) up to 5 times. It says whether that side chain points toward the chromophore or away from it. It does not tell you whether a change fluoresced.

Answer only with:
{{"start": <first of the three>, "sequence": "<three letters>", "confidence": <0.5 to 1.0>}}
"""


def render_user_prompt(start: int, end: int, bracket_sequence: str) -> str:
    return USER_TEMPLATE.format(
        start=start, end=end, bracket_sequence=bracket_sequence
    )
