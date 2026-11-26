"""Unit tests for Capacity Overflow Strategy: Room Splitting & Shift Spilling (UC08.3 - Ngày 5)."""

import sys
from pathlib import Path
import networkx as nx

# Thêm thư mục gốc vào PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.algorithms.coloring import dsatur_coloring
from backend.algorithms.room_allocator import (
    split_course_into_rooms,
    allocate_shift_rooms_with_overflow,
    allocate_exam_rooms_with_spilling,
    allocate_graph_schedule_with_overflow,
)


def test_basic_room_splitting():
    """Test 1: Chia phòng cơ bản (Môn 100 SV, phòng lớn nhất 60 chỗ -> chia vào 60 + 40 cùng ca)."""
    courses = [{"ma_mon": "CS101", "size": 100, "ten_mon": "Lập trình cơ bản"}]
    rooms = [
        {"ma_phong": "P101", "suc_chua": 60},
        {"ma_phong": "P102", "suc_chua": 50},
        {"ma_phong": "P103", "suc_chua": 30},
    ]

    res = allocate_shift_rooms_with_overflow(courses, rooms, allow_room_splitting=True)
    assert res["is_fully_allocated"] is True
    assert res["split_courses"] == ["CS101"]
    assert res["split_courses_count"] == 1
    assert len(res["allocations"]) == 2

    # Kiểm tra bảo toàn sĩ số: 60 + 40 = 100 SV
    part1, part2 = res["allocations"]
    assert part1["ma_mon"] == "CS101" and part1["ma_phong"] == "P101"
    assert part1["so_sinh_vien"] == 60 and part1["is_split"] is True
    assert part1["split_part"] == 1 and part1["split_total"] == 2

    assert part2["ma_mon"] == "CS101" and part2["ma_phong"] == "P102"
    assert part2["so_sinh_vien"] == 40 and part2["is_split"] is True
    assert part2["split_part"] == 2 and part2["split_total"] == 2

    assert res["total_students_allocated"] == 100
    assert res["free_rooms"] == ["P103"]


def test_room_splitting_conservation_and_no_partial_waste():
    """Test 2: Bảo toàn sĩ số qua 3 phòng con và không chiếm dụng dở dang khi tổng phòng không đủ."""
    # Trường hợp A: 150 SV chia vào 3 phòng [60, 50, 45] -> 60 + 50 + 40 = 150
    rooms_a = [
        {"ma_phong": "R1", "suc_chua": 60, "ten_phong": "R1"},
        {"ma_phong": "R2", "suc_chua": 50, "ten_phong": "R2"},
        {"ma_phong": "R3", "suc_chua": 45, "ten_phong": "R3"},
    ]
    allocs, rem_rooms, rem_sv = split_course_into_rooms(
        {"ma_mon": "MA101", "size": 150, "ten_mon": "Giải tích"}, rooms_a
    )
    assert rem_sv == 0
    assert rem_rooms == []
    assert len(allocs) == 3
    assert sum(a["so_sinh_vien"] for a in allocs) == 150
    assert [a["so_sinh_vien"] for a in allocs] == [60, 50, 40]

    # Trường hợp B: Môn 200 SV nhưng tổng sức chứa phòng chỉ là 110 (60 + 50)
    # -> Không được chiếm phòng dở dang, để dành phòng cho môn nhỏ hơn (40 SV)
    courses_b = [
        {"ma_mon": "BIG_200", "size": 200},
        {"ma_mon": "SMALL_40", "size": 40},
    ]
    rooms_b = [
        {"ma_phong": "R1", "suc_chua": 60},
        {"ma_phong": "R2", "suc_chua": 50},
    ]
    res_b = allocate_shift_rooms_with_overflow(courses_b, rooms_b, allow_room_splitting=True)
    assert res_b["is_fully_allocated"] is False
    assert len(res_b["allocations"]) == 1
    assert res_b["allocations"][0]["ma_mon"] == "SMALL_40"
    assert len(res_b["unallocated_courses"]) == 1
    assert res_b["unallocated_courses"][0]["ma_mon"] == "BIG_200"


