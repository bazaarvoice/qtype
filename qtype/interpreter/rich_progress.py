from __future__ import annotations

import logging
import threading
from collections import deque
from typing import Deque, Dict

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    Progress,
    ProgressColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.text import Text

from qtype.interpreter.types import ProgressCallback

logger = logging.getLogger(__name__)


class RateColumn(ProgressColumn):
    """Show processing speed as '123 msg/s' based on task.speed."""

    def __init__(self, unit: str = "msg") -> None:
        super().__init__()
        self.unit = unit

    def render(self, task) -> Text:  # type: ignore[override]
        speed = task.speed or 0.0

        if speed <= 0:
            return Text(f"- {self.unit}/s")

        # Simple formatting similar-ish to tqdm
        if speed < 1:
            rate_str = f"{speed:.2f}"
        elif speed < 100:
            rate_str = f"{speed:4.1f}"
        else:
            rate_str = f"{speed:4.0f}"

        return Text(f"{rate_str} {self.unit}/s")


class SparklineColumn(ProgressColumn):
    """Tiny throughput trend graph using block characters."""

    def __init__(self, max_samples: int = 20) -> None:
        super().__init__()
        self.max_samples = max_samples
        # Per-task speed history
        self._history: Dict[int, Deque[float]] = {}

    def render(self, task) -> Text:  # type: ignore[override]
        speed = task.speed or 0.0

        history = self._history.get(task.id)
        if history is None:
            history = self._history[task.id] = deque(maxlen=self.max_samples)

        history.append(speed)

        if not history or all(v <= 0 for v in history):
            return Text("")

        min_s = min(history)
        max_s = max(history)
        rng = max(max_s - min_s, 1e-9)

        blocks = "▁▂▃▄▅▆▇█"
        n_blocks = len(blocks)

        chars = []
        for v in history:
            idx = int((v - min_s) / rng * (n_blocks - 1))
            chars.append(blocks[idx])

        return Text("".join(chars))


class RichProgressCallback(ProgressCallback):
    """Progress callback that uses Rich to display progress bars.

    Displays a progress row for each step, updating in place.
    Colors the step label based on error rate:
        - Green: error rate <= 1%
        - Yellow: 1% < error rate <= 5%
        - Red: error rate > 5%

    Attributes:
        order: Optional list defining the order of steps progress rows.
    """

    def __init__(
        self,
        order: list[str] | None = None,
    ) -> None:
        super().__init__()
        self.order = order or []
        self._lock = threading.Lock()
        self.console = Console()

        # One shared Progress instance for all steps
        # Columns: description | bar | % | rate | sparkline | ✔ | ✖ | elapsed | remaining
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            TaskProgressColumn(),
            RateColumn(unit="msg"),
            SparklineColumn(max_samples=20),
            TextColumn("[green]✔[/green] {task.fields[succeeded]} succeeded"),
            TextColumn("[red]✖[/red] {task.fields[errors]} errors"),
            TextColumn("[cyan]⟳[/cyan] {task.fields[cache_hits]} hits"),
            TextColumn(
                "[magenta]✗[/magenta] {task.fields[cache_misses]} misses"
            ),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=True,
        )

        # Wrap progress in a panel
        self.panel = Panel(
            self.progress,
            title="[bold cyan]Flow Progress[/bold cyan]",
            border_style="bright_blue",
            padding=(1, 2),
        )

        # Live container for the panel
        self.live = Live(
            self.panel,
            console=self.console,
            refresh_per_second=10,
        )

        # Map step_id -> Rich task id
        self.tasks: Dict[str, int] = {}
        self._started = False

        # Pre-create tasks in the desired order if provided
        for step_id in self.order:
            task_id = self.progress.add_task(
                f"Step {step_id}",
                total=None,  # we’ll update this once we know it
                succeeded=0,
                errors=0,
            )
            self.tasks[step_id] = task_id

    def _ensure_started(self) -> None:
        if not self._started:
            self.live.start()
            self._started = True

    def __call__(
        self,
        step_id: str,
        items_processed: int,
        items_in_error: int,
        items_succeeded: int,
        total_items: int | None,
        cache_hits: int | None = None,
        cache_misses: int | None = None,
    ) -> None:
        with self._lock:
            self._ensure_started()

            # Create a task lazily if we didn't pre-create it
            if step_id not in self.tasks:
                task_id = self.progress.add_task(
                    f"Step {step_id}",
                    total=total_items,
                    succeeded=items_succeeded,
                    errors=items_in_error,
                    cache_hits=cache_hits,
                    cache_misses=cache_misses,
                )
                self.tasks[step_id] = task_id

            task_id = self.tasks[step_id]
            color = self.compute_color(items_processed, items_in_error)

            update_kwargs = {
                "completed": items_processed,
                "succeeded": items_succeeded,
                "errors": items_in_error,
                "description": f"[{color}]Step {step_id}[/{color}]",
            }

            update_kwargs["cache_hits"] = (
                cache_hits if cache_hits is not None else "-"
            )
            update_kwargs["cache_misses"] = (
                cache_misses if cache_misses is not None else "-"
            )
            if total_items is not None:
                update_kwargs["total"] = total_items

            self.progress.update(task_id, **update_kwargs)

    def compute_color(self, items_processed: int, items_in_error: int) -> str:
        # Avoid divide-by-zero
        if items_processed == 0:
            return "green"

        error_rate = items_in_error / items_processed

        if error_rate > 0.05:
            return "red"
        elif error_rate > 0.01:
            return "yellow"
        else:
            return "green"

    def close(self) -> None:
        with self._lock:
            if self._started:
                self.live.stop()
                self._started = False
