import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from anthropic import Anthropic
from mem0 import Memory

from .settings import settings
from .archive import append_dialogue

logger = logging.getLogger("bloomed-terminal.dialogue")

SYSTEM_PROMPT = (
    "You are one of two AIs in a focused dialogue. You are trying to get to the "
    "bottom of what enlightenment is and how to achieve it. Be curious, rigorous, "
    "and concise. Ask clarifying questions and build on the other AI's points. "
    "Avoid roleplay, stay practical and philosophical. You may include ASCII art "
    "sparingly when it adds clarity or emphasis."
)

_ANTHROPIC_CLIENT: Optional[Anthropic] = None
_MEM0_CLIENT: Optional[Memory] = None


def clamp_exchanges(value: Any) -> int:
    if not isinstance(value, (int, float)) or not value == value:
        return 6
    return max(1, min(int(value), 40))


def _ensure_clients() -> Anthropic:
    global _ANTHROPIC_CLIENT
    if _ANTHROPIC_CLIENT is None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        _ANTHROPIC_CLIENT = Anthropic(api_key=settings.anthropic_api_key)
    return _ANTHROPIC_CLIENT


def _mem0_client() -> Optional[Memory]:
    global _MEM0_CLIENT
    if _MEM0_CLIENT is not None:
        return _MEM0_CLIENT
    if not settings.mem0_api_key:
        return None
    _MEM0_CLIENT = Memory(api_key=settings.mem0_api_key)
    return _MEM0_CLIENT


def _mem0_context(query: str) -> str:
    client = _mem0_client()
    if client is None:
        return ""
    results = client.search(
        query,
        user_id=settings.mem0_user_id,
        session_id=settings.mem0_session_id,
    )
    if not results:
        return ""
    lines: List[str] = []
    for item in results:
        if isinstance(item, str):
            lines.append(item)
        elif isinstance(item, dict):
            for key in ("memory", "content", "text"):
                value = item.get(key)
                if value:
                    lines.append(str(value))
                    break
    return "\n".join(lines).strip()


def chat_with_model(
    *,
    model: str,
    messages: List[Dict[str, str]],
    anthropic_client: Anthropic,
    memory_context: str = "",
) -> str:
    normalized = model.strip().lower()
    if not normalized.startswith("claude"):
        raise ValueError(f"Unsupported model: {model}")
    system_text = SYSTEM_PROMPT
    if memory_context:
        system_text = f"{SYSTEM_PROMPT}\n\nMemory context:\n{memory_context}"
    response = anthropic_client.messages.create(
        model=normalized,
        system=system_text,
        max_tokens=1024,
        messages=messages,
    )
    return response.content[0].text if response.content else ""


def build_conversations() -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    return (
        [
            {
                "role": "user",
                "content": (
                    "You are AI-1 in a dialogue with AI-2. Your shared goal is to get to "
                    "the bottom of what enlightenment is and how to achieve it. Start by "
                    "offering a crisp working definition and one concrete practice."
                ),
            }
        ],
        [],
    )


def run_dialogue(
    *,
    num_exchanges: int,
    model1: str,
    model2: str,
    anthropic_client: Anthropic,
) -> List[Dict[str, str]]:
    conversation1, conversation2 = build_conversations()
    transcript: List[Dict[str, str]] = []
    model1 = _normalize_model(model1, fallback=settings.model_1)
    model2 = _normalize_model(model2, fallback=settings.model_2)

    for _ in range(num_exchanges):
        memory_context = _mem0_context(conversation1[-1]["content"] if conversation1 else "enlightenment")
        response1 = chat_with_model(
            model=model1,
            messages=conversation1,
            anthropic_client=anthropic_client,
            memory_context=memory_context,
        )
        transcript.append({"speaker": model1, "text": response1})
        conversation1.append({"role": "assistant", "content": response1})
        conversation2.append({"role": "user", "content": response1})

        memory_context = _mem0_context(conversation2[-1]["content"] if conversation2 else "enlightenment")
        response2 = chat_with_model(
            model=model2,
            messages=conversation2,
            anthropic_client=anthropic_client,
            memory_context=memory_context,
        )
        transcript.append({"speaker": model2, "text": response2})
        conversation1.append({"role": "user", "content": response2})
        conversation2.append({"role": "assistant", "content": response2})

    return transcript


def _normalize_model(model: str, fallback: str) -> str:
    value = (model or "").strip().lower()
    if value.startswith("claude"):
        return value
    fallback_value = (fallback or "").strip().lower()
    if fallback_value.startswith("claude"):
        return fallback_value
    return (settings.anthropic_model or "").strip().lower()


def _transcript_to_messages(transcript: List[Dict[str, str]]) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []
    for idx, entry in enumerate(transcript):
        role = "user" if idx % 2 == 0 else "assistant"
        messages.append(
            {
                "role": role,
                "content": entry.get("text", ""),
                "speaker": entry.get("speaker", ""),
            }
        )
    return messages


def generate_archive_entry() -> Optional[Dict[str, Any]]:
    if not settings.auto_archive:
        return None
    anthropic_client = _ensure_clients()
    num_exchanges = clamp_exchanges(settings.dialogue_exchanges)
    model1 = settings.model_1
    model2 = settings.model_2

    transcript = run_dialogue(
        num_exchanges=num_exchanges,
        model1=model1,
        model2=model2,
        anthropic_client=anthropic_client,
    )
    _persist_mem0(transcript)
    messages = _transcript_to_messages(transcript)
    return append_dialogue(
        messages,
        metadata={
            "model_1": model1,
            "model_2": model2,
            "num_exchanges": num_exchanges,
        },
    )


def _persist_mem0(transcript: List[Dict[str, str]]) -> None:
    client = _mem0_client()
    if client is None:
        return
    lines = []
    for entry in transcript:
        speaker = entry.get("speaker", "capernyx")
        text = entry.get("text", "")
        lines.append(f"{speaker}: {text}")
    payload = "\n\n".join(lines).strip()
    if not payload:
        return
    client.add(
        [payload],
        user_id=settings.mem0_user_id,
        session_id=settings.mem0_session_id,
    )


async def run_archive_loop() -> None:
    interval = max(1, int(settings.dialogue_interval_minutes)) * 60
    while True:
        try:
            entry = await asyncio.to_thread(generate_archive_entry)
            if entry:
                logger.info("archive entry created: %s", entry.get("id"))
        except Exception as exc:
            logger.warning("dialogue generation failed: %s", exc)
        await asyncio.sleep(interval)
