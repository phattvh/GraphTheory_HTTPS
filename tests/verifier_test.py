"""Unit tests for Schedule Verifier module (UC08.4 - Ngày 6)."""

import sys
from pathlib import Path
import networkx as nx

# Thêm thư mục gốc vào PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.algorithms.graph_builder import build_conflict_graph
from backend.algorithms.coloring import dsatur_coloring, welsh_powell_coloring
from backend.algorithms.room_allocator import allocate_graph_schedule_with_overflow
from backend.algorithms.verifier import (
    verify_zero_conflicts,
    verify_room_capacities,
    verify_student_completeness,
    verify_schedule,
)


def test_valid_full_pipeline_schedule():
    """Test 1: Lịch hợp lệ từ pipeline chuẩn (Graph -> DSatur -> FFD/Overflow -> Verifier)."""
    registrations = [
        ("SV01", "CS101"), ("SV01", "MA101"), ("SV01", "PH101"),
        ("SV02", "CS101"), ("SV02", "MA101"), ("SV02", "EN101"),
        ("SV03", "CS102"), ("SV03", "CS103"), ("SV03", "MA102"),
        ("SV04", "CS102"), ("SV04", "CS104"),
        ("SV05", "PH101"), ("SV05", "EN101"),
    ]
    rooms = [
        {"ma_phong": "P101", "suc_chua": 50, "dang_su_dung": True},
        {"ma_phong": "P102", "suc_chua": 40, "dang_su_dung": True},
        {"ma_phong": "P103", "suc_chua": 30, "dang_su_dung": True},
    ]

    G = build_conflict_graph(registrations)
    coloring = dsatur_coloring(G)
    alloc = allocate_graph_schedule_with_overflow(G, coloring["color_map"], rooms)

    report = verify_schedule(G, alloc, rooms=rooms)
    assert report["is_valid"] is True, f"Lịch hợp lệ bị báo lỗi: {report['errors']}"
    assert report["summary"]["zero_conflicts_passed"] is True
    assert report["summary"]["room_capacity_passed"] is True
    assert report["summary"]["student_completeness_passed"] is True
    assert report["summary"]["total_violations"] == 0
    assert report["summary"]["total_courses_expected"] == G.number_of_nodes()
    assert report["summary"]["total_courses_scheduled"] == G.number_of_nodes()
    assert report["summary"]["total_students_expected"] == len(registrations)
    assert report["summary"]["total_students_scheduled"] == len(registrations)
    assert report["errors"] == []


def test_valid_schedule_with_room_splitting():
    """Test 2: Lịch hợp lệ có Room Splitting (1 môn 110 SV chia thành 60 + 50 cùng ca)."""
    G = nx.Graph()
    G.add_node("CS101", size=110)
    G.add_node("MA101", size=40)
    G.add_edge("CS101", "MA101", weight=15)

    rooms = [
        {"ma_phong": "P101", "suc_chua": 60, "dang_su_dung": True},
        {"ma_phong": "P102", "suc_chua": 50, "dang_su_dung": True},
    ]

    coloring = dsatur_coloring(G)
    alloc = allocate_graph_schedule_with_overflow(G, coloring["color_map"], rooms)

    report = verify_schedule(G, alloc, rooms=rooms)
    assert report["is_valid"] is True
    assert report["summary"]["total_students_expected"] == 150
    assert report["summary"]["total_students_scheduled"] == 150
    assert report["errors"] == []


def test_detect_edge_conflict_same_shift():
    """Test 3: Ràng buộc 1 - Phát hiện 2 môn có cạnh xung đột bị xếp chung ca thi."""
    G = nx.Graph()
    G.add_node("CS101", size=30)
    G.add_node("MA101", size=25)
    G.add_edge("CS101", "MA101", weight=12)

    rooms = [
        {"ma_phong": "P101", "suc_chua": 50},
        {"ma_phong": "P102", "suc_chua": 50},
    ]
    # Cố tình gán cả CS101 và MA101 vào Ca 1
    bad_schedule = {
        "shifts_allocation": {
            1: {
                "allocations": [
                    {"ma_mon": "CS101", "ma_phong": "P101", "so_sinh_vien": 30, "suc_chua": 50},
                    {"ma_mon": "MA101", "ma_phong": "P102", "so_sinh_vien": 25, "suc_chua": 50},
                ]
            }
        }
    }

    report = verify_schedule(G, bad_schedule, rooms=rooms)
    assert report["is_valid"] is False
    assert report["summary"]["zero_conflicts_passed"] is False
    assert report["summary"]["room_capacity_passed"] is True
    assert report["summary"]["student_completeness_passed"] is True

    conflicts = report["checks"]["conflicts"]["edge_conflicts"]
    assert len(conflicts) == 1
    assert {conflicts[0]["u"], conflicts[0]["v"]} == {"CS101", "MA101"}
    assert conflicts[0]["shift"] == 1
    assert conflicts[0]["weight"] == 12


