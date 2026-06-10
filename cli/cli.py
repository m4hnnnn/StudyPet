import os
import sys

import click
import httpx

API_URL = os.environ.get("STUDYPET_URL", "http://localhost:8000")

MOOD_LABEL = {
    "sad": "(sad)",
    "okay": "(okay)",
    "happy": "(happy)",
    "ecstatic": "(ecstatic!!)",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _client() -> httpx.Client:
    return httpx.Client(base_url=API_URL, timeout=10.0)


def _abort(msg: str) -> None:
    click.echo(f"Error: {msg}", err=True)
    sys.exit(1)


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    try:
        with _client() as c:
            return getattr(c, method)(path, **kwargs)
    except httpx.ConnectError:
        _abort(
            f"Cannot connect to the StudyPet server at {API_URL}\n"
            "  Start it with:  uv run studypet-server"
        )


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
def main() -> None:
    """StudyPet — virtual pet productivity tracker."""


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@main.command("pet")
def show_pet() -> None:
    """Show your pet's current status."""
    r = _request("get", "/pet")
    if r.status_code != 200:
        _abort(r.text)
    p = r.json()
    label = MOOD_LABEL.get(p["mood"], "")
    click.echo(f"\n[PET] {p['name']}")
    click.echo(f"  Level : {p['level']}")
    click.echo(f"  XP    : {p['xp']}  ({p['xp_to_next_level']} to next level)")
    click.echo(f"  Mood  : {p['mood']} {label}\n")


@main.command("tasks")
@click.option(
    "--completed",
    "filter_completed",
    type=click.BOOL,
    default=None,
    help="Filter: true = completed only, false = pending only",
)
def list_tasks(filter_completed: bool | None) -> None:
    """List tasks (all, pending, or completed)."""
    params: dict = {}
    if filter_completed is not None:
        params["completed"] = str(filter_completed).lower()

    r = _request("get", "/tasks", params=params)
    if r.status_code != 200:
        _abort(r.text)
    tasks = r.json()

    if not tasks:
        click.echo("No tasks found.")
        return

    for t in tasks:
        mark = click.style("[x]", fg="green") if t["completed"] else click.style("[ ]", fg="yellow")
        desc = f" -- {t['description']}" if t.get("description") else ""
        click.echo(f"  [{t['id']}] {mark} {t['title']}{desc}")


@main.command("add")
@click.argument("title")
@click.option("-d", "--description", default=None, help="Optional description")
def add_task(title: str, description: str | None) -> None:
    """Add a new task."""
    payload: dict = {"title": title}
    if description:
        payload["description"] = description

    r = _request("post", "/tasks", json=payload)
    if r.status_code != 201:
        _abort(r.text)
    task = r.json()
    click.echo(f"Added  [{task['id']}] {task['title']}")


@main.command("complete")
@click.argument("task_id", type=int)
def complete_task(task_id: int) -> None:
    """Complete a task by ID and earn XP."""
    r = _request("put", f"/tasks/{task_id}/complete")
    if r.status_code == 404:
        _abort(r.json().get("detail", f"Task {task_id} not found"))
    if r.status_code == 400:
        _abort(r.json().get("detail", r.text))
    if r.status_code != 200:
        _abort(r.text)

    data = r.json()
    task = data["task"]
    pet = data["pet"]
    xp = data["xp_earned"]
    label = MOOD_LABEL.get(pet["mood"], "")

    click.echo(click.style(f"[DONE] Completed: {task['title']}", fg="green"))
    click.echo(
        f"  +{xp} XP -> {pet['name']} is level {pet['level']} "
        f"({pet['xp']} XP)  mood: {pet['mood']} {label}"
    )


@main.command("delete")
@click.argument("task_id", type=int)
@click.confirmation_option(prompt="Delete this task?")
def delete_task(task_id: int) -> None:
    """Delete a task by ID."""
    r = _request("delete", f"/tasks/{task_id}")
    if r.status_code == 404:
        _abort(r.json().get("detail", f"Task {task_id} not found"))
    if r.status_code != 204:
        _abort(r.text)
    click.echo(f"Deleted task {task_id}.")


if __name__ == "__main__":
    main()
