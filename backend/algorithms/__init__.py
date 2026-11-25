"""Algorithms package for graph-based exam scheduling."""

from .graph_builder import build_conflict_graph, get_graph_metrics
from .coloring import (
    dsatur_coloring,
    get_schedule_summary,
    welsh_powell_coloring,
    compare_coloring_algorithms,
)

__all__ = [
    "build_conflict_graph",
    "get_graph_metrics",
    "dsatur_coloring",
    "get_schedule_summary",
    "welsh_powell_coloring",
    "compare_coloring_algorithms",
]
