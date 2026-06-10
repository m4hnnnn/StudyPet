import os
from typing import Optional

import httpx
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Static

API_URL = os.environ.get("STUDYPET_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# API helper
# ---------------------------------------------------------------------------

async def _api(method: str, path: str, **kwargs) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(base_url=API_URL, timeout=10.0) as client:
            r = await getattr(client, method)(path, **kwargs)
        if r.status_code == 204:
            return None
        data = r.json()
        if not r.is_success:
            raise ValueError(data.get("detail", f"HTTP {r.status_code}"))
        return data
    except httpx.ConnectError:
        raise ValueError(f"Cannot connect to server at {API_URL}")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class StudyPetApp(App):
    TITLE = "StudyPet"

    CSS = """
    #main-grid {
        layout: horizontal;
        height: 1fr;
    }
    #pet-panel {
        width: 36;
        border: round $primary;
        padding: 1 2;
        margin: 1 0 0 1;
    }
    #pet-heading {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    #tasks-panel {
        border: round $accent;
        padding: 1;
        margin: 1 1 0 1;
        layout: vertical;
    }
    #task-table {
        height: 1fr;
    }
    #add-form {
        height: 3;
        layout: horizontal;
        margin-top: 1;
    }
    #title-input {
        width: 2fr;
    }
    #desc-input {
        width: 2fr;
    }
    #add-btn {
        width: 10;
    }
    """

    BINDINGS = [
        Binding("c", "complete_task", "Complete"),
        Binding("d", "delete_task", "Delete"),
        Binding("r", "refresh_all", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tasks: list[dict] = []

    # ── Layout ────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-grid"):
            with Vertical(id="pet-panel"):
                yield Label("Your Pet", id="pet-heading")
                yield Static("Connecting...", id="pet-info")
            with Vertical(id="tasks-panel"):
                yield DataTable(id="task-table", cursor_type="row")
                with Horizontal(id="add-form"):
                    yield Input(placeholder="Task title...", id="title-input")
                    yield Input(placeholder="Description (optional)", id="desc-input")
                    yield Button("Add", id="add-btn", variant="success")
        yield Footer()

    async def on_mount(self) -> None:
        table = self.query_one("#task-table", DataTable)
        table.add_column("ID", width=5)
        table.add_column("Title", width=28)
        table.add_column("Status", width=9)
        table.add_column("Description")
        await self._refresh_all()

    # ── Data loading ──────────────────────────────────────────────────────

    async def _refresh_all(self) -> None:
        await self._load_pet()
        await self._load_tasks()

    async def _load_pet(self) -> None:
        try:
            pet = await _api("get", "/pet")
            self._render_pet(pet)
        except ValueError as exc:
            self.query_one("#pet-info", Static).update(f"[red]{exc}[/]")

    def _render_pet(self, pet: dict) -> None:
        mood_color = {
            "sad": "blue",
            "okay": "yellow",
            "happy": "green",
            "ecstatic": "magenta",
        }
        color = mood_color.get(pet["mood"], "white")
        to_next = pet["xp_to_next_level"]
        filled = round((100 - to_next) / 10)
        bar = "[" + "#" * filled + "-" * (10 - filled) + "]"
        text = (
            f"[bold]{pet['name']}[/bold]\n\n"
            f"Level : [cyan]{pet['level']}[/cyan]\n"
            f"XP    : {pet['xp']}\n"
            f"       {bar}\n"
            f"       ({to_next} to next)\n\n"
            f"Mood  : [{color}]{pet['mood']}[/{color}]"
        )
        self.query_one("#pet-info", Static).update(text)

    async def _load_tasks(self) -> None:
        try:
            self._tasks = await _api("get", "/tasks") or []
            self._render_tasks()
        except ValueError as exc:
            self.notify(str(exc), severity="error")

    def _render_tasks(self) -> None:
        table = self.query_one("#task-table", DataTable)
        table.clear()
        for t in self._tasks:
            status = "Done" if t["completed"] else "Pending"
            table.add_row(
                str(t["id"]),
                t["title"],
                status,
                t.get("description") or "",
            )

    def _selected_task_id(self) -> Optional[int]:
        table = self.query_one("#task-table", DataTable)
        idx = table.cursor_row
        if not self._tasks or idx < 0 or idx >= len(self._tasks):
            return None
        return self._tasks[idx]["id"]

    # ── Actions ───────────────────────────────────────────────────────────

    async def action_refresh_all(self) -> None:
        await self._refresh_all()
        self.notify("Refreshed")

    async def action_complete_task(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            self.notify("No task selected", severity="warning")
            return
        try:
            data = await _api("put", f"/tasks/{task_id}/complete")
            self.notify(f"+{data['xp_earned']} XP  |  mood: {data['pet']['mood']}")
            await self._refresh_all()
        except ValueError as exc:
            self.notify(str(exc), severity="error")

    async def action_delete_task(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            self.notify("No task selected", severity="warning")
            return
        try:
            await _api("delete", f"/tasks/{task_id}")
            self.notify("Task deleted")
            await self._load_tasks()
        except ValueError as exc:
            self.notify(str(exc), severity="error")

    # ── Add task ──────────────────────────────────────────────────────────

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-btn":
            await self._add_task()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        await self._add_task()

    async def _add_task(self) -> None:
        title_input = self.query_one("#title-input", Input)
        desc_input  = self.query_one("#desc-input", Input)
        title = title_input.value.strip()
        if not title:
            self.notify("Title is required", severity="warning")
            return
        desc = desc_input.value.strip() or None
        payload: dict = {"title": title}
        if desc:
            payload["description"] = desc
        try:
            await _api("post", "/tasks", json=payload)
            title_input.value = ""
            desc_input.value  = ""
            await self._load_tasks()
            self.notify(f"Added: {title}")
        except ValueError as exc:
            self.notify(str(exc), severity="error")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    StudyPetApp().run()


if __name__ == "__main__":
    main()
