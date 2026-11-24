"""Unit test suite for Welsh-Powell coloring algorithm and benchmark comparisons.

Kiểm thử toàn diện thuật toán tô màu Welsh-Powell (strategy='largest_first')
và so sánh đối chứng với DSatur theo yêu cầu Ngày 3 - Thành viên 1.
"""

import sys
from pathlib import Path
import networkx as nx

# Bổ sung thư mục gốc vào PYTHONPATH để import backend
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.algorithms import (
    build_conflict_graph,
    dsatur_coloring,
    welsh_powell_coloring,
    compare_coloring_algorithms,
    get_schedule_summary,
)


def test_empty_and_single_node():
    """Test 1: Đồ thị rỗng, None và đồ thị chỉ có 1 đỉnh duy nhất."""
    # 1.1 Đồ thị None
    res_none = welsh_powell_coloring(None)
    assert res_none["total_colors"] == 0
    assert res_none["color_map"] == {}
    assert res_none["is_valid"] is True
    assert res_none["conflicts_count"] == 0

    # 1.2 Đồ thị rỗng
    g_empty = nx.Graph()
    res_empty = welsh_powell_coloring(g_empty)
    assert res_empty["total_colors"] == 0
    assert res_empty["is_valid"] is True

    # 1.3 Đồ thị 1 đỉnh
    g_single = nx.Graph()
    g_single.add_node("CS101", ma_mon="CS101", ten_mon="Nhập môn lập trình", size=45)
    res_single = welsh_powell_coloring(g_single)
    assert res_single["total_colors"] == 1
    assert res_single["color_map"] == {"CS101": 1}
    assert res_single["shifts"] == {1: ["CS101"]}
    assert res_single["is_valid"] is True
    assert res_single["conflicts_count"] == 0
    print("✓ Test 1: Đồ thị rỗng & 1 đỉnh hoạt động chính xác.")


def test_independent_graph():
    """Test 2: Đồ thị độc lập (không có cạnh nào, không sinh viên nào thi trùng môn)."""
    G = nx.Graph()
    courses = ["MA101", "PH101", "CS101", "EN101"]
    for c in courses:
        G.add_node(c, ma_mon=c, ten_mon=f"Môn {c}", size=30)

    res = welsh_powell_coloring(G)
    # Không có xung đột -> Tất cả môn có thể thi cùng 1 ca
    assert res["total_colors"] == 1
    assert len(res["shifts"][1]) == 4
    assert res["is_valid"] is True
    assert res["conflicts_count"] == 0
    print("✓ Test 2: Đồ thị không cạnh gom toàn bộ vào đúng 1 ca thi duy nhất.")


def test_complete_graph():
    """Test 3: Đồ thị đầy đủ K_5 (Mọi cặp môn đều có sinh viên thi chung)."""
    G = nx.complete_graph(5)
    mapping = {i: f"M{i+1}" for i in range(5)}
    G = nx.relabel_nodes(G, mapping)
    for node in G.nodes():
        G.nodes[node]["size"] = 25

    res = welsh_powell_coloring(G)
    # Đồ thị đầy đủ K_5 bắt buộc cần 5 ca thi
    assert res["total_colors"] == 5
    assert len(set(res["color_map"].values())) == 5
    assert res["is_valid"] is True
    assert res["conflicts_count"] == 0
    print("✓ Test 3: Đồ thị đầy đủ K_5 xếp chính xác vào 5 ca thi riêng biệt.")


def test_odd_cycle_graph():
    """Test 4: Chu trình lẻ C_5 (Sắc số lý thuyết chi(C_5) = 3)."""
    G = nx.cycle_graph(5)
    mapping = {i: f"SUBJ_{i}" for i in range(5)}
    G = nx.relabel_nodes(G, mapping)

    res = welsh_powell_coloring(G)
    # Chu trình lẻ có sắc số là 3
    assert res["total_colors"] == 3
    assert res["is_valid"] is True
    assert res["conflicts_count"] == 0
    # Đảm bảo không có 2 đỉnh kề nào trùng màu
    for u, v in G.edges():
        assert res["color_map"][u] != res["color_map"][v]
    print("✓ Test 4: Chu trình lẻ C_5 đạt đúng sắc số lý thuyết (3 ca thi) và 0% xung đột.")


