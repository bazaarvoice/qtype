import logging
import time

from qtype.interpreter.types import ProgressCallback


class LoggingProgressCallback(ProgressCallback):
    def __init__(self, log_every_seconds: float = 120.0) -> None:
        super().__init__()
        self.log_every_seconds = log_every_seconds
        self._last_log: dict[str, float] = {}
        self._totals: dict[str, int | None] = {}

    def __call__(
        self,
        step_id: str,
        items_processed: int,
        items_in_error: int,
        items_succeeded: int,
        total_items: int | None,
        cache_hits: int | None,
        cache_misses: int | None,
    ) -> None:
        logger = logging.getLogger(__name__)
        now = time.monotonic()
        last = self._last_log.get(step_id, 0.0)

        self._totals[step_id] = total_items

        if now - last < self.log_every_seconds:
            return

        self._last_log[step_id] = now
        total_str = (
            f"{items_processed}/{total_items}"
            if total_items is not None
            else f"{items_processed}"
        )
        if cache_hits is not None or cache_misses is not None:
            logger.info(
                "Step %s: processed=%s, succeeded=%s, errors=%s, "
                "cache_hits=%s, cache_misses=%s",
                step_id,
                total_str,
                items_succeeded,
                items_in_error,
                cache_hits if cache_hits is not None else "-",
                cache_misses if cache_misses is not None else "-",
            )
        else:
            logger.info(
                "Step %s: processed=%s, succeeded=%s, errors=%s",
                step_id,
                total_str,
                items_succeeded,
                items_in_error,
            )

    def close(self) -> None:
        # optional: final summary logging
        pass
