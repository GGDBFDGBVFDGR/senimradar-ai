from pathlib import Path

RANDOM_SEED = 42
VALIDATION_FRACTION = 0.2
C_GRID = (0.25, 1.0, 4.0)
MIN_DF = 2
WORD_FEATURES = 15000
CHAR_FEATURES = 20000
CALIBRATION_BINS = 10
CALIBRATION_ECE_LIMIT = 0.05
MODEL_VERSION = "tfidf-logreg-0001"

BACKEND_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = BACKEND_ROOT / "data" / "raw"
ARTIFACT_DIR = BACKEND_ROOT / "app" / "ml" / "artifacts"
TRAIN_FILE = RAW_DIR / "train_0.jsonl"
EVAL_EN_FILE = RAW_DIR / "eval_en.jsonl"
EVAL_BILINGUAL_FILE = RAW_DIR / "eval_ru_en.jsonl"
