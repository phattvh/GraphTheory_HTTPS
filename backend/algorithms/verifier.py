"""Module Schedule Verifier kiểm chứng 3 ràng buộc cứng của lịch thi (UC08.4).

Đóng vai trò cổng kiểm duyệt cuối cùng (Quality Gate) trước khi ghi lịch thi vào CSDL
trong giao dịch ACID:
1. Ràng buộc 1 (Zero Conflicts): 0% cạnh xung đột chung ca thi; mỗi môn chỉ thuộc duy nhất 1 ca.
2. Ràng buộc 2 (Room Capacities): 0 <= so_sinh_vien <= suc_chua, không trùng phòng trong cùng ca,
   và chỉ sử dụng phòng hợp lệ đang hoạt động (dang_su_dung=True).
3. Ràng buộc 3 (Student Completeness): Đủ 100% môn thi và bảo toàn tuyệt đối sĩ số thí sinh
   (tổng SV các phòng con khi Room Splitting phải bằng đúng sĩ số môn ban đầu).
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set
import networkx as nx


def _safe_str(value: Any, default: str = "") -> str:
    """Chuẩn hóa chuỗi an toàn, tránh chuyển None thành 'None'."""
    if value is None:
        return default
    return str(value).strip()


def _safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Ép kiểu số nguyên an toàn, chống crash với None/bool/inf/chuỗi bẩn."""
    if value is None or isinstance(value, bool):
        return default
    try:
        return int(value)
    except (ValueError, TypeError, OverflowError):
        return default


def _is_room_active(value: Any) -> bool:
    """Chuẩn hóa cờ dang_su_dung, từ chối False, 0 và chuỗi 'false'/'0'/'no'/'off'."""
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "off", ""}
    return bool(value)


def _extract_allocations_list(shift_data: Any) -> List[Dict[str, Any]]:
    """Trích xuất danh sách bản ghi phân phòng từ dữ liệu của một ca thi."""
    if isinstance(shift_data, dict):
        allocs = shift_data.get("allocations", [])
        return [a for a in allocs if isinstance(a, dict)] if isinstance(allocs, list) else []
    if isinstance(shift_data, list):
        return [a for a in shift_data if isinstance(a, dict)]
    return []


def verify_zero_conflicts(
    G: Optional[nx.Graph],
    color_map: Optional[Dict[str, Any]] = None,
    shifts_allocation: Optional[Dict[Any, Any]] = None,
) -> Dict[str, Any]:
    """Ràng buộc 1: Kiểm chứng 0% cạnh xung đột chung ca thi và nhất quán ca thi của từng môn.

    Args:
        G: Đồ thị xung đột vô hướng có trọng số G = (V, E, W).
        color_map: Bản đồ phân ca {ma_mon: ca_thi} (tùy chọn nếu đã truyền shifts_allocation).
        shifts_allocation: Kết quả phân phòng theo ca {ca_thi: {'allocations': [...]}}.

    Returns:
        Dict báo cáo gồm:
        - passed: True nếu không có cạnh nào chung ca và không có môn nào nằm ở >= 2 ca.
        - edge_conflicts: Danh sách cạnh vi phạm [{'u', 'v', 'shift', 'weight'}].
        - multi_shift_courses: Danh sách môn bị xếp trùng ở >= 2 ca [{'ma_mon', 'shifts'}].
        - conflicts_count: Tổng số vi phạm xung đột.
    """
    course_shifts: Dict[str, Set[Any]] = defaultdict(set)

    # Thu thập tập ca thi của từng môn từ shifts_allocation (nguồn thực tế sau phân phòng)
    if isinstance(shifts_allocation, dict) and shifts_allocation:
        for shift_id, shift_data in shifts_allocation.items():
            for alloc in _extract_allocations_list(shift_data):
                ma_mon = _safe_str(alloc.get("ma_mon"))
                if ma_mon:
                    course_shifts[ma_mon].add(shift_id)

    # Bổ sung từ color_map nếu shifts_allocation chưa có hoặc rỗng
    if isinstance(color_map, dict):
        for raw_mon, shift_id in color_map.items():
            ma_mon = _safe_str(raw_mon)
            if ma_mon and shift_id is not None:
                if not shifts_allocation:
                    course_shifts[ma_mon].add(shift_id)

    # 1. Kiểm tra môn xuất hiện ở >= 2 ca thi khác nhau
    multi_shift_courses: List[Dict[str, Any]] = []
    for ma_mon, shift_set in sorted(course_shifts.items()):
        if len(shift_set) > 1:
            multi_shift_courses.append({
                "ma_mon": ma_mon,
                "shifts": sorted(shift_set, key=lambda s: str(s)),
            })

    # 2. Kiểm tra mọi cạnh (u, v) in E không bao giờ có chung ca thi
    edge_conflicts: List[Dict[str, Any]] = []
    if G is not None and isinstance(G, nx.Graph):
        for u, v, edge_data in G.edges(data=True):
            u_code = _safe_str(u)
            v_code = _safe_str(v)
            if u_code in course_shifts and v_code in course_shifts:
                shared_shifts = course_shifts[u_code] & course_shifts[v_code]
                for shared_shift in sorted(shared_shifts, key=lambda s: str(s)):
                    weight = _safe_int(edge_data.get("weight", 1), default=1)
                    edge_conflicts.append({
                        "u": u_code,
                        "v": v_code,
                        "shift": shared_shift,
                        "weight": weight,
                    })

    total_violations = len(edge_conflicts) + len(multi_shift_courses)
    return {
        "passed": total_violations == 0,
        "edge_conflicts": edge_conflicts,
        "multi_shift_courses": multi_shift_courses,
        "conflicts_count": total_violations,
    }


