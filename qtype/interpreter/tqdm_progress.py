from __future__ import annotations

import logging
import threading

from tqdm import tqdm

from qtype.interpreter.types import ProgressCallback

logger = logging.getLogger(__name__)


class TQDMProgressCallback(ProgressCallback):
    """Progress callback that uses tqdm to display progress bars.
    Displays a progress bar for each step, updating in place.
    Colors the progress bar based on error rate:
        - Green: error rate <= 1%
        - Yellow: 1% < error rate <= 5%
        - Red: error rate > 5%
    Attributes:
        order: Optional list defining the order of steps progress bars.
    """

    def __init__(
        self,
        order: list[str] | None = None,
    ) -> None:
        super().__init__()
        self.callbacks: dict[str, tqdm] = {}
        self._lock = threading.Lock()
        self.order = order

    def __call__(
        self,
        step_id: str,
        items_processed: int,
        items_in_error: int,
        items_succeeded: int,
        total_items: int | None,
    ) -> None:
        with self._lock:
            if step_id not in self.callbacks:
                self.callbacks[step_id] = self._new(step_id, total_items)
            bar = self.callbacks[step_id]
            if not bar.disable:
                delta = items_processed - bar.n
                bar.set_postfix(
                    succeeded=items_succeeded,
                    errors=items_in_error,
                    refresh=False,
                )
                bar.update(delta)
                color = self.compute_color(items_processed, items_in_error)
                if bar.colour != color:
                    bar.colour = color
                    bar.refresh()
                if total_items is not None and items_processed >= total_items:
                    bar.close()

    def _new(self, step_id: str, total_items: int | None) -> tqdm:
        if self.order is not None:
            position = self.order.index(step_id)
        else:
            position = len(self.callbacks)
        return tqdm(
            total=total_items,
            desc=f"Step {step_id}",
            unit=" messages",
            dynamic_ncols=True,
            colour="green",
            position=position,
            mininterval=0.3,
            smoothing=0.1,
        )

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

    def close(self):
        for progress_bar in self.callbacks.values():
            progress_bar.close()
