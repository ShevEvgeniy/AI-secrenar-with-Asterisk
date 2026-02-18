"""Application settings loaded from environment variables."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    """Settings container for the AI secretary application."""

    openai_api_key: str
    elevenlabs_api_key: str
    ari_url: str
    ari_user: str
    ari_password: str
    sqlite_path: Path
    storage_dir: Path
    demo_mode: str
    demo_audio_path: Path
    expected_real_phone: str
    kb_path: Path
    rag_top_k: int
    asterisk_sounds_dir: Path
    asterisk_sounds_subdir: str
    asterisk_ssh_host: str
    asterisk_ssh_user: str
    asterisk_ssh_key: str
    asterisk_ssh_password: str
    asterisk_docker_container: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        demo_mode_raw = os.getenv("DEMO_MODE", "real").strip().lower()
        demo_mode = demo_mode_raw if demo_mode_raw in {"real", "synth"} else "real"
        expected_raw = os.getenv("EXPECTED_REAL_PHONE", "79036784653")
        expected_digits = "".join(ch for ch in expected_raw if ch.isdigit())
        demo_audio_path = (
            Path("./data/demo/client_real.wav")
            if demo_mode == "real"
            else Path("./data/demo/client_synth.wav")
        )
        kb_path = Path(os.getenv("KB_PATH", "./data/kb/mikizol_by_category.md"))
        rag_top_k = int(os.getenv("RAG_TOP_K", "3"))
        asterisk_sounds_dir = Path(os.getenv("ASTERISK_SOUNDS_DIR", "/var/lib/asterisk/sounds"))
        asterisk_sounds_subdir = os.getenv("ASTERISK_SOUNDS_SUBDIR", "ai_secretary")
        asterisk_ssh_host = os.getenv("ASTERISK_SSH_HOST", "")
        asterisk_ssh_user = os.getenv("ASTERISK_SSH_USER", "")
        asterisk_ssh_key = os.getenv("ASTERISK_SSH_KEY", "")
        asterisk_ssh_password = os.getenv("ASTERISK_SSH_PASSWORD", "")
        asterisk_docker_container = os.getenv("ASTERISK_DOCKER_CONTAINER", "")
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY", ""),
            ari_url=os.getenv("ARI_URL", "http://localhost:8088/ari"),
            ari_user=os.getenv("ARI_USER", ""),
            ari_password=os.getenv("ARI_PASSWORD", ""),
            sqlite_path=Path(os.getenv("SQLITE_PATH", "./data/sqlite/ai_secretary.db")),
            storage_dir=Path(os.getenv("STORAGE_DIR", "./data/storage")),
            demo_mode=demo_mode,
            demo_audio_path=demo_audio_path,
            expected_real_phone=expected_digits,
            kb_path=kb_path,
            rag_top_k=rag_top_k,
            asterisk_sounds_dir=asterisk_sounds_dir,
            asterisk_sounds_subdir=asterisk_sounds_subdir,
            asterisk_ssh_host=asterisk_ssh_host,
            asterisk_ssh_user=asterisk_ssh_user,
            asterisk_ssh_key=asterisk_ssh_key,
            asterisk_ssh_password=asterisk_ssh_password,
            asterisk_docker_container=asterisk_docker_container,
        )