def test_bipartite_graph():
    """Test 5: Đồ thị phân đôi (Bipartite Graph K_3,3 - Sắc số lý thuyết chi = 2)."""
    G = nx.complete_bipartite_graph(3, 3)
    res = welsh_powell_coloring(G)
    assert res["total_colors"] == 2
    assert res["is_valid"] is True
    assert res["conflicts_count"] == 0
    print("✓ Test 5: Đồ thị phân đôi K_3,3 xếp vào đúng 2 ca thi.")


def test_realistic_exam_conflict_graph():
    """Test 6: Đồ thị xung đột 10 môn học giả lập trường đại học."""
    # Danh sách đăng ký thi mẫu
    registrations = [
        {"ma_sinh_vien": "SV001", "ma_mon_hoc": "CS101"},
        {"ma_sinh_vien": "SV001", "ma_mon_hoc": "MA101"},
        {"ma_sinh_vien": "SV002", "ma_mon_hoc": "CS101"},
        {"ma_sinh_vien": "SV002", "ma_mon_hoc": "PH101"},
        {"ma_sinh_vien": "SV003", "ma_mon_hoc": "MA101"},
        {"ma_sinh_vien": "SV003", "ma_mon_hoc": "CS102"},
        {"ma_sinh_vien": "SV004", "ma_mon_hoc": "PH101"},
        {"ma_sinh_vien": "SV004", "ma_mon_hoc": "CS103"},
        {"ma_sinh_vien": "SV005", "ma_mon_hoc": "CS102"},
        {"ma_sinh_vien": "SV005", "ma_mon_hoc": "CS103"},
        {"ma_sinh_vien": "SV006", "ma_mon_hoc": "CS104"},
        {"ma_sinh_vien": "SV006", "ma_mon_hoc": "MA102"},
        {"ma_sinh_vien": "SV007", "ma_mon_hoc": "MA102"},
        {"ma_sinh_vien": "SV007", "ma_mon_hoc": "PH102"},
        {"ma_sinh_vien": "SV008", "ma_mon_hoc": "EN101"},
        {"ma_sinh_vien": "SV008", "ma_mon_hoc": "EN102"},
        {"ma_sinh_vien": "SV009", "ma_mon_hoc": "CS101"},
        {"ma_sinh_vien": "SV009", "ma_mon_hoc": "EN101"},
        {"ma_sinh_vien": "SV010", "ma_mon_hoc": "MA101"},
        {"ma_sinh_vien": "SV010", "ma_mon_hoc": "EN102"},
    ]

    G = build_conflict_graph(registrations)
    res_wp = welsh_powell_coloring(G)

    assert res_wp["is_valid"] is True
    assert res_wp["conflicts_count"] == 0
    assert len(res_wp["conflict_pairs"]) == 0
    assert res_wp["total_colors"] > 0
    assert len(res_wp["color_map"]) == 10

    # Kiểm tra phân tích tải trọng qua get_schedule_summary
    summary = get_schedule_summary(G, res_wp["color_map"])
    assert summary["total_courses"] == 10
    assert summary["total_shifts"] == res_wp["total_colors"]
    assert summary["total_students"] == 20

    print(f"✓ Test 6: Đồ thị 10 môn thực tế được Welsh-Powell xếp thành công ({res_wp['total_colors']} ca, 0% xung đột).")