def test_shift_spilling_when_out_of_rooms():
    """Test 3: Tách ca mới (Shift Spilling) khi ca thi có nhiều môn hơn số phòng khả dụng."""
    shifts = {1: ["M1", "M2", "M3"]}
    course_sizes = {"M1": 40, "M2": 35, "M3": 30}
    rooms = [
        {"ma_phong": "P1", "suc_chua": 50},
        {"ma_phong": "P2", "suc_chua": 40},
    ]

    res = allocate_exam_rooms_with_spilling(
        shifts=shifts,
        course_sizes=course_sizes,
        rooms=rooms,
        allow_room_splitting=True,
        allow_shift_spilling=True,
    )
    assert res["is_all_successful"] is True
    assert res["original_shifts_count"] == 1
    assert res["total_shifts"] == 2
    assert res["new_shifts_created"] == 1
    assert res["total_spilled_courses"] == 1
    assert res["total_unallocated_count"] == 0
    assert res["total_allocations_count"] == 3


def test_shift_spilling_selects_lowest_degree_vertex():
    """Test 4: Khi quá tải ca, thuật toán phải chọn đúng môn có bậc xung đột deg(v) thấp nhất để tách."""
    G = nx.Graph()
    # HIGH_DEG (deg=3), MID_DEG (deg=2), LOW_DEG (deg=0) cùng nằm trong Ca 1
    G.add_nodes_from(["HIGH_DEG", "MID_DEG", "LOW_DEG", "X1", "X2", "X3"])
    G.add_edges_from([
        ("HIGH_DEG", "X1"), ("HIGH_DEG", "X2"), ("HIGH_DEG", "X3"),
        ("MID_DEG", "X1"), ("MID_DEG", "X2"),
    ])

    shifts = {1: ["HIGH_DEG", "MID_DEG", "LOW_DEG"], 2: ["X1", "X2", "X3"]}
    course_sizes = {
        "HIGH_DEG": 30,
        "MID_DEG": 30,
        "LOW_DEG": 30,
        "X1": 25,
        "X2": 25,
        "X3": 25,
    }
    # Trường chỉ có 2 phòng -> cả Ca 1 và Ca 2 đều quá tải số phòng
    rooms = [
        {"ma_phong": "P1", "suc_chua": 40},
        {"ma_phong": "P2", "suc_chua": 40},
    ]

    res = allocate_exam_rooms_with_spilling(
        shifts=shifts,
        course_sizes=course_sizes,
        rooms=rooms,
        G=G,
    )
    assert res["is_all_successful"] is True
    assert res["is_conflict_free"] is True
    assert res["conflicts_count"] == 0

    # Sự kiện tách đầu tiên từ Ca 1 bắt buộc phải chọn LOW_DEG (bậc 0 < bậc 2 < bậc 3)
    first_spill_from_shift_1 = next(
        ev for ev in res["spilled_events"] if ev["from_shift"] == 1
    )
    assert first_spill_from_shift_1["ma_mon"] == "LOW_DEG"
    assert first_spill_from_shift_1["degree"] == 0


def test_shift_spilling_respects_graph_conflicts():
    """Test 5: Môn được tách tuyệt đối không được đưa vào ca sẵn có nếu tồn tại cạnh xung đột."""
    G = nx.Graph()
    G.add_nodes_from(["A", "B", "C", "D"])
    # A, B có bậc cao hơn C? Cho A nối D, B nối D, C nối D (tất cả bậc 1)
    # A(45 SV), B(40 SV), C(20 SV) -> C có sĩ số nhỏ nhất nên sẽ bị tách khỏi Ca 1
    G.add_edges_from([("A", "D"), ("B", "D"), ("C", "D")])

    shifts = {1: ["A", "B", "C"], 2: ["D"]}
    course_sizes = {"A": 45, "B": 40, "C": 20, "D": 30}
    rooms = [
        {"ma_phong": "P1", "suc_chua": 50},
        {"ma_phong": "P2", "suc_chua": 50},
    ]

    # Ca 2 còn trống 1 phòng P2, nhưng C xung đột với D -> bắt buộc mở Ca 3!
    res = allocate_exam_rooms_with_spilling(shifts, course_sizes, rooms, G=G)
    assert res["is_all_successful"] is True
    assert res["is_conflict_free"] is True
    assert res["conflicts_count"] == 0
    assert res["total_shifts"] == 3
    assert res["new_shifts_created"] == 1
    assert res["final_color_map"]["C"] == 3
    assert res["final_color_map"]["C"] != res["final_color_map"]["D"]


