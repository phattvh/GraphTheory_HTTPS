"""Unit tests for DSatur Graph Coloring module (UC08.2)."""

import sys
from pathlib import Path
import networkx as nx

# Thêm thư mục gốc vào PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.algorithms.graph_builder import build_conflict_graph
from backend.algorithms.coloring import dsatur_coloring, get_schedule_summary


def test_empty_graph():
    """Kiểm tra xử lý đồ thị rỗng."""
    G = nx.Graph()
    result = dsatur_coloring(G)
    assert result["total_colors"] == 0
    assert result["color_map"] == {}
    assert result["shifts"] == {}
    assert result["is_valid"] is True
    assert result["conflicts_count"] == 0

    summary = get_schedule_summary(G, result["color_map"])
    assert summary["total_courses"] == 0
    assert summary["total_shifts"] == 0


def test_independent_courses():
    """Kiểm tra 10 môn hoàn toàn độc lập (không có sinh viên thi trùng).

    Kỳ vọng: Toàn bộ 10 môn được xếp vào đúng 1 ca thi duy nhất (chi(G) = 1).
    """
    G = nx.Graph()
    for i in range(1, 11):
        G.add_node(f"MON_{i}", size=30)

    result = dsatur_coloring(G)
    assert result["total_colors"] == 1
    assert result["is_valid"] is True
    assert result["conflicts_count"] == 0
    assert len(result["shifts"][1]) == 10

    summary = get_schedule_summary(G, result["color_map"])
    assert summary["total_courses"] == 10
    assert summary["total_shifts"] == 1
    assert summary["shift_details"][1]["total_students"] == 300


def test_complete_graph_k5():
    """Kiểm tra đồ thị đầy đủ K_5 (5 môn mà bất kỳ 2 môn nào cũng có xung đột).

    Kỳ vọng: Bắt buộc phải có đúng 5 ca thi riêng biệt (chi(K_5) = 5).
    """
    G = nx.complete_graph(["M1", "M2", "M3", "M4", "M5"])
    result = dsatur_coloring(G)

    assert result["total_colors"] == 5
    assert result["is_valid"] is True
    assert result["conflicts_count"] == 0

    # Mỗi môn phải thuộc một ca thi khác nhau
    assigned_shifts = list(result["color_map"].values())
    assert len(set(assigned_shifts)) == 5


def test_odd_cycle_c5():
    """Kiểm tra đồ thị chu trình lẻ C_5 (vòng tròn 5 đỉnh).

    Lý thuyết đồ thị: Chu trình lẻ có sắc số chi(C_odd) = 3.
    """
    G = nx.cycle_graph(["C1", "C2", "C3", "C4", "C5"])
    result = dsatur_coloring(G)

    assert result["total_colors"] == 3
    assert result["is_valid"] is True
    assert result["conflicts_count"] == 0

    # Xác thực không có đỉnh kề nào trùng màu
    for u, v in G.edges():
        assert result["color_map"][u] != result["color_map"][v]