def test_detect_multi_shift_course_inconsistency():
    """Test 4: Ràng buộc 1 (biến thể) - Phát hiện 1 môn bị chia nằm ở 2 ca thi khác nhau."""
    G = nx.Graph()
    G.add_node("CS101", size=80)

    bad_schedule = {
        "shifts_allocation": {
            1: {"allocations": [{"ma_mon": "CS101", "ma_phong": "P1", "so_sinh_vien": 40, "suc_chua": 50}]},
            2: {"allocations": [{"ma_mon": "CS101", "ma_phong": "P1", "so_sinh_vien": 40, "suc_chua": 50}]},
        }
    }

    c1 = verify_zero_conflicts(G, shifts_allocation=bad_schedule["shifts_allocation"])
    assert c1["passed"] is False
    assert len(c1["multi_shift_courses"]) == 1
    assert c1["multi_shift_courses"][0]["ma_mon"] == "CS101"
    assert c1["multi_shift_courses"][0]["shifts"] == [1, 2]


def test_detect_room_capacity_overflow():
    """Test 5: Ràng buộc 2 - Phát hiện nhồi sinh viên vượt sức chứa phòng."""
    G = nx.Graph()
    G.add_node("CS101", size=65)
    rooms = [{"ma_phong": "P101", "suc_chua": 50, "dang_su_dung": True}]

    bad_schedule = {
        "shifts_allocation": {
            1: {
                "allocations": [
                    {"ma_mon": "CS101", "ma_phong": "P101", "so_sinh_vien": 65, "suc_chua": 50},
                ]
            }
        }
    }

    report = verify_schedule(G, bad_schedule, rooms=rooms)
    assert report["is_valid"] is False
    assert report["summary"]["room_capacity_passed"] is False
    violations = report["checks"]["capacity"]["capacity_violations"]
    assert len(violations) == 1
    assert violations[0]["ma_mon"] == "CS101"
    assert violations[0]["so_sinh_vien"] == 65
    assert violations[0]["suc_chua"] == 50


def test_detect_double_booked_and_inactive_rooms():
    """Test 6: Ràng buộc 2 (biến thể) - Phát hiện trùng phòng cùng ca và phòng đang khóa."""
    rooms = [
        {"ma_phong": "P101", "suc_chua": 50, "dang_su_dung": True},
        {"ma_phong": "P102", "suc_chua": 50, "dang_su_dung": False},  # Đang bảo trì
    ]
    bad_shifts = {
        1: {
            "allocations": [
                {"ma_mon": "M1", "ma_phong": "P101", "so_sinh_vien": 20, "suc_chua": 50},
                {"ma_mon": "M2", "ma_phong": "P101", "so_sinh_vien": 25, "suc_chua": 50},  # Trùng P101
                {"ma_mon": "M3", "ma_phong": "P102", "so_sinh_vien": 20, "suc_chua": 50},  # Phòng khóa
                {"ma_mon": "M4", "ma_phong": "P999", "so_sinh_vien": 15, "suc_chua": 50},  # Phòng lạ
            ]
        }
    }

    c2 = verify_room_capacities(bad_shifts, rooms=rooms)
    assert c2["passed"] is False
    assert len(c2["double_booked_rooms"]) == 1
    assert c2["double_booked_rooms"][0]["ma_phong"] == "P101"
    assert set(c2["double_booked_rooms"][0]["courses"]) == {"M1", "M2"}
    assert len(c2["invalid_rooms"]) == 2
    assert {r["ma_phong"] for r in c2["invalid_rooms"]} == {"P102", "P999"}