def test_shift_spilling_reuses_non_conflicting_existing_shift():
    """Test 6: Nếu ca hiện có khác không xung đột và còn đủ phòng -> tái sử dụng ca, không tạo ca thừa."""
    G = nx.Graph()
    G.add_nodes_from(["A", "B", "C", "D"])
    G.add_edges_from([("A", "D"), ("B", "D")])  # C KHÔNG xung đột với D

    shifts = {1: ["A", "B", "C"], 2: ["D"]}
    course_sizes = {"A": 45, "B": 40, "C": 20, "D": 30}
    rooms = [
        {"ma_phong": "P1", "suc_chua": 50},
        {"ma_phong": "P2", "suc_chua": 50},
    ]

    res = allocate_exam_rooms_with_spilling(shifts, course_sizes, rooms, G=G)
    assert res["is_all_successful"] is True
    assert res["is_conflict_free"] is True
    assert res["total_shifts"] == 2
    assert res["new_shifts_created"] == 0
    assert res["final_color_map"]["C"] == 2
    assert res["spilled_events"][0]["created_new_shift"] is False


def test_unsolvable_single_course_exceeds_school_capacity():
    """Test 7: Môn đơn lẻ vượt tổng sức chứa toàn trường -> dừng an toàn, không lặp vô hạn."""
    shifts = {1: ["MEGA_500", "NORMAL_30"]}
    course_sizes = {"MEGA_500": 500, "NORMAL_30": 30}
    rooms = [
        {"ma_phong": "P1", "suc_chua": 70},
        {"ma_phong": "P2", "suc_chua": 50},
    ]  # Tổng sức chứa toàn trường = 120 < 500

    res = allocate_exam_rooms_with_spilling(shifts, course_sizes, rooms)
    assert res["is_all_successful"] is False
    assert res["total_unallocated_count"] == 1
    # NORMAL_30 vẫn được xếp phòng bình thường
    all_allocated_courses = [
        a["ma_mon"]
        for s in res["shifts_allocation"].values()
        for a in s["allocations"]
    ]
    assert "NORMAL_30" in all_allocated_courses
    assert "MEGA_500" not in all_allocated_courses


def test_high_load_combined_splitting_and_spilling():
    """Test 8: Kịch bản kỳ thi tải cao kết hợp cả Room Splitting + Shift Spilling + DSatur."""
    G = nx.Graph()
    course_data = [
        ("CS101", "Lập trình cơ bản", 110),   # Cần chia phòng (vượt phòng lớn nhất 60)
        ("MA101", "Giải tích 1", 95),         # Cần chia phòng
        ("CS102", "Cấu trúc dữ liệu", 55),
        ("CS103", "Cơ sở dữ liệu", 50),
        ("PH101", "Vật lý đại cương", 45),
        ("EN101", "Tiếng Anh 1", 40),
        ("EN102", "Tiếng Anh 2", 35),
        ("MA102", "Đại số tuyến tính", 30),
    ]
    for ma, ten, size in course_data:
        G.add_node(ma, ma_mon=ma, ten_mon=ten, size=size)

    # Tạo mạng xung đột vừa phải để DSatur gom nhiều môn vào ít ca -> kích hoạt quá tải ca
    G.add_edges_from([
        ("CS101", "MA101"),
        ("CS101", "CS102"),
        ("CS102", "CS103"),
        ("MA101", "PH101"),
        ("EN101", "EN102"),
    ])

    # Tổng sức chứa toàn trường = 60 + 50 + 40 + 30 = 180 chỗ
    rooms = [
        {"ma_phong": "P101", "suc_chua": 60},
        {"ma_phong": "P102", "suc_chua": 50},
        {"ma_phong": "P103", "suc_chua": 40},
        {"ma_phong": "P104", "suc_chua": 30},
    ]

    dsatur_res = dsatur_coloring(G)
    assert dsatur_res["is_valid"] is True

    res = allocate_graph_schedule_with_overflow(
        G=G,
        color_map=dsatur_res["color_map"],
        rooms=rooms,
        allow_room_splitting=True,
        allow_shift_spilling=True,
    )

    assert res["is_all_successful"] is True
    assert res["is_conflict_free"] is True
    assert res["conflicts_count"] == 0
    assert res["total_unallocated_count"] == 0
    assert res["total_split_courses"] >= 2, "CS101 (110 SV) và MA101 (95 SV) phải được chia phòng"
    assert res["total_spilled_courses"] >= 1, "Ca quá tải phải kích hoạt tách ca"

    # Kiểm chứng bảo toàn 100% sĩ số thí sinh
    expected_total_students = sum(size for _, _, size in course_data)
    actual_total_students = sum(
        s["total_students_allocated"] for s in res["shifts_allocation"].values()
    )
    assert actual_total_students == expected_total_students

    # Kiểm chứng sức chứa từng phòng con không bao giờ bị vượt
    for shift_id, s_data in res["shifts_allocation"].items():
        used = s_data["used_rooms"]
        assert len(used) == len(set(used)), f"Ca {shift_id} bị trùng phòng!"
        for alloc in s_data["allocations"]:
            assert alloc["so_sinh_vien"] <= alloc["suc_chua"]

    print(
        f"\n✓ Kịch bản tải cao thành công: {res['original_shifts_count']} ca ban đầu -> "
        f"{res['total_shifts']} ca sau tách (chia phòng: {res['total_split_courses']} môn, "
        f"tách ca: {res['total_spilled_courses']} lượt, 0% xung đột, "
        f"bảo toàn {actual_total_students}/{expected_total_students} SV)."
    )
    for shift_id, s_data in res["shifts_allocation"].items():
        print(f"  * Ca thi {shift_id} ({s_data['total_students_allocated']} SV):")
        for a in s_data["allocations"]:
            tag = f" [Phần {a['split_part']}/{a['split_total']}]" if a["is_split"] else ""
            print(
                f"    + {a['ma_mon']}{tag}: {a['so_sinh_vien']} SV -> "
                f"{a['ma_phong']} ({a['suc_chua']} chỗ) [{a['ti_le_lap_day'] * 100:.1f}%]"
            )


