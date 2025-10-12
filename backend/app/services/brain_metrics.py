"""
In-memory metrics for Single Brain (Stage 7):
- resolver_counts: how many times each rule answered
- resolver_times_ms: cumulative time per rule
- cache_stats: counters of hit/miss per store key
"""
from __future__ import annotations

from typing import Dict
from collections import defaultdict
from datetime import datetime, timezone


class BrainMetrics:
    def __init__(self):
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.resolver_counts: Dict[str, int] = defaultdict(int)
        self.resolver_times_ms: Dict[str, int] = defaultdict(int)
        self.cache_hits: Dict[str, int] = defaultdict(int)
        self.cache_misses: Dict[str, int] = defaultdict(int)

    def record_resolver(self, rule: str, elapsed_ms: int) -> None:
        self.resolver_counts[rule] += 1
        self.resolver_times_ms[rule] += int(elapsed_ms)

    def record_cache(self, area: str, hit: bool) -> None:
        if hit:
            self.cache_hits[area] += 1
        else:
            self.cache_misses[area] += 1

    def snapshot(self) -> Dict[str, dict]:
        return {
            "started_at": self.started_at,
            "resolver_counts": dict(self.resolver_counts),
            "resolver_times_ms": dict(self.resolver_times_ms),
            "cache_hits": dict(self.cache_hits),
            "cache_misses": dict(self.cache_misses),
        }


brain_metrics = BrainMetrics()