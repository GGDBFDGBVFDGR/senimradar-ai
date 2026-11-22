import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from app.ml.labels import LABELS
from app.ml.preprocess import template_key

_MESSAGE_RE = re.compile(
    r"scam risk:\s*(.*?)\s*Return only the JSON object\.?\s*$",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class Example:
    example_id: str
    group_id: str
    language: str
    label: str
    text: str
    template: str
    split_source: str


def extract_message(user_turn: str) -> str:
    match = _MESSAGE_RE.search(user_turn.strip())
    if match is None:
        raise ValueError("message_not_found")
    text = match.group(1).strip()
    if text.startswith('"""') and text.endswith('"""'):
        text = text[3:-3].strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        text = text[1:-1].strip()
    text = text.strip().strip("`").strip()
    if not text:
        raise ValueError("empty_message")
    return text


def base_group(example_id: str) -> str:
    if example_id.endswith("_ru"):
        return example_id[: -len("_ru")]
    return example_id


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_training_rows(path: Path) -> tuple[list[Example], dict[str, int]]:
    examples: list[Example] = []
    rejected: Counter[str] = Counter()
    for row in _read_jsonl(path):
        try:
            label = json.loads(row["assistant"])["risk_level"]
            text = extract_message(row["user"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            rejected["unreadable"] += 1
            continue
        language = row.get("language")
        if label not in LABELS or language not in {"ru", "en"} or not row.get("id"):
            rejected["invalid_label_or_language"] += 1
            continue
        examples.append(
            Example(
                example_id=row["id"],
                group_id=base_group(row["id"]),
                language=language,
                label=label,
                text=text,
                template=template_key(text),
                split_source="train_file",
            )
        )
    return examples, dict(rejected)


def load_evaluation_rows(english_path: Path, bilingual_path: Path) -> tuple[list[Example], dict[str, int]]:
    """Use every English eval row once, plus the Russian half of the bilingual file."""

    examples: list[Example] = []
    rejected: Counter[str] = Counter()
    seen: set[str] = set()
    for row in _read_jsonl(english_path):
        example = _eval_example(row, default_language="en")
        if example is None:
            rejected["invalid_eval"] += 1
            continue
        examples.append(example)
        seen.add(example.example_id)
    for row in _read_jsonl(bilingual_path):
        if row.get("language") != "ru":
            continue
        example = _eval_example(row, default_language="ru")
        if example is None or example.example_id in seen:
            rejected["invalid_or_duplicate_eval"] += 1
            continue
        examples.append(example)
        seen.add(example.example_id)
    return examples, dict(rejected)


def _eval_example(row: dict, default_language: str) -> Example | None:
    label = row.get("expected_risk_level")
    text = (row.get("input") or "").strip()
    example_id = row.get("id")
    language = row.get("language") or default_language
    if label not in LABELS or language not in {"ru", "en"} or not example_id or not text:
        return None
    return Example(
        example_id=example_id,
        group_id=base_group(example_id),
        language=language,
        label=label,
        text=text,
        template=template_key(text),
        split_source="official_eval",
    )


def tally(examples: list[Example]) -> dict[str, dict[str, int]]:
    by_label: Counter[str] = Counter(item.label for item in examples)
    by_language: Counter[str] = Counter(item.language for item in examples)
    by_pair: Counter[str] = Counter(f"{item.language}:{item.label}" for item in examples)
    return {
        "labels": dict(by_label),
        "languages": dict(by_language),
        "language_label": dict(by_pair),
        "rows": {"total": len(examples)},
    }