def test_no_useless_spill_for_impossible_courses_and_mixed_shift_keys():
    """Không tách ca vô ích cho môn vượt sức chứa đơn khi tắt chia phòng hoặc khi chỉ có môn quá tải; hỗ trợ shift_id lẫn kiểu."""
    rooms = [
        {"ma_phong": "P1", "suc_chua": 80},
        {"ma_phong": "P2", "suc_chua": 50},
    ]

    # 1. allow_room_splitting=False: môn 120 SV vượt phòng lớn nhất (80) không được tách ca vô ích
    res_no_split = allocate_exam_rooms_with_spilling(
        shifts={1: ["M_BIG", "M_OK"]},
        course_sizes={"M_BIG": 120, "M_OK": 40},
        rooms=rooms,
        allow_room_splitting=False,
        allow_shift_spilling=True,
    )
    assert res_no_split["new_shifts_created"] == 0
    assert res_no_split["total_spilled_courses"] == 0
    assert res_no_split["is_all_successful"] is False

    # 2. Môn 500 SV vượt tổng sức chứa toàn trường (130) ở chung ca với môn 30 SV -> không tách vô ích môn 30 SV
    res_monster = allocate_exam_rooms_with_spilling(
        shifts={1: ["M_MONSTER", "M_SMALL"]},
        course_sizes={"M_MONSTER": 500, "M_SMALL": 30},
        rooms=rooms,
        allow_room_splitting=True,
        allow_shift_spilling=True,
    )
    assert res_monster["new_shifts_created"] == 0
    assert res_monster["total_spilled_courses"] == 0

    # 3. shift_id lẫn kiểu (int và str) không gây TypeError và gộp cùng ca 1 mà không ghi đè mất môn
    res_mixed = allocate_exam_rooms_with_spilling(
        shifts={1: ["M1"], "1": ["M2"], "2": ["M3"]},
        course_sizes={"M1": 40, "M2": 30, "M3": 20},
        rooms=rooms,
    )
    assert res_mixed["is_all_successful"] is True
    assert res_mixed["total_courses"] == 3


if __name__ == "__main__":
    test_basic_room_splitting()
    test_room_splitting_conservation_and_no_partial_waste()
    test_shift_spilling_when_out_of_rooms()
    test_shift_spilling_selects_lowest_degree_vertex()
    test_shift_spilling_respects_graph_conflicts()
    test_shift_spilling_reuses_non_conflicting_existing_shift()
    test_unsolvable_single_course_exceeds_school_capacity()
    test_high_load_combined_splitting_and_spilling()
    test_no_useless_spill_for_impossible_courses_and_mixed_shift_keys()
    print("\nALL OVERFLOW ALLOCATOR (ROOM SPLITTING & SHIFT SPILLING) TESTS PASSED 100%!")
