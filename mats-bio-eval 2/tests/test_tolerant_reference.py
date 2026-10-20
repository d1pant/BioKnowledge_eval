"""The Sarkisyan reference must match the triplet letters in the counts note."""

import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "src" / "bio_eval" / "tasks" / "gfp_tolerant_site" / "data"
P42212 = (
    Path(__file__).resolve().parents[1]
    / "analysis"
    / "ground_truth"
    / "structures"
    / "P42212.fasta"
)

# Three-letter codes copied from gfp-triplet-window-counts.md.
TRIPLETS = {
    "1-50": {
        3: "KGE", 4: "GEE", 5: "EEL", 6: "ELF", 7: "LFT", 8: "FTG", 9: "TGV",
        10: "GVV", 11: "VVP", 12: "VPI", 23: "NGH", 24: "GHK", 36: "DAT",
        37: "ATY", 45: "KFI",
    },
    "51-100": {
        73: "RYP", 74: "YPD", 75: "PDH", 76: "DHM", 77: "HMK", 78: "MKQ", 79: "KQH",
    },
    "101-150": {
        101: "KDD", 102: "DDG", 103: "DGN", 113: "KFE", 114: "FEG", 115: "EGD",
        116: "GDT", 131: "KED", 132: "EDG", 133: "DGN", 134: "GNI", 138: "GHK",
        139: "HKL", 140: "KLE", 141: "LEY", 142: "EYN", 143: "YNY", 144: "NYN",
        145: "YNS", 146: "NSH", 147: "SHN", 148: "HNV",
    },
    "151-200": {
        151: "YIM", 152: "IMA", 153: "MAD", 154: "ADK", 155: "DKQ", 156: "KQK",
        157: "QKN", 158: "KNG", 159: "NGI", 160: "GIK", 161: "IKV", 162: "KVN",
        163: "VNF", 164: "NFK", 165: "FKI", 166: "KIR", 170: "NIE", 171: "IED",
        172: "EDG", 173: "DGS", 174: "GSV", 175: "SVQ", 176: "VQL", 185: "NTP",
        186: "TPI", 187: "PIG", 188: "IGD", 189: "GDG", 190: "DGP", 191: "GPV",
        192: "PVL", 193: "VLL", 194: "LLP", 195: "LPD", 196: "PDN",
    },
    "200-238": {
        202: "STQ", 208: "SKD", 209: "KDP", 210: "DPN", 214: "KRD", 221: "LEF",
        222: "EFV", 223: "FVT", 224: "VTA", 225: "TAA", 226: "AAG", 227: "AGI",
        228: "GIT", 229: "ITH", 230: "THG", 231: "HGM", 232: "GMD", 233: "MDE",
        234: "DEL", 235: "ELY",
    },
}
EXPECTED_N = {"1-50": 48, "51-100": 48, "101-150": 48, "151-200": 48, "200-238": 37}


def _fasta(path: Path) -> str:
    lines = path.read_text().splitlines()
    return "".join(line.strip() for line in lines if not line.startswith(">"))


def test_sarkisyan_reference_is_p42212_with_f64l():
    ref = _fasta(P42212)
    sark = _fasta(DATA / "avgfp_sarkisyan.fasta")
    assert len(ref) == len(sark) == 238
    assert ref[63] == "F" and sark[63] == "L"
    assert sark[:63] + "F" + sark[64:] == ref


def test_accepted_starts_match_triplet_letters():
    payload = json.loads((DATA / "accepted_starts.json").read_text())
    sark = _fasta(DATA / "avgfp_sarkisyan.fasta")
    assert list(payload) == list(TRIPLETS)
    for bracket, letters in TRIPLETS.items():
        info = payload[bracket]
        starts = info["starts"]
        assert starts == sorted(letters)
        width = info["end"] - info["start"] + 1
        possible = width - 2
        assert possible == EXPECTED_N[bracket]
        assert len(starts) / possible == len(letters) / EXPECTED_N[bracket]
        for start, seq in letters.items():
            assert info["start"] <= start <= info["end"] - 2
            assert sark[start - 1 : start + 2] == seq
