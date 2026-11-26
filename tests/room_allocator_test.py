"""Unit tests for First-Fit Decreasing (FFD) Room Allocator module (UC08.3)."""

import sys
from pathlib import Path
import networkx as nx

# Thêm thư mục gốc vào PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.algorithms.graph_builder import build_conflict_graph
from backend.algorithms.coloring import dsatur_coloring, welsh_powell_coloring
from backend.algorithms.room_allocator import (
    allocate_shift_rooms_ffd,
    allocate_exam_rooms_ffd,
    allocate_graph_schedule_rooms_ffd,
)


def test_empty_input():
    """Kiểm tra xử lý danh sách rỗng an toàn."""
    res1 = allocate_shift_rooms_ffd([], [])
    assert res1["is_fully_allocated"] is True
    assert res1["allocations"] == []
    assert res1["free_rooms"] == []

    rooms = [{"ma_phong": "P101", "suc_chua": 50}]
    res2 = allocate_shift_rooms_ffd([], rooms)
    assert res2["is_fully_allocated"] is True
    assert res2["free_rooms"] == ["P101"]
    assert res2["used_rooms"] == []


def test_exact_fit():
    """Kiểm tra môn vừa khít sức chứa phòng (Tỷ lệ lấp đầy 100%)."""
    courses = [{"ma_mon": "CS101", "size": 60, "ten_mon": "Lập trình C"}]
    rooms = [{"ma_phong": "P101", "suc_chua": 60, "ten_phong": "Phòng 101"}]

    res = allocate_shift_rooms_ffd(courses, rooms)
    assert res["is_fully_allocated"] is True
    assert len(res["allocations"]) == 1
    alloc = res["allocations"][0]
    assert alloc["ma_mon"] == "CS101"
    assert alloc["ma_phong"] == "P101"
    assert alloc["ti_le_lap_day"] == 1.0
    assert res["avg_utilization"] == 1.0
    assert res["used_rooms"] == ["P101"]
    assert res["free_rooms"] == []


def test_strict_ffd_ordering():
    """Kiểm tra nguyên lý FFD: Sắp xếp giảm dần cả môn và phòng trước khi ghép.

    Dù danh sách truyền vào bị xáo trộn thứ tự:
    - Môn: C3 (30 SV), C1 (80 SV), C2 (50 SV)
    - Phòng: R2 (60 chỗ), R3 (40 chỗ), R1 (100 chỗ)
    Kỳ vọng:
    - C1 (80) -> R1 (100) (tỷ lệ 80%)
    - C2 (50) -> R2 (60)  (tỷ lệ 83.33%)
    - C3 (30) -> R3 (40)  (tỷ lệ 75%)
    """
    courses = [
        {"ma_mon": "C3", "size": 30},
        {"ma_mon": "C1", "size": 80},
        {"ma_mon": "C2", "size": 50},
    ]
    rooms = [
        {"ma_phong": "R2", "suc_chua": 60},
        {"ma_phong": "R3", "suc_chua": 40},
        {"ma_phong": "R1", "suc_chua": 100},
    ]

    res = allocate_shift_rooms_ffd(courses, rooms)
    assert res["is_fully_allocated"] is True
    assert len(res["allocations"]) == 3

    mapping = {a["ma_mon"]: a["ma_phong"] for a in res["allocations"]}
    assert mapping["C1"] == "R1"
    assert mapping["C2"] == "R2"
    assert mapping["C3"] == "R3"

    assert res["used_rooms"] == ["R1", "R2", "R3"]
    assert res["free_rooms"] == []


