import logging
from typing import List, Optional, Dict, Tuple

from anthropic import Anthropic

from .settings import settings
from .personalities import default_persona_system

logger = logging.getLogger("bloomed-terminal.inference")
logging.basicConfig(level=logging.INFO)

_CLIENT = None

def load_model(model_dir: Optional[str] = None) -> None:
    """
    Lazy-load Anthropic client into module globals.
    """
    del model_dir
    global _CLIENT
    if _CLIENT is not None:
        return
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to your environment.")
    logger.info("Initializing Anthropic client.")
    _CLIENT = Anthropic(api_key=settings.anthropic_api_key)
    logger.info("Anthropic client ready.")

def _ensure_persona_system(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    If no system prompt is present, inject Bloomed Terminal’s house-voice system.
    """
    if messages and messages[0].get("role") == "system":
        return messages
    sys = default_persona_system()
    return [{"role": "system", "content": sys}, *messages]

def _split_system(messages: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
    system_parts: List[str] = []
    filtered: List[Dict[str, str]] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            if content:
                system_parts.append(content)
        elif role in ("user", "assistant"):
            filtered.append({"role": role, "content": content})
    return "\n\n".join(system_parts).strip(), filtered

def generate(
    messages: List[Dict[str, str]],
    max_new_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    stop: Optional[List[str]] = None,
) -> str:
    """
    Core text generation: returns assistant content as a string.
    """
    global _CLIENT
    if _CLIENT is None:
        load_model()

    messages = _ensure_persona_system(messages)

    max_new_tokens = int(max_new_tokens or settings.max_new_tokens)
    temperature = float(temperature if temperature is not None else settings.temperature)
    top_p = float(top_p if top_p is not None else settings.top_p)

    system_text, anthropic_messages = _split_system(messages)
    if not anthropic_messages:
        anthropic_messages = [{"role": "user", "content": ""}]

    req = {
        "model": settings.anthropic_model,
        "max_tokens": max_new_tokens,
        "messages": anthropic_messages,
        "temperature": temperature,
        "top_p": top_p,
    }
    if system_text:
        req["system"] = system_text
    if stop:
        req["stop_sequences"] = stop

    response = _CLIENT.messages.create(**req)
    parts = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts).strip()
