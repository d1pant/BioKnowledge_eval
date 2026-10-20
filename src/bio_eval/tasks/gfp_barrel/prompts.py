"""Model-facing prompts for the barrel-orientation task.

The user template is filled with ``str.format``. Literal JSON braces in
``USER_TEMPLATE`` are doubled. Render once and store the string on
``Sample.input``. Do not pass it through ``prompt_template()`` or
``user_message()``.
"""

from __future__ import annotations

SYSTEM_PROMPT = (
    "You are an expert structural biologist. Answer questions about protein "
    "three-dimensional structure using your own knowledge only. Respond with "
    "a single JSON object and nothing else."
)

USER_TEMPLATE = """\
Protein: green fluorescent protein (GFP) from Aequorea victoria. Residue numbering is the standard 238-amino-acid sequence.

GFP folds as an 11-stranded beta-barrel. Its chromophore sits inside the barrel, near the barrel's centre.

Residue: {aa_three} {author_resnum} ({aa_one})
Beta-strand: {strand_id} (of b1-b11), residues {strand_start}-{strand_end}
Strand sequence, target residue in brackets: {strand_context}

Question: Does the side chain of {aa_three} {author_resnum} point TOWARD the chromophore (into the barrel interior) or AWAY from the chromophore (out toward the barrel surface)?
Definition: take the direction from the residue's C-alpha atom to its side chain (for glycine, the direction of a hypothetical C-beta). TOWARD means this direction points toward the chromophore; AWAY means it points away from it.

Respond with exactly one JSON object:
{{"label": "TOWARD" or "AWAY", "confidence": <number from 0.5 to 1.0, your probability that your label is correct>}}
"""

ONE_TO_THREE = {
    "A": "ALA", "R": "ARG", "N": "ASN", "D": "ASP", "C": "CYS", "Q": "GLN",
    "E": "GLU", "G": "GLY", "H": "HIS", "I": "ILE", "L": "LEU", "K": "LYS",
    "M": "MET", "F": "PHE", "P": "PRO", "S": "SER", "T": "THR", "W": "TRP",
    "Y": "TYR", "V": "VAL",
}


def strand_context(sequence: str, start: int, target: int) -> str:
    """Strand sequence with the target residue wrapped in brackets."""
    index = target - start
    if not 0 <= index < len(sequence):
        raise ValueError(f"residue {target} is outside {start}-{start + len(sequence) - 1}")
    return f"{sequence[:index]}[{sequence[index]}]{sequence[index + 1:]}"


def render_user_prompt(row: dict) -> str:
    """Fill ``USER_TEMPLATE``. ``row`` uses the dataset record fields."""
    return USER_TEMPLATE.format(
        aa_three=row["aa_three"],
        author_resnum=row["author_resnum"],
        aa_one=row["aa"],
        strand_id=row["strand_id"],
        strand_start=row["strand_start"],
        strand_end=row["strand_end"],
        strand_context=row["strand_context"],
    )
