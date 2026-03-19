from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from juthoor_arabicgenome_lv1.core.loaders import load_binary_roots, load_letters


LV1_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = LV1_ROOT.parent
CANON_ROOT = LV1_ROOT / "data" / "theory_canon"
REGISTRIES_DIR = CANON_ROOT / "registries"
PROMOTED_DIR = REPO_ROOT / "outputs" / "research_factory" / "promoted" / "promoted_features"
AXIS2_DIR = REPO_ROOT / "outputs" / "research_factory" / "axis2"
THEORY_DOC_DIR = LV1_ROOT / "docs" / "The Arabic Tongue (nature-genome-application)"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _load_articulatory_features() -> dict[str, dict[str, Any]]:
    makhaarij_path = LV1_ROOT / "resources" / "phonetics" / "makhaarij.json"
    sifaat_path = LV1_ROOT / "resources" / "phonetics" / "sifaat.json"
    makhaarij = json.loads(makhaarij_path.read_text(encoding="utf-8")) if makhaarij_path.exists() else {}
    sifaat = json.loads(sifaat_path.read_text(encoding="utf-8")) if sifaat_path.exists() else {}
    out: dict[str, dict[str, Any]] = {}
    for letter in set(makhaarij) | set(sifaat):
        out[letter] = {
            "makhraj": makhaarij.get(letter),
            "sifaat": sifaat.get(letter, []),
        }
    return out


def _load_coherence_map() -> dict[str, float]:
    preferred = PROMOTED_DIR / "field_coherence_scores.jsonl"
    fallback = AXIS2_DIR / "field_coherence.jsonl"
    rows = _read_jsonl(preferred if preferred.exists() else fallback)
    return {
        str(row["binary_root"]): float(row["coherence"])
        for row in rows
        if row.get("binary_root") and row.get("coherence") is not None
    }


def _build_letter_rows() -> list[dict[str, Any]]:
    articulatory = _load_articulatory_features()
    rows: list[dict[str, Any]] = []
    for letter in load_letters():
        rows.append(
            {
                "letter": letter.letter,
                "letter_name": letter.letter_name,
                "canonical_semantic_gloss": letter.meaning,
                "canonical_kinetic_gloss": None,
                "canonical_sensory_gloss": None,
                "articulatory_features": articulatory.get(letter.letter),
                "sources": [
                    {
                        "source_id": f"muajam-letter-{letter.letter}",
                        "scholar": "jabal",
                        "claim_type": "semantic",
                        "claim_text": letter.meaning,
                        "document_ref": "data/muajam/letter_meanings.jsonl",
                        "curation_status": "reviewed",
                    }
                ],
                "agreement_level": "unknown",
                "confidence_tier": "stub",
                "status": "draft",
            }
        )
    return rows


def _build_binary_rows() -> list[dict[str, Any]]:
    coherence_map = _load_coherence_map()
    roots_path = LV1_ROOT / "data" / "muajam" / "roots.jsonl"
    roots_rows = _read_jsonl(roots_path)
    members: dict[str, list[str]] = {}
    for row in roots_rows:
        br = str(row.get("binary_root") or "").strip()
        tri = str(row.get("tri_root") or "").strip()
        if br and tri:
            members.setdefault(br, [])
            if tri not in members[br]:
                members[br].append(tri)

    rows: list[dict[str, Any]] = []
    for binary in load_binary_roots():
        roots = tuple(members.get(binary.binary_root, []))
        rows.append(
            {
                "binary_root": binary.binary_root,
                "field_gloss": binary.meaning or None,
                "field_gloss_source": "jabal" if binary.meaning else None,
                "letter1": binary.letter1,
                "letter2": binary.letter2,
                "letter1_gloss": binary.letter1_meaning or None,
                "letter2_gloss": binary.letter2_meaning or None,
                "member_roots": list(roots),
                "member_count": len(roots),
                "coherence_score": coherence_map.get(binary.binary_root),
                "cross_lingual_support": None,
                "status": "draft",
            }
        )
    return rows


