from pathlib import Path
import os

DATA = Path(os.getenv("TTS_DATA", "/data"))
DB = DATA / "studio.sqlite3"
TOKEN = os.getenv("STUDIO_PASSWORD", "change-me")
MAX_UPLOAD = int(os.getenv("MAX_UPLOAD_MB", "100")) * 1024 * 1024
MODEL_REVISION = os.getenv("MODEL_REVISION", "chatterbox-tts-0.1.6")

