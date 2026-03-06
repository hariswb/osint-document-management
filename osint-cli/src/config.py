from pathlib import Path


class Config:
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    DB_PATH = DATA_DIR / "osint.db"
    CACHE_DIR = DATA_DIR / "cache"

    # Model settings
    DEFAULT_MODEL = "dslim/bert-base-NER"
    DEVICE = "cpu"  # Default to CPU, can be overridden

    # Processing settings
    BATCH_SIZE = 32
    MAX_SEQUENCE_LENGTH = 512


config = Config()
