"""Load the researcher corpus and keep whole families inside one split."""

from __future__ import annotations

import hashlib
from collections import Counter

from app.ml.labels import LABELS
from app.ml.preprocess import template_key
from training.dataset import Example
from training.research_corpus import ROWS

SPLIT_SALT = "senimradar-stage-2.1|"


def assigned_split(family_id: str) -> str:
    digest = hashlib.sha256(f"{SPLIT_SALT}{family_id}".encode()).hexdigest()
    bucket = int(digest[:8], 16) % 100
    if bucket < 20:
        return "test"
    if bucket < 40:
        return "validation"
    return "train"


def load_research_examples() -> dict[str, list[Example]]:
    grouped: dict[str, list[Example]] = {"train": [], "validation": [], "test": []}
    seen_text: set[str] = set()
    for index, (family, language, label, role, text) in enumerate(ROWS):
        if language not in {"ru", "kk", "mixed"} or label not in LABELS or not text.strip():
            raise ValueError(f"invalid research row {index}")
        if text in seen_text:
            raise ValueError(f"duplicate research text at {index}")
        seen_text.add(text)
        part = assigned_split(family)
        grouped[part].append(
            Example(
                example_id=f"research-{family}-{index}",
                group_id=f"research:{family}",
                language=language,
                label=label,
                text=text,
                template=template_key(text),
                split_source=f"research_{part}:{role}",
            )
        )
    return grouped


def overlap_report(left: list[Example], right: list[Example]) -> dict[str, int]:
    left_ids = {item.group_id for item in left}
    right_ids = {item.group_id for item in right}
    left_templates = {item.template for item in left}
    right_templates = {item.template for item in right}
    return {
        "shared_groups": len(left_ids & right_ids),
        "shared_templates": len(left_templates & right_templates),
    }


def tally_roles(examples: list[Example]) -> dict[str, int]:
    return dict(Counter(item.split_source for item in examples))