def test_detect_missing_unexpected_and_mismatched_students():
    """Test 7: Ràng buộc 3 - Phát hiện bỏ sót môn, thừa môn lạ, chia phòng thiếu/thừa SV."""
    G = nx.Graph()
    G.add_node("M1", size=100)  # Xếp thiếu còn 90 SV (50 + 40)
    G.add_node("M2", size=50)   # Bị bỏ sót hoàn toàn
    G.add_node("M3", size=30)   # Xếp thừa thành 35 SV

    bad_shifts = {
        1: {
            "allocations": [
                {"ma_mon": "M1", "ma_phong": "P1", "so_sinh_vien": 50, "suc_chua": 60},
                {"ma_mon": "M1", "ma_phong": "P2", "so_sinh_vien": 40, "suc_chua": 60},
                {"ma_mon": "M3", "ma_phong": "P3", "so_sinh_vien": 35, "suc_chua": 60},
                {"ma_mon": "GHOST", "ma_phong": "P4", "so_sinh_vien": 10, "suc_chua": 60},
            ]
        }
    }

    c3 = verify_student_completeness(G, bad_shifts)
    assert c3["passed"] is False
    assert c3["missing_courses"] == ["M2"]
    assert c3["unexpected_courses"] == ["GHOST"]
    mismatches = {m["ma_mon"]: m for m in c3["student_count_mismatches"]}
    assert set(mismatches.keys()) == {"M1", "M3"}
    assert mismatches["M1"]["diff"] == -10
    assert mismatches["M3"]["diff"] == +5


def test_empty_and_dirty_inputs():
    """Test 8: Xử lý an toàn đồ thị rỗng và dữ liệu bẩn (None, sĩ số âm)."""
    empty_report = verify_schedule(nx.Graph(), {})
    assert empty_report["is_valid"] is True
    assert empty_report["summary"]["total_violations"] == 0

    none_report = verify_schedule(None, None)
    assert none_report["is_valid"] is True

    # Sĩ số âm phải bị bắt lỗi ở Ràng buộc 2
    dirty_shifts = {
        1: {"allocations": [{"ma_mon": "M1", "ma_phong": "P1", "so_sinh_vien": -5, "suc_chua": 40}]}
    }
    c2 = verify_room_capacities(dirty_shifts)
    assert c2["passed"] is False
    assert len(c2["capacity_violations"]) == 1


def test_large_seed_scale_dataset_dsatur_and_welsh_powell():
    """Test 9: Kiểm chứng tải thực tế 15 môn, 100 SV, 10 phòng, 300 đăng ký (DSatur & Welsh-Powell)."""
    courses = [{"ma_mon": f"M{i:02d}", "ten_mon": f"Môn học {i:02d}"} for i in range(1, 16)]
    registrations = []
    # 100 sinh viên, mỗi SV đăng ký đúng 3 môn tạo thành 300 lượt đăng ký có xung đột đa tầng
    for sv_idx in range(1, 101):
        mssv = f"2211{sv_idx:04d}"
        c1 = f"M{((sv_idx - 1) % 15) + 1:02d}"
        c2 = f"M{((sv_idx + 2) % 15) + 1:02d}"
        c3 = f"M{((sv_idx + 6) % 15) + 1:02d}"
        registrations.extend([(mssv, c1), (mssv, c2), (mssv, c3)])

    rooms = [
        {"ma_phong": f"P{i:02d}", "suc_chua": cap, "dang_su_dung": True}
        for i, cap in enumerate([60, 50, 45, 40, 35, 30, 30, 25, 25, 20], start=1)
    ]

    G = build_conflict_graph(registrations, courses=courses)
    assert G.number_of_nodes() == 15

    for algo_name, algo_fn in [("DSatur", dsatur_coloring), ("Welsh-Powell", welsh_powell_coloring)]:
        coloring = algo_fn(G)
        alloc = allocate_graph_schedule_with_overflow(G, coloring["color_map"], rooms)
        report = verify_schedule(G, alloc, rooms=rooms)

        assert report["is_valid"] is True, f"{algo_name} thất bại Verifier: {report['errors']}"
        assert report["summary"]["total_violations"] == 0
        assert report["summary"]["total_courses_scheduled"] == 15
        assert report["summary"]["total_students_scheduled"] == 300
        print(
            f"✓ Verifier [{algo_name}]: is_valid=True, {alloc['total_shifts']} ca thi, "
            f"15/15 môn, 300/300 thí sinh, 0% xung đột."
        )


