"""
Basic observability utilities:
- run_id and stage context propagation
- error classification (severity + error_code)
- stage metrics and run summary
"""

from __future__ import annotations

import datetime
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Dict, Optional


_run_id_ctx: ContextVar[str] = ContextVar("run_id", default="-")
_stage_ctx: ContextVar[str] = ContextVar("stage", default="-")


def create_run_id() -> str:
    now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    return f"run-{now}-{suffix}"


def set_run_id(run_id: str):
    _run_id_ctx.set(run_id)


def get_run_id() -> str:
    return _run_id_ctx.get()


def set_stage(stage: str):
    _stage_ctx.set(stage)


def clear_stage():
    _stage_ctx.set("-")


def get_stage() -> str:
    return _stage_ctx.get()


def classify_error(stage: str, exc: Exception) -> tuple[str, str]:
    """
    Returns (severity, error_code).
    Severity: CRITICAL | HIGH | MEDIUM | LOW
    """
    base = stage.upper()
    root_exc = exc.__cause__ if getattr(exc, "__cause__", None) else exc

    if stage == "config":
        return "CRITICAL", "E_CFG_VALIDATION"
    if isinstance(root_exc, TimeoutError):
        return "HIGH", f"E_{base}_TIMEOUT"
    if isinstance(root_exc, ValueError):
        return "HIGH", f"E_{base}_VALUE"
    if isinstance(root_exc, ConnectionError):
        return "HIGH", f"E_{base}_NETWORK"
    if isinstance(root_exc, RuntimeError):
        return "MEDIUM", f"E_{base}_RUNTIME"
    return "MEDIUM", f"E_{base}_FAILED"


@dataclass
class StageStats:
    attempts: int = 0
    success: bool = False
    duration_ms: int = 0
    error_code: str = ""
    severity: str = ""
    error_message: str = ""


@dataclass
class RunMetrics:
    run_id: str
    started_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    stages: Dict[str, StageStats] = field(default_factory=dict)
    counters: Dict[str, int] = field(default_factory=dict)
    _stage_timers: Dict[str, float] = field(default_factory=dict)

    def start_stage(self, stage: str):
        self._stage_timers[stage] = time.perf_counter()
        if stage not in self.stages:
            self.stages[stage] = StageStats()

    def end_stage_success(self, stage: str, attempts: int = 1):
        st = self.stages.setdefault(stage, StageStats())
        st.attempts = attempts
        st.success = True
        started = self._stage_timers.pop(stage, None)
        if started is not None:
            st.duration_ms = int((time.perf_counter() - started) * 1000)

    def end_stage_failure(self, stage: str, attempts: int, error_code: str, severity: str, message: str):
        st = self.stages.setdefault(stage, StageStats())
        st.attempts = attempts
        st.success = False
        st.error_code = error_code
        st.severity = severity
        st.error_message = message[:200]
        started = self._stage_timers.pop(stage, None)
        if started is not None:
            st.duration_ms = int((time.perf_counter() - started) * 1000)

    def set_counter(self, key: str, value: int):
        self.counters[key] = int(value)

    def summary(self) -> dict:
        ended_at = datetime.datetime.now().isoformat()
        stage_count = len(self.stages)
        success_count = len([s for s in self.stages.values() if s.success])
        success_rate = round((success_count / stage_count) * 100, 2) if stage_count else 0.0
        total_duration_ms = sum(s.duration_ms for s in self.stages.values())
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "ended_at": ended_at,
            "stage_count": stage_count,
            "stage_success_count": success_count,
            "stage_success_rate": success_rate,
            "total_duration_ms": total_duration_ms,
            "counters": self.counters,
            "stages": {k: vars(v) for k, v in self.stages.items()},
        }
