"""Module for First-Fit Decreasing (FFD) room allocation algorithm (UC08.3).

Mô hình hóa toán học:
Bài toán phân bổ phòng thi (Exam Room Allocation) được mô hình hóa thành
Bài toán đóng gói thùng (Bin Packing Problem):
- Thùng (Bins): Danh sách các phòng thi P, mỗi phòng có sức chứa tối đa cap(p).
- Vật phẩm (Items): Danh sách các môn thi trong cùng một ca thi M_c, mỗi môn
  có số lượng sinh viên dự thi size(m).
- Chiến lược First-Fit Decreasing (FFD):
  1. Sắp xếp các môn thi theo số lượng sinh viên giảm dần: size(m1) >= size(m2) >= ...
  2. Sắp xếp các phòng thi theo sức chứa giảm dần: cap(p1) >= cap(p2) >= ...
  3. Duyệt từng môn, gán vào phòng trống đầu tiên có cap(p) >= size(m).
"""

from typing import Any, Dict, List, Optional
import networkx as nx


def _safe_str(value: Any, default: str = "") -> str:
    """Chuẩn hóa chuỗi an toàn, tránh chuyển None thành 'None'."""
    if value is None:
        return default
    return str(value).strip()


def _safe_non_negative_int(value: Any, default: int = 0) -> int:
    """Ép kiểu số nguyên không âm an toàn, chống crash với None/bool/inf/chuỗi bẩn."""
    if value is None or isinstance(value, bool):
        return default
    try:
        parsed = int(value)
    except (ValueError, TypeError, OverflowError):
        return default
    return parsed if parsed >= 0 else 0


def _is_room_active(value: Any) -> bool:
    """Chuẩn hóa cờ dang_su_dung, từ chối False, 0, và chuỗi 'false'/'0'/'no'/'off'."""
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "off", ""}
    return bool(value)


def _normalize_course_item(course: Any, fallback_size: int = 0) -> Dict[str, Any]:
    """Chuẩn hóa dữ liệu môn học đầu vào."""
    if isinstance(course, dict):
        raw_ma = course.get("ma_mon")
        if raw_ma is None or str(raw_ma).strip() == "":
            raw_ma = course.get("ma_mon_hoc")
        ma_mon = _safe_str(raw_ma)

        raw_size = course.get("size")
        if raw_size is None:
            raw_size = course.get("so_sinh_vien")
        if raw_size is None:
            raw_size = course.get("so_luong", fallback_size)
        size = _safe_non_negative_int(raw_size, default=fallback_size)

        raw_ten = course.get("ten_mon")
        if raw_ten is None or str(raw_ten).strip() == "":
            raw_ten = course.get("ten_mon_hoc")
        ten_mon = _safe_str(raw_ten)
        return {"ma_mon": ma_mon, "size": size, "ten_mon": ten_mon}
    if isinstance(course, str):
        return {
            "ma_mon": course.strip(),
            "size": _safe_non_negative_int(fallback_size),
            "ten_mon": "",
        }
    if course is None:
        return {"ma_mon": "", "size": 0, "ten_mon": ""}
    return {
        "ma_mon": _safe_str(course),
        "size": _safe_non_negative_int(fallback_size),
        "ten_mon": "",
    }


def _normalize_room_item(room: Any) -> Optional[Dict[str, Any]]:
    """Chuẩn hóa dữ liệu phòng thi đầu vào; trả về None nếu phòng không hợp lệ/đang khóa."""
    if not isinstance(room, dict):
        return None
    if not _is_room_active(room.get("dang_su_dung", True)):
        return None

    ma_phong = _safe_str(room.get("ma_phong"))
    if not ma_phong:
        return None

    raw_cap = room.get("suc_chua")
    if raw_cap is None:
        raw_cap = room.get("capacity", 0)
    suc_chua = _safe_non_negative_int(raw_cap, default=0)
    if suc_chua <= 0:
        return None

    ten_phong = _safe_str(room.get("ten_phong"), default=ma_phong) or ma_phong
    return {"ma_phong": ma_phong, "suc_chua": suc_chua, "ten_phong": ten_phong}


