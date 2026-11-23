"""Unit tests for Graph Builder module (UC08.1)."""

import sys
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH để có thể import backend
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.algorithms.graph_builder import build_conflict_graph, get_graph_metrics


def test_empty_input():
    G = build_conflict_graph([])
    metrics = get_graph_metrics(G)
    assert metrics["total_nodes"] == 0
    assert metrics["total_edges"] == 0
    assert metrics["density"] == 0.0
    assert metrics["max_degree"] == 0
    assert metrics["isolated_nodes"] == []


def test_isolated_courses():
    # 3 sinh viên thi 3 môn hoàn toàn tách biệt
    registrations = [
        {"mssv": "SV01", "ma_mon": "CS101"},
        {"mssv": "SV02", "ma_mon": "CS102"},
        {"mssv": "SV03", "ma_mon": "CS103"},
    ]
    G = build_conflict_graph(registrations)
    metrics = get_graph_metrics(G)

    assert metrics["total_nodes"] == 3
    assert metrics["total_edges"] == 0
    assert metrics["density"] == 0.0
    assert len(metrics["isolated_nodes"]) == 3
    assert G.nodes["CS101"]["size"] == 1
    assert G.nodes["CS101"]["ten_mon"] == ""
    assert G.nodes["CS102"]["size"] == 1
    assert G.nodes["CS103"]["size"] == 1


def test_triangle_conflict_clique():
    # 1 sinh viên thi cả 3 môn -> tạo thành tam giác K_3 (3 đỉnh, 3 cạnh)
    registrations = [
        {"mssv": "SV01", "ma_mon": "CS101"},
        {"mssv": "SV01", "ma_mon": "CS102"},
        {"mssv": "SV01", "ma_mon": "CS103"},
    ]
    G = build_conflict_graph(registrations)
    metrics = get_graph_metrics(G)

    assert metrics["total_nodes"] == 3
    assert metrics["total_edges"] == 3
    assert metrics["max_degree"] == 2
    assert metrics["min_degree"] == 2
    assert metrics["avg_degree"] == 2.0
    assert metrics["isolated_nodes"] == []
    assert G["CS101"]["CS102"]["weight"] == 1
    assert G["CS102"]["CS103"]["weight"] == 1
    assert G["CS101"]["CS103"]["weight"] == 1


def test_overlapping_weights_and_degrees():
    # SV01 thi CS101, CS102
    # SV02 thi CS101, CS102
    # SV03 thi CS102, CS103
    registrations = [
        {"mssv": "SV01", "ma_mon": "CS101"},
        {"mssv": "SV01", "ma_mon": "CS102"},
        {"mssv": "SV02", "ma_mon": "CS101"},
        {"mssv": "SV02", "ma_mon": "CS102"},
        {"mssv": "SV03", "ma_mon": "CS102"},
        {"mssv": "SV03", "ma_mon": "CS103"},
    ]
    G = build_conflict_graph(registrations)
    metrics = get_graph_metrics(G)

    assert metrics["total_nodes"] == 3
    assert metrics["total_edges"] == 2
    # Cạnh (CS101, CS102) có 2 sinh viên trùng
    assert G["CS101"]["CS102"]["weight"] == 2
    # Cạnh (CS102, CS103) có 1 sinh viên trùng
    assert G["CS102"]["CS103"]["weight"] == 1
    # Không có cạnh giữa CS101 và CS103
    assert not G.has_edge("CS101", "CS103")

    # Kích thước từng môn (số lượng sinh viên)
    assert G.nodes["CS101"]["size"] == 2
    assert G.nodes["CS102"]["size"] == 3
    assert G.nodes["CS103"]["size"] == 1

    # Bậc đỉnh: CS102 có bậc 2, CS101 bậc 1, CS103 bậc 1
    assert G.degree["CS102"] == 2
    assert G.degree["CS101"] == 1
    assert G.degree["CS103"] == 1
    assert metrics["max_degree"] == 2
    assert metrics["min_degree"] == 1
    assert list(metrics["degrees"].keys())[0] == "CS102"


def test_course_metadata_support():
    courses = [
        {"ma_mon": "CS101", "ten_mon": "Cấu trúc dữ liệu"},
        {"ma_mon": "MA101", "ten_mon": "Giải tích 1"},
    ]
    registrations = [
        {"mssv": "SV01", "ma_mon": "CS101"},
    ]
    G = build_conflict_graph(registrations, courses=courses)
    metrics = get_graph_metrics(G)

    assert metrics["total_nodes"] == 2
    assert metrics["total_edges"] == 0
    assert G.nodes["CS101"]["ten_mon"] == "Cấu trúc dữ liệu"
    assert G.nodes["CS101"]["size"] == 1
    assert G.nodes["MA101"]["ten_mon"] == "Giải tích 1"
    assert G.nodes["MA101"]["size"] == 0
    assert "MA101" in metrics["isolated_nodes"]


def test_tuple_and_list_format():
    registrations = [
        ("SV01", "CS101"),
        ("SV01", "CS102"),
        ["SV02", "CS101"],
        ["SV02", "CS102"],
    ]
    G = build_conflict_graph(registrations)
    assert G.number_of_nodes() == 2
    assert G.number_of_edges() == 1
    assert G["CS101"]["CS102"]["weight"] == 2


def test_duplicate_registrations():
    registrations = [
        ("SV01", "CS101"),
        ("SV01", "CS101"),
        ("SV01", "CS102"),
        {"mssv": "SV01", "ma_mon": "CS102"},
    ]
    G = build_conflict_graph(registrations)
    assert G.number_of_nodes() == 2
    assert G.number_of_edges() == 1
    assert G.nodes["CS101"]["size"] == 1
    assert G.nodes["CS102"]["size"] == 1
    assert G["CS101"]["CS102"]["weight"] == 1


def test_none_and_whitespace_inputs():
    courses = [
        {"ma_mon": " CS101 ", "ten_mon": "Cấu trúc dữ liệu"},
        {"ma_mon": None, "ten_mon": "Không hợp lệ"},
    ]
    registrations = [
        {"mssv": None, "ma_mon": "CS101"},
        (None, "CS102"),
        ("SV01", None),
        ("  ", "CS101"),
        {"mssv": " SV01 ", "ma_mon": " CS101 "},
    ]
    G = build_conflict_graph(registrations, courses=courses)
    assert list(G.nodes()) == ["CS101"]
    assert G.number_of_edges() == 0
    assert G.nodes["CS101"]["size"] == 1
    assert G.nodes["CS101"]["ten_mon"] == "Cấu trúc dữ liệu"


if __name__ == "__main__":
    test_empty_input()
    test_isolated_courses()
    test_triangle_conflict_clique()
    test_overlapping_weights_and_degrees()
    test_course_metadata_support()
    test_tuple_and_list_format()
    test_duplicate_registrations()
    test_none_and_whitespace_inputs()
    print("ALL GRAPH BUILDER TESTS PASSED!")