def test_capacity_constraint_and_no_double_booking():
    """Kiểm tra ràng buộc cứng: Không môn nào vượt sức chứa và không trùng phòng trong cùng ca."""
    courses = [
        {"ma_mon": "M1", "size": 45},
        {"ma_mon": "M2", "size": 35},
        {"ma_mon": "M3", "size": 25},
    ]
    rooms = [
        {"ma_phong": "P1", "suc_chua": 50},
        {"ma_phong": "P2", "suc_chua": 50},
        {"ma_phong": "P3", "suc_chua": 30},
        {"ma_phong": "P4", "suc_chua": 20},
    ]

    res = allocate_shift_rooms_ffd(courses, rooms)
    assert res["is_fully_allocated"] is True

    # 1. Kiểm tra từng phòng gán phải đủ sức chứa
    for alloc in res["allocations"]:
        assert alloc["so_sinh_vien"] <= alloc["suc_chua"], (
            f"Vi phạm sức chứa: Môn {alloc['ma_mon']} ({alloc['so_sinh_vien']} SV) "
            f"vượt phòng {alloc['ma_phong']} ({alloc['suc_chua']} chỗ)"
        )

    # 2. Không phòng nào bị gán 2 lần trong cùng 1 ca
    used = res["used_rooms"]
    assert len(used) == len(set(used)), "Trùng phòng trong cùng một ca thi!"
    assert "P4" in res["free_rooms"]


def test_room_reusable_across_different_shifts():
    """Kiểm tra phòng thi được giải phóng và tái sử dụng qua các ca thi khác nhau."""
    shifts = {
        1: ["MON_A", "MON_B"],
        2: ["MON_C", "MON_D"],
    }
    course_sizes = {"MON_A": 40, "MON_B": 30, "MON_C": 45, "MON_D": 35}
    rooms = [
        {"ma_phong": "HALL_1", "suc_chua": 50},
        {"ma_phong": "HALL_2", "suc_chua": 40},
    ]

    exam_res = allocate_exam_rooms_ffd(shifts, course_sizes, rooms)
    assert exam_res["is_all_successful"] is True
    assert exam_res["total_shifts"] == 2
    assert exam_res["total_allocations_count"] == 4

    # HALL_1 và HALL_2 đều được dùng ở ca 1 và được tái sử dụng ở ca 2
    shift1 = exam_res["shifts_allocation"][1]
    shift2 = exam_res["shifts_allocation"][2]
    assert set(shift1["used_rooms"]) == {"HALL_1", "HALL_2"}
    assert set(shift2["used_rooms"]) == {"HALL_1", "HALL_2"}


def test_overflow_detection():
    """Kiểm tra phát hiện môn vượt sức chứa (chuẩn bị cho Room Splitting Ngày 5)."""
    courses = [
        {"ma_mon": "MON_GIANG_DUONG_LON", "size": 150},  # Vượt quá mọi phòng
        {"ma_mon": "MON_VUA", "size": 40},
    ]
    rooms = [
        {"ma_phong": "P1", "suc_chua": 80},
        {"ma_phong": "P2", "suc_chua": 50},
    ]

    res = allocate_shift_rooms_ffd(courses, rooms)
    assert res["is_fully_allocated"] is False
    assert len(res["allocations"]) == 1
    assert res["allocations"][0]["ma_mon"] == "MON_VUA"

    assert len(res["unallocated_courses"]) == 1
    unalloc = res["unallocated_courses"][0]
    assert unalloc["ma_mon"] == "MON_GIANG_DUONG_LON"
    assert unalloc["so_sinh_vien"] == 150
    assert "vượt sức chứa" in unalloc["reason"]