def _build_root_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    genome_dir = LV1_ROOT / "outputs" / "genome_v2"
    if genome_dir.exists():
        for path in sorted(genome_dir.glob("*.jsonl")):
            for record in _read_jsonl(path):
                root = str(record.get("root") or "").strip()
                binary_root = str(record.get("binary_root") or "").strip()
                if not root or not binary_root:
                    continue
                added_letter = str(record.get("added_letter") or "")
                if not added_letter or added_letter == "—":
                    added_letter = root[2] if len(root) >= 3 else ""
                rows.append(
                    {
                        "root": root,
                        "binary_root": binary_root,
                        "third_letter": added_letter[-1:] if added_letter else "",
                        "conceptual_root_meaning": None,
                        "binary_field_meaning": record.get("binary_root_meaning"),
                        "axial_meaning": record.get("axial_meaning"),
                        "letter_trace": None,
                        "position_profile": None,
                        "modifier_profile": None,
                        "compositional_signal": None,
                        "agreement_with_observed_gloss": None,
                        "semantic_score": record.get("semantic_score"),
                        "status": "draft",
                    }
                )
    return rows


def _build_theory_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "claim-jabal-binary-field",
            "theme": "binary_derivation",
            "scholar": "jabal",
            "statement": "أول حرفين صحيحين يحددان الحقل الدلالي",
            "scope": "arabic_general",
            "evidence_type": "lexical",
            "source_doc": str(THEORY_DOC_DIR / "ملخص_الدلالة_الصوتية_العربية.md"),
            "source_locator": "§7 ب",
            "status": "draft",
        },
        {
            "claim_id": "claim-jabal-letter-meaning",
            "theme": "letter_semantics",
            "scholar": "jabal",
            "statement": "لكل حرف من الحروف العربية قيمة دلالية محددة",
            "scope": "arabic_general",
            "evidence_type": "lexical",
            "source_doc": str(THEORY_DOC_DIR / "ملخص_الدلالة_الصوتية_العربية.md"),
            "source_locator": "§7 ج",
            "status": "draft",
        },
        {
            "claim_id": "claim-neili-intentionality",
            "theme": "intentionality",
            "scholar": "neili",
            "statement": "العلاقة بين الدال والمدلول قصدية لا اعتباطية",
            "scope": "quranic_only",
            "evidence_type": "doctrinal",
            "source_doc": str(THEORY_DOC_DIR / "نحو_نظرية_لسانية_للتفسير_القرآني.md"),
            "source_locator": "§عالم سبيط النيلي / أولاً",
            "status": "draft",
        },
        {
            "claim_id": "claim-neili-no-synonymy",
            "theme": "no_synonymy",
            "scholar": "neili",
            "statement": "لا ترادف في القرآن وكل مفردة فريدة الدلالة",
            "scope": "quranic_only",
            "evidence_type": "interpretive",
            "source_doc": str(THEORY_DOC_DIR / "نحو_نظرية_لسانية_للتفسير_القرآني.md"),
            "source_locator": "§المبدأ الخامس",
            "status": "draft",
        },
        {
            "claim_id": "claim-samarrai-context",
            "theme": "quranic_method",
            "scholar": "samarrai",
            "statement": "السياق القرآني الكامل يقيد المعنى ولا تُفهم المفردة بمعزل عنه",
            "scope": "quranic_only",
            "evidence_type": "interpretive",
            "source_doc": str(THEORY_DOC_DIR / "نحو_نظرية_لسانية_للتفسير_القرآني.md"),
            "source_locator": "§المبدأ الخامس",
            "status": "draft",
        },
    ]


def seed_registries(registry_root: Path | None = None) -> dict[str, Any]:
    root = registry_root or REGISTRIES_DIR
    root.mkdir(parents=True, exist_ok=True)

    letters = _build_letter_rows()
    binary_fields = _build_binary_rows()
    root_composition = _build_root_rows()
    theory_claims = _build_theory_claim_rows()
    quranic_profiles: list[dict[str, Any]] = []

    _write_jsonl(root / "letters.jsonl", letters)
    _write_jsonl(root / "binary_fields.jsonl", binary_fields)
    _write_jsonl(root / "root_composition.jsonl", root_composition)
    _write_jsonl(root / "theory_claims.jsonl", theory_claims)
    _write_jsonl(root / "quranic_profiles.jsonl", quranic_profiles)

    return {
        "letters": len(letters),
        "binary_fields": len(binary_fields),
        "root_composition": len(root_composition),
        "theory_claims": len(theory_claims),
        "quranic_profiles": len(quranic_profiles),
        "registry_root": str(root),
    }


def main() -> int:
    summary = seed_registries()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
