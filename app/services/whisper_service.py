from faster_whisper import WhisperModel
from pathlib import Path


class WhisperService:
    def __init__(self, model_size: str = "base"):
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, file_path: Path) -> str:
        segments, _ = self.model.transcribe(str(file_path))
        return " ".join(segment.text for segment in segments)