import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from .settings import settings

_SUPABASE = None


def _supabase_client():
    global _SUPABASE
    if _SUPABASE is not None:
        return _SUPABASE
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None
    from supabase import create_client
    _SUPABASE = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _SUPABASE


def _supabase_table():
    return settings.supabase_table or "conversations"


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
    client = _supabase_client()
    if client is not None:
        table = _supabase_table()
        client.table(table).insert(item).execute()
        return item
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
    client = _supabase_client()
    if client is not None:
        table = _supabase_table()
        client.table(table).insert(item).execute()
        return item
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=True) + "\n")
    return item


def read_archive(limit: int | None = None, search: str | None = None) -> List[Dict[str, Any]]:
    client = _supabase_client()
    if client is not None:
        table = _supabase_table()
        query = client.table(table).select("*").order("created_at", desc=False)
        if search:
            query = query.ilike("preview", f"%{search}%")
        if limit is not None and limit >= 0:
            query = query.limit(limit)
        response = query.execute()
        return response.data or []
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
    if search:
        needle = search.lower()
        items = [item for item in items if needle in str(item.get("preview", "")).lower()]
    return items


def get_archive_item(entry_id: str) -> Dict[str, Any] | None:
    client = _supabase_client()
    if client is not None:
        table = _supabase_table()
        response = client.table(table).select("*").eq("id", entry_id).execute()
        if response.data:
            return response.data[0]
        return None
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
