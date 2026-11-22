"""Train the URL classifier from public lists. Phishing pages are not opened."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from app.ml.registry import ARTIFACT_DIR
from app.url.domains import registrable_domain
from app.url.features import UrlVectorizer
from app.url.safety import admission

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "url"
PHISH_URL = "https://data.phishtank.com/data/online-valid.csv.gz"
MAJESTIC_URL = "https://downloads.majestic.com/majestic_million.csv"
USER_AGENT = "SenimRadarAI/0.1 (research; no crawl)"
BENIGN_DOMAINS = 12000
GENERIC_PATHS = {"/", "/index.php", "/index.html", "/index.htm"}
VARIANTS = (
    "https://{domain}/",
    "https://www.{domain}/",
    "https://{domain}/about",
    "https://{domain}/login",
    "https://{domain}/search?q=weather",
)


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=120) as response, destination.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 256)
            if not chunk:
                break
            handle.write(chunk)


def _majestic_slice(destination: Path, limit: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(MAJESTIC_URL, headers={"User-Agent": USER_AGENT})
    domains: list[str] = []
    with urlopen(request, timeout=120) as response, destination.open("w", encoding="utf-8") as handle:
        header = response.readline().decode("utf-8", "replace").strip().split(",")
        domain_index = header.index("Domain") if "Domain" in header else 2
        while len(domains) < limit:
            raw = response.readline()
            if not raw:
                break
            columns = raw.decode("utf-8", "replace").split(",")
            if len(columns) <= domain_index:
                continue
            domain = columns[domain_index].strip().lower().strip(".")
            if not domain or " " in domain or "/" in domain:
                continue
            domains.append(domain)
            handle.write(domain + "\n")


def _parse_time(value: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is not None:
        return parsed.replace(tzinfo=None)
    return parsed


def _template(url: str) -> str:
    path = urlsplit(url).path.lower() or "/"
    path = re.sub(r"[0-9a-f]{8,}", "h", path)
    path = re.sub(r"\d+", "0", path)
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path or "/"


def _identity(url: str) -> tuple[str, str]:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower().strip(".")
    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    key = f"{parts.scheme.lower()}://{host}{path}"
    if parts.query:
        key += f"?{parts.query}"
    return key[:512], registrable_domain(host)


def _load_phishing(path: Path) -> dict[str, dict]:
    grouped: dict[str, dict] = {}
    seen: set[str] = set()
    with gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("verified") != "yes" or row.get("online") != "yes":
                continue
            raw = (row.get("url") or "").strip()
            if admission(raw) is not None:
                continue
            try:
                when = _parse_time(row.get("verification_time") or "")
                key, domain = _identity(raw)
            except (TypeError, ValueError):
                continue
            if not domain or key in seen:
                continue
            seen.add(key)
            bucket = grouped.setdefault(domain, {"first": when, "rows": []})
            if when < bucket["first"]:
                bucket["first"] = when
            bucket["rows"].append((key, _template(key), when))
    return grouped


def _split_domains(grouped: dict[str, dict]) -> dict[str, str]:
    ordered = sorted(grouped, key=lambda domain: (grouped[domain]["first"], domain))
    count = len(ordered)
    train_end = int(count * 0.70)
    valid_end = int(count * 0.85)
    assigned = {}
    for index, domain in enumerate(ordered):
        if index < train_end:
            assigned[domain] = "train"
        elif index < valid_end:
            assigned[domain] = "validation"
        else:
            assigned[domain] = "test"
    return assigned


def _phishing_rows(grouped: dict[str, dict], assigned: dict[str, str]) -> dict[str, list[str]]:
    test_templates = {
        template
        for domain, split in assigned.items()
        if split == "test"
        for _url, template, _when in grouped[domain]["rows"]
        if template not in GENERIC_PATHS and len(template) >= 8
    }
    rows = {"train": [], "validation": [], "test": []}
    dropped = 0
    for domain, split in assigned.items():
        for url, template, _when in grouped[domain]["rows"]:
            if split != "test" and template in test_templates:
                dropped += 1
                continue
            rows[split].append(url)
    rows["dropped_template_overlap"] = dropped  # type: ignore[assignment]
    return rows


def _benign_rows(domains: list[str], blocked: set[str]) -> dict[str, list[str]]:
    rows = {"train": [], "validation": [], "test": []}
    kept = 0
    for domain in domains:
        if kept >= BENIGN_DOMAINS:
            break
        if not re.fullmatch(r"[a-z0-9.-]+", domain) or registrable_domain(domain) in blocked:
            continue
        kept += 1
        bucket = int(hashlib.sha256(f"senimradar-url|{domain}".encode()).hexdigest()[:8], 16) % 100
        split = "train" if bucket < 70 else "validation" if bucket < 85 else "test"
        for pattern in VARIANTS:
            if pattern.startswith("https://www.") and domain.startswith("www."):
                continue
            rows[split].append(pattern.format(domain=domain))
    return rows


def _metrics(truth: list[str], predicted: list[str]) -> dict:
    precision, recall, f1, _support = precision_recall_fscore_support(
        truth, predicted, labels=["phishing", "benign"], zero_division=0
    )
    matrix = confusion_matrix(truth, predicted, labels=["phishing", "benign"])
    return {
        "phishing_precision": round(float(precision[0]), 4),
        "phishing_recall": round(float(recall[0]), 4),
        "benign_precision": round(float(precision[1]), 4),
        "benign_recall": round(float(recall[1]), 4),
        "macro_f1": round(float(f1.mean()), 4),
        "false_negatives": int(matrix[0, 1]),
        "false_positives": int(matrix[1, 0]),
        "true_phishing": int(matrix[0, 0]),
        "true_benign": int(matrix[1, 1]),
    }


def _margin(pipeline: Pipeline, urls: list[str], labels: list[str]) -> float:
    distances = np.abs(pipeline.decision_function(urls))
    predicted = pipeline.predict(urls)
    best_margin = 0.0
    best_score = -1.0
    labels_array = np.array(labels)
    for candidate in np.linspace(0.0, 1.5, 16):
        keep = distances >= candidate
        if keep.mean() < 0.75:
            continue
        score = _metrics(labels_array[keep].tolist(), predicted[keep].tolist())["macro_f1"]
        if score > best_score:
            best_score = score
            best_margin = float(candidate)
    return best_margin


def _fit(name: str, urls: list[str], labels: list[str]) -> Pipeline:
    if name == "svm":
        classifier = LinearSVC(C=1.0, class_weight="balanced", dual=False, max_iter=2000, random_state=22)
    else:
        classifier = LogisticRegression(
            C=1.0, class_weight="balanced", solver="saga", max_iter=1000, random_state=22
        )
    pipeline = Pipeline([("features", UrlVectorizer()), ("clf", classifier)])
    pipeline.fit(urls, labels)
    return pipeline


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    phish_path = DATA_DIR / "phishtank-online-valid.csv.gz"
    majestic_path = DATA_DIR / "majestic-top.txt"
    if not phish_path.is_file():
        _download(PHISH_URL, phish_path)
    if not majestic_path.is_file():
        _majestic_slice(majestic_path, 20000)
    grouped = _load_phishing(phish_path)
    assigned = _split_domains(grouped)
    phishing = _phishing_rows(grouped, assigned)
    dropped = int(phishing.pop("dropped_template_overlap"))
    benign = _benign_rows(majestic_path.read_text(encoding="utf-8").splitlines(), set(grouped))
    splits = {}
    for name in ("train", "validation", "test"):
        splits[name] = {
            "urls": phishing[name] + benign[name],
            "labels": ["phishing"] * len(phishing[name]) + ["benign"] * len(benign[name]),
            "phishing": len(phishing[name]),
            "benign": len(benign[name]),
        }
        if len(set(phishing[name]) & set(benign[name])) != 0:
            raise SystemExit("label collision")
    domain_sets = {name: set() for name in ("train", "validation", "test")}
    for domain, split in assigned.items():
        domain_sets[split].add(domain)
    if domain_sets["train"] & domain_sets["validation"] or domain_sets["train"] & domain_sets["test"] or domain_sets["validation"] & domain_sets["test"]:
        raise SystemExit("domain overlap")
    for name in ("train", "validation", "test"):
        if splits[name]["phishing"] < 500 or splits[name]["benign"] < 500:
            raise SystemExit(f"split too small: {name}")
    candidates = {}
    pipelines = {}
    for name in ("svm", "logistic"):
        pipelines[name] = _fit(name, splits["train"]["urls"], splits["train"]["labels"])
        predicted = pipelines[name].predict(splits["validation"]["urls"]).tolist()
        score = _metrics(splits["validation"]["labels"], predicted)
        raw_iterations = getattr(pipelines[name].named_steps["clf"], "n_iter_", 0)
        score["iterations"] = int(np.max(raw_iterations))
        candidates[name] = score
    winner = max(candidates, key=lambda name: candidates[name]["macro_f1"])
    margin = _margin(pipelines[winner], splits["validation"]["urls"], splits["validation"]["labels"])
    test_predicted = pipelines[winner].predict(splits["test"]["urls"]).tolist()
    test_metrics = _metrics(splits["test"]["labels"], test_predicted)
    distances = np.abs(pipelines[winner].decision_function(splits["test"]["urls"]))
    keep = distances >= margin
    kept_labels = [label for label, flag in zip(splits["test"]["labels"], keep, strict=True) if flag]
    kept_predicted = [label for label, flag in zip(test_predicted, keep, strict=True) if flag]
    version = "url-tfidf-linearsvm-0001" if winner == "svm" else "url-tfidf-logreg-0001"
    card = {
        "model_version": version,
        "task": "url",
        "algorithm": "character tf-idf 3-5 plus structural features, " + winner,
        "confidence_calibrated": False,
        "risk_score_displayed": False,
        "uncertainty_margin": margin,
        "sources": {
            "phishing": "PhishTank verified online CSV. Community labels. Pages were not opened.",
            "benign": "Majestic Million top domains, CC BY 3.0. Paths were constructed locally and were not crawled.",
        },
        "counts": {
            "phishing_domains": len(grouped),
            "template_rows_removed_from_train_and_validation": dropped,
            "train": splits["train"]["phishing"] + splits["train"]["benign"],
            "train_phishing": splits["train"]["phishing"],
            "train_benign": splits["train"]["benign"],
            "validation": splits["validation"]["phishing"] + splits["validation"]["benign"],
            "validation_phishing": splits["validation"]["phishing"],
            "validation_benign": splits["validation"]["benign"],
            "test": splits["test"]["phishing"] + splits["test"]["benign"],
            "test_phishing": splits["test"]["phishing"],
            "test_benign": splits["test"]["benign"],
        },
        "validation": candidates,
        "selected_on": "validation macro-F1",
        "test_raw": test_metrics,
        "test_after_validation_margin": {
            **_metrics(kept_labels, kept_predicted),
            "kept": int(keep.sum()),
            "abstained": int((~keep).sum()),
        },
        "leakage": {
            "same_registrable_domain_across_phishing_splits": 0,
            "same_url_across_labels": 0,
        },
    }
    artifact = ARTIFACT_DIR / f"{version}.joblib"
    card_path = ARTIFACT_DIR / f"{version}.json"
    joblib.dump(
        {"model_version": version, "task": "url", "pipeline": pipelines[winner], "uncertainty_margin": margin},
        artifact,
    )
    card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ARTIFACT_DIR / "active_url_model.json").write_text(
        json.dumps({"model_version": version, "artifact": artifact.name, "card": card_path.name}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"version": version, "validation": candidates[winner], "test_raw": test_metrics, "counts": card["counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