def _prepare_valid_rooms(rooms: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Chuẩn hóa, lọc phòng khả dụng, khử trùng ma_phong và sắp xếp giảm dần theo sức chứa."""
    if not rooms:
        return []

    dedup_rooms: Dict[str, Dict[str, Any]] = {}
    for raw_room in rooms:
        norm = _normalize_room_item(raw_room)
        if norm is not None and norm["ma_phong"] not in dedup_rooms:
            dedup_rooms[norm["ma_phong"]] = norm

    return sorted(
        dedup_rooms.values(),
        key=lambda r: (r["suc_chua"], r["ma_phong"]),
        reverse=True,
    )


def allocate_shift_rooms_ffd(
    courses: Optional[List[Any]],
    rooms: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Phân bổ phòng thi cho một ca thi đơn lẻ bằng thuật toán First-Fit Decreasing (FFD).

    Args:
        courses: Danh sách các môn thi diễn ra trong ca. Mỗi phần tử có thể là
                 dict {'ma_mon': '...', 'size': ...} hoặc object tương đương.
        rooms: Danh sách toàn bộ các phòng thi khả dụng của trường.
               Mỗi phòng là dict {'ma_phong': '...', 'suc_chua': ...}.

    Returns:
        Dict chứa:
        - allocations: Danh sách các môn đã gán phòng thành công kèm tỷ lệ lấp đầy
        - unallocated_courses: Danh sách môn chưa xếp được phòng (do vượt sức chứa hoặc thiếu phòng)
        - used_rooms: Danh sách mã phòng đã sử dụng trong ca
        - free_rooms: Danh sách mã phòng còn trống trong ca
        - avg_utilization: Tỷ lệ lấp đầy phòng trung bình (tính trên các phòng được sử dụng)
        - is_fully_allocated: True nếu 100% môn trong ca đều được xếp phòng
        - total_students_allocated: Tổng số SV được xếp vào phòng thành công
        - total_students_unallocated: Tổng số SV của các môn chưa có phòng
    """
    # 1. Chuẩn hóa & sắp xếp phòng khả dụng (dùng chung cho cả nhánh rỗng lẫn chính)
    sorted_rooms = _prepare_valid_rooms(rooms)

    if not courses:
        return {
            "allocations": [],
            "unallocated_courses": [],
            "used_rooms": [],
            "free_rooms": [r["ma_phong"] for r in sorted_rooms],
            "avg_utilization": 0.0,
            "is_fully_allocated": True,
            "total_students_allocated": 0,
            "total_students_unallocated": 0,
        }

    # 2. Chuẩn hóa, khử trùng ma_mon trong cùng ca & sắp xếp giảm dần theo nguyên lý FFD
    dedup_courses: Dict[str, Dict[str, Any]] = {}
    for raw_course in courses:
        norm = _normalize_course_item(raw_course)
        if norm["ma_mon"] and norm["ma_mon"] not in dedup_courses:
            dedup_courses[norm["ma_mon"]] = norm

    sorted_courses = sorted(
        dedup_courses.values(),
        key=lambda c: (c["size"], c["ma_mon"]),
        reverse=True,
    )

    # 3. Tiến hành duyệt First-Fit gán môn vào phòng trống đầu tiên vừa sức chứa
    available_rooms = list(sorted_rooms)
    allocations: List[Dict[str, Any]] = []
    unallocated_courses: List[Dict[str, Any]] = []
    used_rooms: List[str] = []

    for course in sorted_courses:
        course_size = course["size"]
        found_room_idx = -1

        # Tìm phòng trống đầu tiên có suc_chua >= course_size
        for idx, room in enumerate(available_rooms):
            if room["suc_chua"] >= course_size:
                found_room_idx = idx
                break

        if found_room_idx != -1:
            assigned_room = available_rooms.pop(found_room_idx)
            used_rooms.append(assigned_room["ma_phong"])
            cap = assigned_room["suc_chua"]
            utilization = round(course_size / cap, 4) if cap > 0 else 1.0

            allocations.append({
                "ma_mon": course["ma_mon"],
                "ten_mon": course["ten_mon"],
                "so_sinh_vien": course_size,
                "ma_phong": assigned_room["ma_phong"],
                "ten_phong": assigned_room["ten_phong"],
                "suc_chua": cap,
                "ti_le_lap_day": utilization,
            })
        else:
            # Phân loại chính xác lý do không xếp được phòng
            reason = (
                "Đã sử dụng hết toàn bộ phòng thi trong ca"
                if not available_rooms
                else "Sĩ số môn thi vượt sức chứa của mọi phòng trống khả dụng"
            )
            unallocated_courses.append({
                "ma_mon": course["ma_mon"],
                "ten_mon": course["ten_mon"],
                "so_sinh_vien": course_size,
                "reason": reason,
            })

    free_rooms = [r["ma_phong"] for r in available_rooms]
    total_allocated = sum(a["so_sinh_vien"] for a in allocations)
    total_unallocated = sum(u["so_sinh_vien"] for u in unallocated_courses)

    avg_utilization = (
        round(sum(a["ti_le_lap_day"] for a in allocations) / len(allocations), 4)
        if allocations
        else 0.0
    )

    return {
        "allocations": allocations,
        "unallocated_courses": unallocated_courses,
        "used_rooms": used_rooms,
        "free_rooms": free_rooms,
        "avg_utilization": avg_utilization,
        "is_fully_allocated": len(unallocated_courses) == 0,
        "total_students_allocated": total_allocated,
        "total_students_unallocated": total_unallocated,
    }


def allocate_exam_rooms_ffd(
    shifts: Optional[Dict[int, List[str]]],
    course_sizes: Optional[Dict[str, int]],
    rooms: Optional[List[Dict[str, Any]]],
    course_names: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Phân bổ phòng thi FFD cho toàn bộ các ca thi trong kỳ thi.

    Mỗi ca thi, toàn bộ danh mục phòng của trường đều được giải phóng và
    tái sử dụng độc lập (Room Reusability).

    Args:
        shifts: Dictionary {ca_thi: [danh_sach_ma_mon]}
        course_sizes: Dictionary {ma_mon: so_sinh_vien}
        rooms: Danh mục phòng thi khả dụng của trường
        course_names: Dictionary {ma_mon: ten_mon} (tùy chọn)

    Returns:
        Dict tổng hợp kết quả phân phòng cho toàn kỳ thi:
        - shifts_allocation: Dictionary {ca_thi: ket_qua_allocate_shift_rooms_ffd}
        - is_all_successful: True nếu tất cả các ca thi đều xếp phòng 100%
        - total_shifts: Tổng số ca thi
        - total_courses: Tổng số môn thi
        - total_allocations_count: Tổng số lượt môn đã xếp phòng
        - total_unallocated_count: Tổng số lượt môn chưa xếp được phòng
        - overall_avg_utilization: Tỷ lệ lấp đầy phòng trung bình toàn trường
        - max_rooms_shift: Ca thi sử dụng nhiều phòng nhất
        - max_rooms_count: Số phòng sử dụng trong ca thi cao điểm nhất
    """
    if not shifts:
        return {
            "shifts_allocation": {},
            "is_all_successful": True,
            "total_shifts": 0,
            "total_courses": 0,
            "total_allocations_count": 0,
            "total_unallocated_count": 0,
            "overall_avg_utilization": 0.0,
            "max_rooms_shift": 0,
            "max_rooms_count": 0,
        }

    course_sizes = course_sizes or {}
    course_names = course_names or {}
    shifts_allocation: Dict[int, Dict[str, Any]] = {}
    all_successful = True
    total_allocations_count = 0
    total_unallocated_count = 0
    utilization_sum = 0.0
    utilization_count = 0

    max_rooms_shift = 0
    max_rooms_count = 0
    all_courses_set = set()

    def _shift_sort_key(item: Any) -> tuple:
        key = item[0]
        if isinstance(key, int) and not isinstance(key, bool):
            return (0, key, "")
        return (1, 0, str(key))

    for shift_id, course_list in sorted(shifts.items(), key=_shift_sort_key):
        shift_course_items = []
        for ma_mon in course_list or []:
            clean_ma = _safe_str(ma_mon)
            if not clean_ma:
                continue
            all_courses_set.add(clean_ma)
            raw_size = course_sizes.get(ma_mon)
            if raw_size is None:
                raw_size = course_sizes.get(clean_ma, 0)
            size = _safe_non_negative_int(raw_size)
            raw_name = course_names.get(ma_mon)
            if raw_name is None:
                raw_name = course_names.get(clean_ma, "")
            ten_mon = _safe_str(raw_name)
            shift_course_items.append({
                "ma_mon": clean_ma,
                "size": size,
                "ten_mon": ten_mon,
            })

        # Phân phòng cho ca thi hiện tại
        shift_result = allocate_shift_rooms_ffd(shift_course_items, rooms)
        shifts_allocation[shift_id] = shift_result

        if not shift_result["is_fully_allocated"]:
            all_successful = False

        total_allocations_count += len(shift_result["allocations"])
        total_unallocated_count += len(shift_result["unallocated_courses"])

        rooms_used_in_shift = len(shift_result["used_rooms"])
        if rooms_used_in_shift > max_rooms_count:
            max_rooms_count = rooms_used_in_shift
            max_rooms_shift = shift_id

        if shift_result["allocations"]:
            utilization_sum += sum(
                a["ti_le_lap_day"] for a in shift_result["allocations"]
            )
            utilization_count += len(shift_result["allocations"])

    overall_avg_utilization = (
        round(utilization_sum / utilization_count, 4) if utilization_count > 0 else 0.0
    )

    return {
        "shifts_allocation": shifts_allocation,
        "is_all_successful": all_successful,
        "total_shifts": len(shifts),
        "total_courses": len(all_courses_set),
        "total_allocations_count": total_allocations_count,
        "total_unallocated_count": total_unallocated_count,
        "overall_avg_utilization": overall_avg_utilization,
        "max_rooms_shift": max_rooms_shift,
        "max_rooms_count": max_rooms_count,
    }


def allocate_graph_schedule_rooms_ffd(
    G: Optional[nx.Graph],
    color_map: Optional[Dict[str, int]],
    rooms: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Kết nối trực tiếp kết quả tô màu đồ thị (DSatur / Welsh-Powell) vào phân phòng FFD.

    Args:
        G: Đồ thị xung đột NetworkX (chứa thuộc tính size và ten_mon của đỉnh).
        color_map: Kết quả gán màu {ma_mon: ca_thi}.
        rooms: Danh mục phòng thi khả dụng.

    Returns:
        Dict tổng hợp tương tự allocate_exam_rooms_ffd.
    """
    if not color_map:
        return allocate_exam_rooms_ffd(shifts={}, course_sizes={}, rooms=rooms)

    has_valid_graph = G is not None and isinstance(G, nx.Graph)
    shifts: Dict[int, List[str]] = {}
    course_sizes: Dict[str, int] = {}
    course_names: Dict[str, str] = {}

    for node, shift_id in color_map.items():
        if shift_id not in shifts:
            shifts[shift_id] = []
        shifts[shift_id].append(node)

        node_data = G.nodes[node] if (has_valid_graph and G.has_node(node)) else {}
        course_sizes[node] = _safe_non_negative_int(node_data.get("size", 0))
        course_names[node] = _safe_str(node_data.get("ten_mon", ""))

    return allocate_exam_rooms_ffd(
        shifts=shifts,
        course_sizes=course_sizes,
        rooms=rooms,
        course_names=course_names,
    )