def test_algorithm_comparison_benchmark():
    """Test 7: Đối chứng benchmark toàn diện DSatur vs Welsh-Powell."""
    # Tạo đồ thị Crown Graph S_4^0: 2 tập đỉnh U0..U3 và V0..V3.
    # Cạnh nối u_i với v_j (i != j). Bậc mỗi đỉnh bằng 3, sắc số lý thuyết = 2.
    G = nx.Graph()
    # Tập U và V
    n = 4
    for i in range(n):
        G.add_node(f"U{i}", size=20)
        G.add_node(f"V{i}", size=20)

    for i in range(n):
        for j in range(n):
            if i != j:
                G.add_edge(f"U{i}", f"V{j}", weight=2)

    # Chạy hàm so sánh
    comparison = compare_coloring_algorithms(G)

    assert "dsatur" in comparison
    assert "welsh_powell" in comparison
    assert "comparison" in comparison

    cmp_stats = comparison["comparison"]
    assert cmp_stats["both_valid"] is True
    assert cmp_stats["winner"] in ["DSATUR", "WELSH_POWELL", "TIE"]
    assert cmp_stats["dsatur_time_ms"] >= 0
    assert cmp_stats["welsh_powell_time_ms"] >= 0

    print(f"✓ Test 7: Đối chứng Benchmark thành công:")
    print(f"  - DSatur:       {cmp_stats['dsatur_colors']} ca thi ({cmp_stats['dsatur_time_ms']} ms)")
    print(f"  - Welsh-Powell: {cmp_stats['welsh_powell_colors']} ca thi ({cmp_stats['welsh_powell_time_ms']} ms)")
    print(f"  - Kết luận:     Winner={cmp_stats['winner']}, Độ lệch={cmp_stats['color_difference']} ca thi")


def test_edge_cases_digraph_mixed_nodes_and_empty_compare():
    """Test 8: Edge cases — đồ thị có hướng, đỉnh hỗn hợp int/str và benchmark rỗng."""
    # 8.1 Benchmark với None & đồ thị rỗng: 2 kết quả phải là 2 dict độc lập
    cmp_none = compare_coloring_algorithms(None)
    assert cmp_none["comparison"]["winner"] == "TIE"
    assert cmp_none["comparison"]["both_valid"] is True
    assert cmp_none["dsatur"] is not cmp_none["welsh_powell"]
    cmp_none["dsatur"]["total_colors"] = 99
    assert cmp_none["welsh_powell"]["total_colors"] == 0

    cmp_empty = compare_coloring_algorithms(nx.Graph())
    assert cmp_empty["dsatur"] is not cmp_empty["welsh_powell"]

    # 8.2 Đồ thị có hướng (DiGraph) phải tự chuyển sang vô hướng để tránh tô trùng màu
    digraph = nx.DiGraph([("CS101", "MA101")])
    res_wp_di = welsh_powell_coloring(digraph)
    res_ds_di = dsatur_coloring(digraph)
    assert res_wp_di["is_valid"] is True and res_wp_di["total_colors"] == 2
    assert res_ds_di["is_valid"] is True and res_ds_di["total_colors"] == 2

    # 8.3 Đồ thị có đỉnh hỗn hợp int và str không gây TypeError khi sắp xếp
    mixed = nx.Graph()
    mixed.add_node(101, size=20)
    mixed.add_node("CS102", size=30)
    res_mixed = welsh_powell_coloring(mixed)
    assert res_mixed["is_valid"] is True
    assert res_mixed["total_colors"] == 1
    summary_mixed = get_schedule_summary(mixed, res_mixed["color_map"])
    assert summary_mixed["total_students"] == 50

    print("✓ Test 8: Edge cases (DiGraph, mixed int/str nodes, isolated empty benchmark) đạt 100%.")


if __name__ == "__main__":
    print("=== BẮT ĐẦU KIỂM THỬ THUẬT TOÁN WELSH-POWELL & BENCHMARK (NGÀY 3 - TV1) ===")
    test_empty_and_single_node()
    test_independent_graph()
    test_complete_graph()
    test_odd_cycle_graph()
    test_bipartite_graph()
    test_realistic_exam_conflict_graph()
    test_algorithm_comparison_benchmark()
    test_edge_cases_digraph_mixed_nodes_and_empty_compare()
    print("==========================================================================")
    print("ALL WELSH-POWELL & BENCHMARK TESTS PASSED 100%!")