def test_realistic_10_course_exam_dataset():
    """Kiểm thử bài toán xếp lịch thi thực tế với 10 môn học và các xung đột đan xen (UC08.2).

    Danh mục 10 môn học:
    - CS101: Lập trình cơ bản, CS102: Cấu trúc dữ liệu, CS103: Cơ sở dữ liệu, CS104: Thuật toán
    - MA101: Giải tích 1, MA102: Đại số tuyến tính
    - PH101: Vật lý đại cương, PH102: Vật lý ứng dụng
    - EN101: Tiếng Anh 1, EN102: Tiếng Anh 2
    """
    courses = [
        {"ma_mon": "CS101", "ten_mon": "Lập trình cơ bản"},
        {"ma_mon": "CS102", "ten_mon": "Cấu trúc dữ liệu"},
        {"ma_mon": "CS103", "ten_mon": "Cơ sở dữ liệu"},
        {"ma_mon": "CS104", "ten_mon": "Phân tích thuật toán"},
        {"ma_mon": "MA101", "ten_mon": "Giải tích 1"},
        {"ma_mon": "MA102", "ten_mon": "Đại số tuyến tính"},
        {"ma_mon": "PH101", "ten_mon": "Vật lý đại cương"},
        {"ma_mon": "PH102", "ten_mon": "Vật lý ứng dụng"},
        {"ma_mon": "EN101", "ten_mon": "Tiếng Anh 1"},
        {"ma_mon": "EN102", "ten_mon": "Tiếng Anh 2"},
    ]

    # Danh sách sinh viên đăng ký môn học (tạo ra các xung đột thực tế)
    registrations = [
        # Nhóm SV K1 ngành CNTT: học CS101, MA101, PH101, EN101
        ("SV01", "CS101"), ("SV01", "MA101"), ("SV01", "PH101"), ("SV01", "EN101"),
        ("SV02", "CS101"), ("SV02", "MA101"), ("SV02", "PH101"), ("SV02", "EN101"),
        ("SV03", "CS101"), ("SV03", "MA101"), ("SV03", "PH101"),
        # Nhóm SV K2 ngành CNTT: học CS102, CS103, MA102
        ("SV04", "CS102"), ("SV04", "CS103"), ("SV04", "MA102"),
        ("SV05", "CS102"), ("SV05", "CS103"), ("SV05", "MA102"),
        ("SV06", "CS102"), ("SV06", "CS103"),
        # Nhóm SV Chuyên sâu Thuật toán & CSDL: CS102, CS103, CS104
        ("SV07", "CS102"), ("SV07", "CS104"),
        ("SV08", "CS103"), ("SV08", "CS104"),
        # Sinh viên học lại / cải thiện (Tạo xung đột chéo giữa K1 và K2):
        ("SV09", "CS101"), ("SV09", "CS102"),  # Học lại CS101 khi đang học CS102
        ("SV10", "MA101"), ("SV10", "MA102"),  # Học lại Giải tích khi học Đại số
        ("SV11", "PH101"), ("SV11", "PH102"),  # SV ngành Vật lý học cả 2 môn
        ("SV12", "PH102"), ("SV12", "MA102"),
        ("SV13", "EN101"), ("SV13", "EN102"),  # SV học cả 2 cấp độ tiếng Anh
    ]

    # 1. Dựng đồ thị xung đột
    G = build_conflict_graph(registrations, courses=courses)
    assert G.number_of_nodes() == 10
    assert G.number_of_edges() > 0

    # 2. Thực thi thuật toán DSatur
    result = dsatur_coloring(G)

    # 3. Kiểm chứng các chỉ số cốt lõi
    assert result["is_valid"] is True, "Phát hiện xung đột lịch thi giữa các môn có cạnh nối!"
    assert result["conflicts_count"] == 0, f"Số cạnh vi phạm: {result['conflicts_count']}"
    assert 2 <= result["total_colors"] <= 10, f"Số ca thi không hợp lý: {result['total_colors']}"

    # 4. Kiểm chứng tuyệt đối: Không có 2 môn kề nhau nào cùng ca thi
    for u, v in G.edges():
        shift_u = result["color_map"][u]
        shift_v = result["color_map"][v]
        assert shift_u != shift_v, (
            f"Xung đột nghiêm trọng: Môn {u} và Môn {v} cùng ca {shift_u} "
            f"nhưng có {G[u][v]['weight']} sinh viên thi chung!"
        )

    # 5. Kiểm tra hàm thống kê tải trọng
    summary = get_schedule_summary(G, result["color_map"])
    assert summary["total_courses"] == 10
    assert summary["total_shifts"] == result["total_colors"]
    assert summary["max_students_count"] > 0
    assert summary["avg_students_per_shift"] > 0

    print(f"✓ DSatur xếp 10 môn học vào {result['total_colors']} ca thi (0% xung đột).")
    for shift_id, course_list in result["shifts"].items():
        total_sv = summary["shift_details"][shift_id]["total_students"]
        print(f"  - Ca thi {shift_id}: {course_list} (Tổng: {total_sv} lượt thi)")


if __name__ == "__main__":
    test_empty_graph()
    test_independent_courses()
    test_complete_graph_k5()
    test_odd_cycle_c5()
    test_realistic_10_course_exam_dataset()
    print("\nALL DSATUR TESTS PASSED!")
