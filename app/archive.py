import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from .settings import settings


def _archive_path() -> Path:
    return Path(settings.archive_path)


def ensure_archive_dir() -> Path:
    path = _archive_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()
    return path


def _preview(messages: List[Dict[str, str]]) -> str:
    for msg in messages:
        if msg.get("role") == "user" and msg.get("content"):
            return msg["content"].strip()[:160]
    for msg in messages:
        if msg.get("content"):
            return msg["content"].strip()[:160]
    return ""


def append_conversation(messages: List[Dict[str, str]], response_text: str) -> Dict[str, Any]:
    path = ensure_archive_dir()
    convo_messages = [*messages, {"role": "assistant", "content": response_text}]
    item = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "messages": convo_messages,
        "preview": _preview(convo_messages),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=True) + "\n")
    return item


def append_dialogue(
    messages: List[Dict[str, Any]],
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    path = ensure_archive_dir()
    item = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "messages": messages,
        "preview": _preview(messages),
    }
    if metadata:
        item["metadata"] = metadata
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=True) + "\n")
    return item


def read_archive(limit: int | None = None) -> List[Dict[str, Any]]:
    path = ensure_archive_dir()
    items: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if limit is not None and limit >= 0:
        items = items[-limit:]
    return items


def get_archive_item(entry_id: str) -> Dict[str, Any] | None:
    path = ensure_archive_dir()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("id") == entry_id:
                return item
    return None
