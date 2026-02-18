"""Generate synthetic demo audio for the synth mode."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    """Generate a synthetic WAV file using the Silero TTS adapter."""
    root = Path(__file__).resolve().parents[1]
    src_path = root / "src"
    sys.path.insert(0, str(src_path))

    from ai_secretary.tts.silero import SileroTTS

    text = (
        "Здравствуйте, меня зовут Светлана Иванова. Я из Казани.\n"
        "Хочу уточнить условия поставки оборудования.\n"
        "Мой телефон 9 903 678 46 53. ИНН 7701234567."
    )

    out_path = root / "data" / "demo" / "client_synth.wav"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    tts = SileroTTS()
    audio = tts.synthesize(text)
    out_path.write_bytes(audio)

    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