def test_end_to_end_dsatur_and_welsh_powell_integration():
    """Kiểm thử tích hợp luồng hoàn chỉnh:

    Đăng ký thi -> Dựng đồ thị G -> Tô màu (DSatur & Welsh-Powell) -> Phân phòng FFD.
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

    registrations = [
        ("SV01", "CS101"), ("SV01", "MA101"), ("SV01", "PH101"),
        ("SV02", "CS101"), ("SV02", "MA101"), ("SV02", "EN101"),
        ("SV03", "CS102"), ("SV03", "CS103"), ("SV03", "MA102"),
        ("SV04", "CS102"), ("SV04", "CS104"),
        ("SV05", "PH101"), ("SV05", "PH102"), ("SV05", "MA102"),
        ("SV06", "EN101"), ("SV06", "EN102"),
        ("SV07", "CS101"), ("SV07", "CS102"),
        ("SV08", "MA101"), ("SV08", "MA102"),
    ]

    # Danh mục phòng của trường
    university_rooms = [
        {"ma_phong": "HALL_A", "ten_phong": "Hội trường A", "suc_chua": 100},
        {"ma_phong": "HALL_B", "ten_phong": "Hội trường B", "suc_chua": 80},
        {"ma_phong": "LAB_1", "ten_phong": "Phòng máy 1", "suc_chua": 50},
        {"ma_phong": "LAB_2", "ten_phong": "Phòng máy 2", "suc_chua": 40},
        {"ma_phong": "P201", "ten_phong": "Phòng học 201", "suc_chua": 30},
        {"ma_phong": "P202", "ten_phong": "Phòng học 202", "suc_chua": 30},
    ]

    # 1. Dựng đồ thị
    G = build_conflict_graph(registrations, courses=courses)
    assert G.number_of_nodes() == 10

    # 2. Tô màu DSatur
    dsatur_res = dsatur_coloring(G)
    assert dsatur_res["is_valid"] is True

    # 3. Phân phòng FFD theo kết quả DSatur
    ffd_res = allocate_graph_schedule_rooms_ffd(
        G=G,
        color_map=dsatur_res["color_map"],
        rooms=university_rooms,
    )

    assert ffd_res["is_all_successful"] is True
    assert ffd_res["total_courses"] == 10
    assert ffd_res["total_allocations_count"] == 10
    assert ffd_res["total_unallocated_count"] == 0
    assert ffd_res["overall_avg_utilization"] > 0.0

    print("\n✓ Phân phòng FFD thành công cho toàn bộ kỳ thi (DSatur):")
    print(f"  - Tổng số ca thi: {ffd_res['total_shifts']}")
    print(f"  - Tỷ lệ lấp đầy phòng trung bình: {ffd_res['overall_avg_utilization'] * 100:.2f}%")
    for shift_id, s_data in ffd_res["shifts_allocation"].items():
        print(f"  * Ca thi {shift_id}:")
        for alloc in s_data["allocations"]:
            pct = alloc["ti_le_lap_day"] * 100
            print(f"    + Môn {alloc['ma_mon']} ({alloc['so_sinh_vien']} SV) -> Phòng {alloc['ma_phong']} ({alloc['suc_chua']} chỗ) [{pct:.1f}%]")

    # 4. Kiểm tra tương thích cả với kết quả Welsh-Powell
    wp_res = welsh_powell_coloring(G)
    wp_ffd = allocate_graph_schedule_rooms_ffd(G, wp_res["color_map"], university_rooms)
    assert wp_ffd["is_all_successful"] is True
    assert wp_ffd["total_allocations_count"] == 10


def test_out_of_rooms_reason():
    """Kiểm tra phân loại đúng lý do khi hết sạch phòng trống trong ca (không phải vượt sức chứa)."""
    courses = [
        {"ma_mon": "M1", "size": 30},
        {"ma_mon": "M2", "size": 20},
        {"ma_mon": "M3", "size": 10},
    ]
    rooms = [
        {"ma_phong": "P1", "suc_chua": 50},
        {"ma_phong": "P2", "suc_chua": 40},
    ]
    res = allocate_shift_rooms_ffd(courses, rooms)
    assert res["is_fully_allocated"] is False
    assert len(res["allocations"]) == 2
    assert len(res["unallocated_courses"]) == 1
    unalloc = res["unallocated_courses"][0]
    assert unalloc["ma_mon"] == "M3"
    assert "hết toàn bộ phòng" in unalloc["reason"]


def test_inactive_duplicate_and_invalid_rooms():
    """Kiểm tra lọc phòng đang khóa (dang_su_dung=False), phòng sức chứa <= 0 và khử trùng ma_phong."""
    courses = [
        {"ma_mon": "M1", "size": 30},
        {"ma_mon": "M2", "size": 20},
    ]
    rooms = [
        {"ma_phong": "P101", "suc_chua": 50, "dang_su_dung": True},
        {"ma_phong": "P101", "suc_chua": 50, "dang_su_dung": True},  # Trùng mã phòng
        {"ma_phong": "P102", "suc_chua": 60, "dang_su_dung": False},  # Đang bảo trì
        {"ma_phong": "P103", "suc_chua": 0},  # Sức chứa = 0
        {"ma_phong": "P104", "suc_chua": None},  # Sức chứa None
        {"ma_phong": None, "suc_chua": 80},  # Mã phòng None
    ]

    # Chỉ có duy nhất 1 phòng hợp lệ (P101)
    res_empty = allocate_shift_rooms_ffd([], rooms)
    assert res_empty["free_rooms"] == ["P101"]

    res = allocate_shift_rooms_ffd(courses, rooms)
    assert res["is_fully_allocated"] is False
    assert res["used_rooms"] == ["P101"]
    assert len(res["allocations"]) == 1
    assert res["allocations"][0]["ma_mon"] == "M1"
    assert len(res["unallocated_courses"]) == 1
    assert res["unallocated_courses"][0]["ma_mon"] == "M2"


def test_dirty_course_and_graph_inputs():
    """Kiểm tra chống crash khi đầu vào chứa None, size âm, chuỗi số hoặc đồ thị rỗng/None."""
    courses = [
        {"ma_mon": None, "size": 20},
        {"ma_mon": "M_NONE_SIZE", "size": None, "ten_mon": None},
        {"ma_mon": "M_NEG_SIZE", "size": -15},
        {"ma_mon": "M_STR_SIZE", "size": "25"},
    ]
    rooms = [
        {"ma_phong": "P1", "suc_chua": 50},
        {"ma_phong": "P2", "suc_chua": 40},
        {"ma_phong": "P3", "suc_chua": 30},
    ]

    res = allocate_shift_rooms_ffd(courses, rooms)
    assert res["is_fully_allocated"] is True
    assert len(res["allocations"]) == 3
    alloc_by_code = {a["ma_mon"]: a for a in res["allocations"]}
    assert alloc_by_code["M_STR_SIZE"]["so_sinh_vien"] == 25
    assert alloc_by_code["M_NONE_SIZE"]["so_sinh_vien"] == 0
    assert alloc_by_code["M_NONE_SIZE"]["ten_mon"] == ""
    assert alloc_by_code["M_NEG_SIZE"]["so_sinh_vien"] == 0
    assert all(a["ti_le_lap_day"] >= 0.0 for a in res["allocations"])

    # rooms=None không gây crash
    res_no_rooms = allocate_shift_rooms_ffd([], None)
    assert res_no_rooms["free_rooms"] == []

    # allocate_graph_schedule_rooms_ffd với G=None và size=None
    res_none_graph = allocate_graph_schedule_rooms_ffd(None, {}, rooms)
    assert res_none_graph["is_all_successful"] is True
    assert res_none_graph["total_shifts"] == 0

    G_dirty = nx.Graph()
    G_dirty.add_node("CS101", size=None, ten_mon=None)
    res_dirty_graph = allocate_graph_schedule_rooms_ffd(G_dirty, {"CS101": 1}, rooms)
    assert res_dirty_graph["is_all_successful"] is True
    assert res_dirty_graph["total_allocations_count"] == 1


if __name__ == "__main__":
    test_empty_input()
    test_exact_fit()
    test_strict_ffd_ordering()
    test_capacity_constraint_and_no_double_booking()
    test_room_reusable_across_different_shifts()
    test_overflow_detection()
    test_end_to_end_dsatur_and_welsh_powell_integration()
    test_out_of_rooms_reason()
    test_inactive_duplicate_and_invalid_rooms()
    test_dirty_course_and_graph_inputs()
    print("\nALL ROOM ALLOCATOR FFD TESTS PASSED 100%!")