def verify_room_capacities(
    shifts_allocation: Optional[Dict[Any, Any]],
    rooms: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Ràng buộc 2: Kiểm chứng đủ sức chứa phòng, không trùng phòng trong cùng ca và phòng hợp lệ.

    Args:
        shifts_allocation: Kết quả phân phòng theo ca {ca_thi: {'allocations': [...]}}.
        rooms: Danh mục phòng thi chính thức của trường (tùy chọn). Nếu truyền vào,
               sức chứa và trạng thái dang_su_dung trong danh mục này là nguồn đối chiếu chuẩn.

    Returns:
        Dict báo cáo gồm:
        - passed: True nếu 0 vi phạm sức chứa, 0 trùng phòng, 0 phòng không hợp lệ.
        - capacity_violations: Danh sách bản ghi vượt sức chứa hoặc sĩ số âm.
        - double_booked_rooms: Danh sách phòng bị gán >= 2 môn trong cùng 1 ca.
        - invalid_rooms: Danh sách phòng không tồn tại hoặc dang_su_dung=False.
        - violations_count: Tổng số vi phạm phòng thi.
    """
    capacity_violations: List[Dict[str, Any]] = []
    double_booked_rooms: List[Dict[str, Any]] = []
    invalid_rooms: List[Dict[str, Any]] = []

    if not isinstance(shifts_allocation, dict) or not shifts_allocation:
        return {
            "passed": True,
            "capacity_violations": [],
            "double_booked_rooms": [],
            "invalid_rooms": [],
            "violations_count": 0,
        }

    # Lập bảng tra cứu danh mục phòng nếu được cung cấp
    has_room_catalog = rooms is not None
    active_room_caps: Dict[str, int] = {}
    inactive_room_ids: Set[str] = set()

    if has_room_catalog and isinstance(rooms, list):
        for r in rooms:
            if not isinstance(r, dict):
                continue
            ma_phong = _safe_str(r.get("ma_phong"))
            if not ma_phong:
                continue
            if not _is_room_active(r.get("dang_su_dung", True)):
                inactive_room_ids.add(ma_phong)
                continue
            raw_cap = r.get("suc_chua")
            if raw_cap is None:
                raw_cap = r.get("capacity")
            cap = _safe_int(raw_cap, default=0)
            if cap is not None and cap > 0:
                if ma_phong not in active_room_caps:
                    active_room_caps[ma_phong] = cap

    for shift_id, shift_data in sorted(shifts_allocation.items(), key=lambda x: str(x[0])):
        allocations = _extract_allocations_list(shift_data)
        seen_rooms: Dict[str, List[str]] = defaultdict(list)

        for alloc in allocations:
            ma_mon = _safe_str(alloc.get("ma_mon"))
            ma_phong = _safe_str(alloc.get("ma_phong"))
            so_sv = _safe_int(alloc.get("so_sinh_vien"), default=None)
            declared_cap = _safe_int(alloc.get("suc_chua"), default=None)

            # Kiểm tra mã phòng hợp lệ
            if not ma_phong:
                invalid_rooms.append({
                    "shift": shift_id,
                    "ma_mon": ma_mon,
                    "ma_phong": "",
                    "reason": "Thiếu mã phòng thi trong bản ghi phân bổ",
                })
                continue

            seen_rooms[ma_phong].append(ma_mon or "<unknown>")

            # Đối chiếu danh mục phòng chuẩn nếu có
            effective_cap = declared_cap
            if has_room_catalog:
                if ma_phong in inactive_room_ids:
                    invalid_rooms.append({
                        "shift": shift_id,
                        "ma_mon": ma_mon,
                        "ma_phong": ma_phong,
                        "reason": "Phòng thi đang tạm khóa / bảo trì (dang_su_dung=False)",
                    })
                    continue
                if ma_phong not in active_room_caps:
                    invalid_rooms.append({
                        "shift": shift_id,
                        "ma_mon": ma_mon,
                        "ma_phong": ma_phong,
                        "reason": "Phòng thi không tồn tại trong danh mục phòng khả dụng",
                    })
                    continue
                effective_cap = active_room_caps[ma_phong]

            # Kiểm tra sĩ số hợp lệ và không vượt sức chứa
            if so_sv is None or so_sv < 0:
                capacity_violations.append({
                    "shift": shift_id,
                    "ma_mon": ma_mon,
                    "ma_phong": ma_phong,
                    "so_sinh_vien": so_sv,
                    "suc_chua": effective_cap,
                    "reason": "Số sinh viên phân bổ không hợp lệ hoặc âm",
                })
            elif effective_cap is None or effective_cap <= 0:
                capacity_violations.append({
                    "shift": shift_id,
                    "ma_mon": ma_mon,
                    "ma_phong": ma_phong,
                    "so_sinh_vien": so_sv,
                    "suc_chua": effective_cap,
                    "reason": "Sức chứa phòng không hợp lệ (<= 0)",
                })
            elif so_sv > effective_cap:
                capacity_violations.append({
                    "shift": shift_id,
                    "ma_mon": ma_mon,
                    "ma_phong": ma_phong,
                    "so_sinh_vien": so_sv,
                    "suc_chua": effective_cap,
                    "reason": f"Vượt sức chứa phòng ({so_sv} SV > {effective_cap} chỗ)",
                })

        # Kiểm tra trùng phòng trong cùng 1 ca thi
        for room_code, assigned_courses in sorted(seen_rooms.items()):
            if len(assigned_courses) > 1:
                double_booked_rooms.append({
                    "shift": shift_id,
                    "ma_phong": room_code,
                    "courses": assigned_courses,
                })

    total_violations = (
        len(capacity_violations) + len(double_booked_rooms) + len(invalid_rooms)
    )
    return {
        "passed": total_violations == 0,
        "capacity_violations": capacity_violations,
        "double_booked_rooms": double_booked_rooms,
        "invalid_rooms": invalid_rooms,
        "violations_count": total_violations,
    }


def verify_student_completeness(
    G: Optional[nx.Graph],
    shifts_allocation: Optional[Dict[Any, Any]],
    expected_course_sizes: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Ràng buộc 3: Kiểm chứng đủ 100% môn thi và bảo toàn chính xác số lượng thí sinh.

    Hỗ trợ hoàn hảo Room Splitting: tự động cộng dồn số sinh viên của cùng một môn
    trên nhiều phòng con để đối chiếu với sĩ số kỳ vọng.

    Args:
        G: Đồ thị xung đột chứa thuộc tính đỉnh `size` (dùng khi không truyền expected_course_sizes).
        shifts_allocation: Kết quả phân phòng theo ca {ca_thi: {'allocations': [...]}}.
        expected_course_sizes: Dictionary {ma_mon: so_sinh_vien_ky_vong} (ưu tiên nếu truyền vào).

    Returns:
        Dict báo cáo gồm:
        - passed: True nếu không sót môn, không thừa môn lạ, và mọi môn khớp 100% sĩ số.
        - missing_courses: Danh sách môn có trong kỳ thi nhưng chưa được xếp phòng.
        - unexpected_courses: Danh sách môn lạ xuất hiện trong lịch nhưng không có ở đầu vào.
        - student_count_mismatches: Danh sách môn có tổng SV phân bổ lệch với sĩ số kỳ vọng.
        - total_courses_expected / total_courses_scheduled
        - total_students_expected / total_students_scheduled
        - violations_count
    """
    expected_sizes: Dict[str, int] = {}

    if isinstance(expected_course_sizes, dict):
        for raw_code, raw_size in expected_course_sizes.items():
            code = _safe_str(raw_code)
            size = _safe_int(raw_size, default=0)
            if code:
                expected_sizes[code] = max(0, size if size is not None else 0)
    elif G is not None and isinstance(G, nx.Graph):
        for node, data in G.nodes(data=True):
            code = _safe_str(node)
            size = _safe_int(data.get("size", 0), default=0)
            if code:
                expected_sizes[code] = max(0, size if size is not None else 0)

    # Cộng dồn sĩ số thực tế đã xếp phòng theo từng môn (gộp cả các phòng con Room Splitting)
    scheduled_sizes: Dict[str, int] = defaultdict(int)
    scheduled_courses: Set[str] = set()

    if isinstance(shifts_allocation, dict):
        for shift_data in shifts_allocation.values():
            for alloc in _extract_allocations_list(shift_data):
                ma_mon = _safe_str(alloc.get("ma_mon"))
                if not ma_mon:
                    continue
                scheduled_courses.add(ma_mon)
                so_sv = _safe_int(alloc.get("so_sinh_vien"), default=0)
                scheduled_sizes[ma_mon] += so_sv if (so_sv is not None and so_sv > 0) else 0

    expected_set = set(expected_sizes.keys())
    missing_courses = sorted(expected_set - scheduled_courses)
    unexpected_courses = sorted(scheduled_courses - expected_set)

    student_count_mismatches: List[Dict[str, Any]] = []
    for ma_mon in sorted(expected_set & scheduled_courses):
        exp = expected_sizes[ma_mon]
        act = scheduled_sizes[ma_mon]
        if act != exp:
            student_count_mismatches.append({
                "ma_mon": ma_mon,
                "expected": exp,
                "actual": act,
                "diff": act - exp,
            })

    total_violations = (
        len(missing_courses) + len(unexpected_courses) + len(student_count_mismatches)
    )
    return {
        "passed": total_violations == 0,
        "missing_courses": missing_courses,
        "unexpected_courses": unexpected_courses,
        "student_count_mismatches": student_count_mismatches,
        "total_courses_expected": len(expected_set),
        "total_courses_scheduled": len(scheduled_courses),
        "total_students_expected": sum(expected_sizes.values()),
        "total_students_scheduled": sum(scheduled_sizes.values()),
        "violations_count": total_violations,
    }


def verify_schedule(
    G: Optional[nx.Graph],
    schedule_result: Optional[Dict[str, Any]],
    rooms: Optional[List[Dict[str, Any]]] = None,
    expected_course_sizes: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Kiểm chứng toàn diện lịch thi trên cả 3 ràng buộc cứng (UC08.4).

    Nhận trực tiếp kết quả trả về từ `allocate_graph_schedule_with_overflow`,
    `allocate_exam_rooms_with_spilling`, `allocate_graph_schedule_rooms_ffd` hoặc
    `allocate_exam_rooms_ffd`.

    Args:
        G: Đồ thị xung đột G = (V, E, W).
        schedule_result: Dict kết quả phân phòng (chứa `shifts_allocation` và tùy chọn `final_color_map`).
        rooms: Danh mục phòng thi của trường (tùy chọn, khuyến nghị truyền để đối chiếu sức chứa & trạng thái).
        expected_course_sizes: Dictionary {ma_mon: size} (tùy chọn, mặc định đọc từ G.nodes[u]['size']).

    Returns:
        Báo cáo kiểm chứng chuẩn JSON:
        - is_valid: True khi và chỉ khi cả 3 ràng buộc đều PASS (0 vi phạm).
        - summary: Thống kê tổng quan trạng thái từng ràng buộc và số lượng môn/thí sinh.
        - checks: Kết quả chi tiết của 3 bộ kiểm chứng (`conflicts`, `capacity`, `completeness`).
        - errors: Danh sách thông báo lỗi tiếng Việt rõ ràng cho API / giao diện.
    """
    result_dict = schedule_result if isinstance(schedule_result, dict) else {}
    shifts_allocation = result_dict.get("shifts_allocation", {})
    color_map = result_dict.get("final_color_map") or result_dict.get("color_map")

    conflicts_check = verify_zero_conflicts(
        G=G,
        color_map=color_map,
        shifts_allocation=shifts_allocation,
    )
    capacity_check = verify_room_capacities(
        shifts_allocation=shifts_allocation,
        rooms=rooms,
    )
    completeness_check = verify_student_completeness(
        G=G,
        shifts_allocation=shifts_allocation,
        expected_course_sizes=expected_course_sizes,
    )

    errors: List[str] = []

    for c in conflicts_check["edge_conflicts"]:
        errors.append(
            f"[Xung đột ca {c['shift']}] Hai môn {c['u']} và {c['v']} bị xếp trùng ca "
            f"(có {c['weight']} sinh viên thi chung)."
        )
    for m in conflicts_check["multi_shift_courses"]:
        errors.append(
            f"[Trùng lặp ca] Môn {m['ma_mon']} bị xếp đồng thời ở nhiều ca: {m['shifts']}."
        )
    for v in capacity_check["capacity_violations"]:
        errors.append(
            f"[Sức chứa ca {v['shift']}] Môn {v['ma_mon']} tại phòng {v['ma_phong']}: {v['reason']}."
        )
    for d in capacity_check["double_booked_rooms"]:
        errors.append(
            f"[Trùng phòng ca {d['shift']}] Phòng {d['ma_phong']} bị gán cho nhiều môn cùng lúc: {d['courses']}."
        )
    for inv in capacity_check["invalid_rooms"]:
        errors.append(
            f"[Phòng không hợp lệ ca {inv['shift']}] Môn {inv['ma_mon']} - phòng '{inv['ma_phong']}': {inv['reason']}."
        )
    for missing in completeness_check["missing_courses"]:
        errors.append(f"[Thiếu môn] Môn {missing} chưa được xếp phòng thi.")
    for extra in completeness_check["unexpected_courses"]:
        errors.append(f"[Môn lạ] Môn {extra} xuất hiện trong lịch nhưng không thuộc kỳ thi.")
    for mm in completeness_check["student_count_mismatches"]:
        errors.append(
            f"[Lệch sĩ số] Môn {mm['ma_mon']}: dự kiến {mm['expected']} SV nhưng chỉ xếp được {mm['actual']} SV."
        )

    total_violations = (
        conflicts_check["conflicts_count"]
        + capacity_check["violations_count"]
        + completeness_check["violations_count"]
    )
    is_valid = (
        conflicts_check["passed"]
        and capacity_check["passed"]
        and completeness_check["passed"]
    )

    return {
        "is_valid": is_valid,
        "summary": {
            "zero_conflicts_passed": conflicts_check["passed"],
            "room_capacity_passed": capacity_check["passed"],
            "student_completeness_passed": completeness_check["passed"],
            "total_violations": total_violations,
            "total_courses_expected": completeness_check["total_courses_expected"],
            "total_courses_scheduled": completeness_check["total_courses_scheduled"],
            "total_students_expected": completeness_check["total_students_expected"],
            "total_students_scheduled": completeness_check["total_students_scheduled"],
        },
        "checks": {
            "conflicts": conflicts_check,
            "capacity": capacity_check,
            "completeness": completeness_check,
        },
        "errors": errors,
    }
