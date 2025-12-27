from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
import os

load_dotenv()

def _default_archive_path() -> str:
    if os.getenv("VERCEL"):
        return "/tmp/conversations.jsonl"
    return r"data\conversations.jsonl"

class Settings(BaseModel):
    model_config = {"protected_namespaces": ()}
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5-20251101")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    model_1: str = os.getenv("MODEL_1", "claude-opus-4-5-20251101")
    model_2: str = os.getenv("MODEL_2", "claude-opus-4-5-20251101")
    cron_secret: Optional[str] = os.getenv("CRON_SECRET")
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_service_role_key: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase_table: str = os.getenv("SUPABASE_TABLE", "conversations")
    archive_path: str = os.getenv("ARCHIVE_PATH", _default_archive_path())
    dialogue_exchanges: int = int(os.getenv("DIALOGUE_EXCHANGES", "6"))
    dialogue_interval_minutes: int = int(os.getenv("DIALOGUE_INTERVAL_MINUTES", "60"))
    auto_archive: bool = os.getenv("AUTO_ARCHIVE", "true").lower() in ("1", "true", "yes")
    max_new_tokens: int = int(os.getenv("MAX_NEW_TOKENS", "256"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.7"))
    top_p: float = float(os.getenv("TOP_P", "0.95"))
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

settings = Settings()
