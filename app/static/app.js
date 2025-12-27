const archiveList = document.getElementById("archiveList");
const archiveStatus = document.getElementById("status");
const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");
const clearSearchBtn = document.getElementById("clearSearchBtn");
const conversationLog = document.getElementById("conversationLog");
const entryMeta = document.getElementById("entryMeta");

function setStatus(text) {
  if (archiveStatus) {
    archiveStatus.textContent = text;
  }
  if (entryMeta) {
    entryMeta.textContent = text;
  }
}

function renderArchiveItem(item) {
  const link = document.createElement("a");
  link.className = "log-entry archive-entry";
  link.href = `/archive/${item.id}`;

  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = item.created_at ? `Logged ${item.created_at}` : "Logged";

  const preview = document.createElement("div");
  preview.className = "preview";
  preview.textContent = item.preview || "No preview available.";

  link.appendChild(meta);
  link.appendChild(preview);
  return link;
}

function renderConversationMessage(message, index) {
  const wrap = document.createElement("div");
  wrap.className = "message-line";

  const label = document.createElement("div");
  label.className = "message-role";
  const speaker = message.speaker ? ` ${message.speaker}` : "";
  label.textContent = `capernyx${speaker}`;

  const body = document.createElement("div");
  body.className = "message-content";
  body.textContent = message.content || "";

  wrap.appendChild(label);
  wrap.appendChild(body);
  return wrap;
}

async function loadArchive() {
  if (!archiveList) {
    return;
  }
  setStatus("Retrieving archive...");
  try {
    const query = searchInput && searchInput.value.trim();
    const url = query ? `/v1/archive?search=${encodeURIComponent(query)}` : "/v1/archive";
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error("Archive fetch failed");
    }
    const data = await response.json();
    const items = Array.isArray(data) ? data : data.items || [];
    archiveList.innerHTML = "";
    if (!items.length) {
      archiveList.innerHTML = query
        ? '<div class="log-entry">no matches found.</div>'
        : '<div class="log-entry">no archived conversations yet.</div>';
    } else {
      items.reverse().forEach((item) => {
        archiveList.appendChild(renderArchiveItem(item));
      });
    }
    setStatus(`Loaded ${items.length} sessions.`);
  } catch (err) {
    setStatus("Archive unreachable.");
  }
}

async function loadConversation() {
  if (!conversationLog) {
    return;
  }
  const parts = window.location.pathname.split("/");
  const entryId = parts[parts.length - 1] || "";
  if (!entryId) {
    setStatus("missing entry id.");
    return;
  }
  setStatus("loading session...");
  try {
    const response = await fetch(`/v1/archive/${entryId}`);
    if (!response.ok) {
      throw new Error("Entry fetch failed");
    }
    const entry = await response.json();
    if (entry.error) {
      setStatus("session not found.");
      return;
    }
    const createdAt = entry.created_at ? `Logged ${entry.created_at}` : "Logged";
    if (entryMeta) {
      entryMeta.textContent = createdAt;
    }
    conversationLog.innerHTML = "";
    const messages = entry.messages || [];
    if (!messages.length) {
      conversationLog.innerHTML = '<div class="log-entry">no messages found.</div>';
      return;
    }
    messages.forEach((message, index) => {
      conversationLog.appendChild(renderConversationMessage(message, index));
    });
  } catch (err) {
    setStatus("session unreachable.");
  }
}

if (searchBtn) {
  searchBtn.addEventListener("click", () => loadArchive());
}

if (clearSearchBtn) {
  clearSearchBtn.addEventListener("click", () => {
    if (searchInput) {
      searchInput.value = "";
    }
    loadArchive();
  });
}

if (searchInput) {
  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      loadArchive();
    }
  });
}

loadArchive();
loadConversation();
