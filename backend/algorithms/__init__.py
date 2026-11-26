"""Algorithms package for graph-based exam scheduling."""

from .graph_builder import build_conflict_graph, get_graph_metrics
from .coloring import (
    dsatur_coloring,
    get_schedule_summary,
    welsh_powell_coloring,
    compare_coloring_algorithms,
)
from .room_allocator import (
    allocate_shift_rooms_ffd,
    allocate_exam_rooms_ffd,
    allocate_graph_schedule_rooms_ffd,
    split_course_into_rooms,
    allocate_shift_rooms_with_overflow,
    allocate_exam_rooms_with_spilling,
    allocate_graph_schedule_with_overflow,
)

__all__ = [
    "build_conflict_graph",
    "get_graph_metrics",
    "dsatur_coloring",
    "get_schedule_summary",
    "welsh_powell_coloring",
    "compare_coloring_algorithms",
    "allocate_shift_rooms_ffd",
    "allocate_exam_rooms_ffd",
    "allocate_graph_schedule_rooms_ffd",
    "split_course_into_rooms",
    "allocate_shift_rooms_with_overflow",
    "allocate_exam_rooms_with_spilling",
    "allocate_graph_schedule_with_overflow",
]
