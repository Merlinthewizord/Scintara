from typing import Dict, Any
from .settings import settings

def get_model_info() -> Dict[str, Any]:
    return {
        "provider": "anthropic",
        "model": settings.anthropic_model,
        "max_new_tokens": settings.max_new_tokens,
        "temperature": settings.temperature,
        "top_p": settings.top_p,
    }
