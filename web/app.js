const API_URL = "http://127.0.0.1:8000";

let currentFilter = "";   // "" | "true" | "false"

// ── API helpers ───────────────────────────────────────────────────────────

async function apiFetch(method, path, body) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);

  const res = await fetch(API_URL + path, opts);
  if (res.status === 204) return null;   // DELETE success

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || `HTTP ${res.status}`);
  }
  return data;
}

// ── Pet ───────────────────────────────────────────────────────────────────

async function loadPet() {
  try {
    const pet = await apiFetch("GET", "/pet");
    renderPet(pet);
  } catch (err) {
    showStatus(`Could not load pet: ${err.message}`, "error");
  }
}

function renderPet(pet) {
  document.getElementById("pet-name").textContent = pet.name;
  document.getElementById("pet-level").textContent = pet.level;
  document.getElementById("pet-xp").textContent = `${pet.xp} XP`;

  const badge = document.getElementById("pet-mood");
  badge.textContent = pet.mood;
  badge.className = `mood-badge mood-${pet.mood}`;

  const pct = Math.round(((100 - pet.xp_to_next_level) / 100) * 100);
  document.getElementById("xp-bar").style.width = `${Math.max(pct, 0)}%`;
  document.getElementById("xp-label").textContent =
    `${pet.xp_to_next_level} XP to level ${pet.level + 1}`;
}

// ── Tasks ─────────────────────────────────────────────────────────────────

async function loadTasks() {
  try {
    const url = currentFilter !== ""
      ? `/tasks?completed=${currentFilter}`
      : "/tasks";
    const tasks = await apiFetch("GET", url);
    renderTasks(tasks);
  } catch (err) {
    showStatus(`Could not load tasks: ${err.message}`, "error");
  }
}

function renderTasks(tasks) {
  const list = document.getElementById("task-list");
  const empty = document.getElementById("empty-msg");
  list.innerHTML = "";

  if (tasks.length === 0) {
    empty.classList.remove("hidden");
    return;
  }
  empty.classList.add("hidden");

  tasks.forEach(task => list.appendChild(buildTaskItem(task)));
}

function buildTaskItem(task) {
  const li = document.createElement("li");
  li.className = "task-item";
  li.dataset.id = task.id;

  // Circle check indicator
  const check = document.createElement("div");
  check.className = task.completed ? "task-check done" : "task-check";
  check.textContent = task.completed ? "✓" : "";

  // Text body
  const body = document.createElement("div");
  body.className = "task-body";

  const title = document.createElement("div");
  title.className = task.completed ? "task-title done" : "task-title";
  title.textContent = task.title;
  body.appendChild(title);

  if (task.description) {
    const desc = document.createElement("div");
    desc.className = "task-desc";
    desc.textContent = task.description;
    body.appendChild(desc);
  }

  // Action buttons
  const actions = document.createElement("div");
  actions.className = "task-actions";

  if (!task.completed) {
    const btnDone = document.createElement("button");
    btnDone.className = "btn-complete";
    btnDone.textContent = "Done";
    btnDone.onclick = () => handleComplete(task.id);
    actions.appendChild(btnDone);
  }

  const btnDel = document.createElement("button");
  btnDel.className = "btn-delete";
  btnDel.textContent = "Delete";
  btnDel.onclick = () => handleDelete(task.id, task.title);
  actions.appendChild(btnDel);

  li.append(check, body, actions);
  return li;
}

// ── Actions ───────────────────────────────────────────────────────────────

async function handleAdd(e) {
  e.preventDefault();
  const title = document.getElementById("task-title").value.trim();
  const desc  = document.getElementById("task-desc").value.trim();
  if (!title) return;

  try {
    await apiFetch("POST", "/tasks", { title, description: desc || undefined });
    document.getElementById("task-title").value = "";
    document.getElementById("task-desc").value  = "";
    await loadTasks();
  } catch (err) {
    showStatus(`Add failed: ${err.message}`, "error");
  }
}

async function handleComplete(id) {
  try {
    const data = await apiFetch("PUT", `/tasks/${id}/complete`);
    renderPet(data.pet);
    showStatus(`+${data.xp_earned} XP earned!`, "info");
    await loadTasks();
  } catch (err) {
    showStatus(`Complete failed: ${err.message}`, "error");
  }
}

async function handleDelete(id, title) {
  if (!confirm(`Delete "${title}"?`)) return;
  try {
    await apiFetch("DELETE", `/tasks/${id}`);
    await loadTasks();
  } catch (err) {
    showStatus(`Delete failed: ${err.message}`, "error");
  }
}

// ── Status messages ───────────────────────────────────────────────────────

let statusTimer = null;
function showStatus(msg, type) {
  const el = document.getElementById("status-msg");
  el.textContent = msg;
  el.className = `status-msg ${type}`;
  el.classList.remove("hidden");
  clearTimeout(statusTimer);
  statusTimer = setTimeout(() => el.classList.add("hidden"), 4000);
}

// ── Boot ──────────────────────────────────────────────────────────────────

document.getElementById("add-form").addEventListener("submit", handleAdd);

document.querySelectorAll(".filter-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentFilter = btn.dataset.filter;
    loadTasks();
  });
});

loadPet();
loadTasks();