def test_verifier_edge_cases():
    """Test 10: Edge cases (empty-alloc fallback color_map, int/str shift IDs, DiGraph/self-loop, missing ma_mon)."""
    # 10.1 shifts_allocation có key nhưng không có allocation -> vẫn phải fallback kiểm tra color_map
    g_conflict = nx.Graph()
    g_conflict.add_edge("A", "B", weight=5)
    c1_fallback = verify_zero_conflicts(
        g_conflict,
        color_map={"A": "1", "B": 1},
        shifts_allocation={1: {"allocations": []}},
    )
    assert c1_fallback["passed"] is False
    assert len(c1_fallback["edge_conflicts"]) == 1
    assert c1_fallback["edge_conflicts"][0]["shift"] == 1

    # 10.2 DiGraph có 2 cạnh ngược chiều (A->B và B->A) + self-loop (A->A) -> chỉ đếm đúng 1 xung đột (A, B)
    di_g = nx.DiGraph()
    di_g.add_edge("A", "B", weight=3)
    di_g.add_edge("B", "A", weight=3)
    di_g.add_edge("A", "A", weight=1)
    c1_di = verify_zero_conflicts(di_g, color_map={"A": 1, "B": 1})
    assert c1_di["passed"] is False
    assert len(c1_di["edge_conflicts"]) == 1

    # 10.3 Bản ghi allocation thiếu ma_mon không được lọt qua Quality Gate
    g_single = nx.Graph()
    g_single.add_node("M1", size=20)
    rooms = [
        {"ma_phong": "P1", "suc_chua": 50, "dang_su_dung": True},
        {"ma_phong": "P2", "suc_chua": 50, "dang_su_dung": True},
    ]
    bad_blank_course = {
        "shifts_allocation": {
            1: {
                "allocations": [
                    {"ma_mon": "M1", "ma_phong": "P1", "so_sinh_vien": 20, "suc_chua": 50},
                    {"ma_mon": "", "ma_phong": "P2", "so_sinh_vien": 10, "suc_chua": 50},
                ]
            }
        }
    }
    report_blank = verify_schedule(g_single, bad_blank_course, rooms=rooms)
    assert report_blank["is_valid"] is False
    assert report_blank["summary"]["room_capacity_passed"] is False

    # 10.4 Thông báo lỗi xếp thừa sinh viên hiển thị rõ chênh lệch (+5)
    g_over = nx.Graph()
    g_over.add_node("M1", size=30)
    over_schedule = {
        "shifts_allocation": {
            1: {"allocations": [{"ma_mon": "M1", "ma_phong": "P1", "so_sinh_vien": 35, "suc_chua": 50}]}
        }
    }
    report_over = verify_schedule(g_over, over_schedule, rooms=rooms)
    assert report_over["is_valid"] is False
    assert any("+5" in err and "thực tế xếp 35 SV" in err for err in report_over["errors"])

    # 10.5 Trùng phòng giữa key int (1) và str ("1") của cùng ca thi phải bị bắt lỗi
    c2_mixed_keys = verify_room_capacities(
        {
            1: {"allocations": [{"ma_mon": "M1", "ma_phong": "P1", "so_sinh_vien": 20, "suc_chua": 50}]},
            "1": {"allocations": [{"ma_mon": "M2", "ma_phong": "P1", "so_sinh_vien": 20, "suc_chua": 50}]},
        },
        rooms=rooms,
    )
    assert c2_mixed_keys["passed"] is False
    assert len(c2_mixed_keys["double_booked_rooms"]) == 1
    assert c2_mixed_keys["double_booked_rooms"][0]["shift"] == 1

    # 10.6 Sĩ số kiểu số thực lẻ (30.7) không được bị cắt phần thập phân thành 30
    c2_float = verify_room_capacities(
        {1: {"allocations": [{"ma_mon": "M1", "ma_phong": "P1", "so_sinh_vien": 30.7, "suc_chua": 50}]}},
        rooms=rooms,
    )
    assert c2_float["passed"] is False
    assert len(c2_float["capacity_violations"]) == 1


if __name__ == "__main__":
    test_valid_full_pipeline_schedule()
    test_valid_schedule_with_room_splitting()
    test_detect_edge_conflict_same_shift()
    test_detect_multi_shift_course_inconsistency()
    test_detect_room_capacity_overflow()
    test_detect_double_booked_and_inactive_rooms()
    test_detect_missing_unexpected_and_mismatched_students()
    test_empty_and_dirty_inputs()
    test_large_seed_scale_dataset_dsatur_and_welsh_powell()
    test_verifier_edge_cases()
    print("\nALL SCHEDULE VERIFIER TESTS PASSED 100%!")
