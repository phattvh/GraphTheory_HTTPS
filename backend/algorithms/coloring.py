"""Module for exam graph vertex coloring algorithms.

Triển khai thuật toán tô màu đồ thị (Vertex Coloring Problem) ứng dụng cho xếp lịch thi:
- Thuật toán chính: DSatur (Degree of Saturation) theo Daniel Brélaz (1979).
- Đảm bảo 100% ràng buộc cứng: Không có 2 môn kề nhau (có sinh viên thi chung) nào bị trùng ca thi.
"""

from collections import defaultdict
from typing import Any, Dict, List
import networkx as nx


def dsatur_coloring(G: nx.Graph) -> Dict[str, Any]:
    """Tô màu đồ thị xung đột bằng thuật toán phỏng đoán Heuristic DSatur.

    Nguyên lý:
    1. Ưu tiên đỉnh có độ bão hòa màu sat(v) lớn nhất (kề với nhiều màu khác nhau nhất).
    2. Nếu bằng nhau: chọn đỉnh có bậc deg(v) trong tập chưa tô lớn nhất.
    3. Gán màu nguyên dương nhỏ nhất khả dĩ (1, 2, ..., k) không trùng màu với các đỉnh kề.

    Args:
        G: Đồ thị xung đột NetworkX (G = (V, E, W)).

    Returns:
        Dict chứa:
        - color_map: Dictionary {ma_mon: ca_thi} (ca_thi đánh số từ 1)
        - total_colors: Tổng số ca thi cần thiết (sắc số xấp xỉ chi(G))
        - shifts: Dictionary {ca_thi: [danh_sach_ma_mon]}
        - is_valid: True nếu 100% các cạnh không bị trùng màu (0% xung đột)
        - conflicts_count: Số cạnh vi phạm ràng buộc cứng (phải bằng 0)
    """
    if G is None or not isinstance(G, nx.Graph) or G.number_of_nodes() == 0:
        return {
            "color_map": {},
            "total_colors": 0,
            "shifts": {},
            "is_valid": True,
            "conflicts_count": 0,
            "conflict_pairs": [],
        }

    # 1. Thực thi thuật toán DSatur từ NetworkX (trả về 0-indexed colors)
    raw_coloring = nx.greedy_color(G, strategy="DSATUR")

    # 2. Chuẩn hóa sang 1-indexed ca thi (Ca 1, Ca 2, ...)
    color_map: Dict[str, int] = {
        node: raw_color + 1 for node, raw_color in raw_coloring.items()
    }

    # 3. Gom nhóm danh sách môn thi theo từng ca thi
    shifts_dict: Dict[int, List[str]] = defaultdict(list)
    for node, shift_id in color_map.items():
        shifts_dict[shift_id].append(node)

    # Sắp xếp danh sách ca thi tăng dần và danh sách môn theo thứ tự bảng chữ cái
    sorted_shifts: Dict[int, List[str]] = {
        shift: sorted(courses) for shift, courses in sorted(shifts_dict.items())
    }

    # 4. Kiểm chứng ràng buộc cứng & bóc tách chi tiết các cạnh vi phạm:
    # Với mọi cạnh (u, v) in E: color(u) != color(v)
    conflict_pairs: List[Dict[str, Any]] = []
    for u, v in G.edges():
        if u != v and color_map.get(u) == color_map.get(v):
            conflict_pairs.append({
                "course_u": u,
                "course_v": v,
                "shift": color_map.get(u),
                "weight": G[u][v].get("weight", 1),
            })

    is_valid = len(conflict_pairs) == 0
    total_colors = len(sorted_shifts)

    return {
        "color_map": color_map,
        "total_colors": total_colors,
        "shifts": sorted_shifts,
        "is_valid": is_valid,
        "conflicts_count": len(conflict_pairs),
        "conflict_pairs": conflict_pairs,
    }


def get_schedule_summary(G: nx.Graph, color_map: Dict[str, int]) -> Dict[str, Any]:
    """Tổng hợp số liệu thống kê tải trọng của lịch thi sau khi tô màu.

    Args:
        G: Đồ thị xung đột chứa thuộc tính đỉnh `size` (số lượng sinh viên).
        color_map: Dictionary phân ca {ma_mon: ca_thi}.

    Returns:
        Dict chứa các chỉ số thống kê tổng hợp:
        - total_courses: Tổng số môn thi
        - total_students: Tổng số lượt thi của toàn trường
        - total_shifts: Tổng số ca thi
        - max_students_shift: Ca thi có số lượng thí sinh đông nhất
        - max_students_count: Số thí sinh trong ca đông nhất
        - avg_students_per_shift: Số thí sinh trung bình mỗi ca thi
        - shift_details: Thống kê chi tiết từng ca (danh sách môn, số môn, tổng SV)
    """
    if not color_map or G is None or not isinstance(G, nx.Graph) or G.number_of_nodes() == 0:
        return {
            "total_courses": 0,
            "total_students": 0,
            "total_shifts": 0,
            "max_students_shift": 0,
            "max_students_count": 0,
            "avg_students_per_shift": 0.0,
            "shift_details": {},
        }

    shift_details: Dict[int, Dict[str, Any]] = defaultdict(
        lambda: {"courses": [], "course_count": 0, "total_students": 0}
    )

    for node, shift in color_map.items():
        # Xử lý an toàn: chống lỗi khi size=None hoặc kiểu chuỗi (ví dụ: '30')
        raw_count = G.nodes[node].get("size") if G.has_node(node) else 0
        try:
            student_count = int(raw_count) if raw_count is not None else 0
        except (ValueError, TypeError):
            student_count = 0

        shift_details[shift]["courses"].append(node)
        shift_details[shift]["course_count"] += 1
        shift_details[shift]["total_students"] += student_count

    # Sắp xếp chi tiết theo mã ca thi
    sorted_details = {
        shift: {
            "courses": sorted(data["courses"]),
            "course_count": data["course_count"],
            "total_students": data["total_students"],
        }
        for shift, data in sorted(shift_details.items())
    }

    students_per_shift = [d["total_students"] for d in sorted_details.values()]
    max_count = max(students_per_shift) if students_per_shift else 0
    max_shift = next(
        (s for s, d in sorted_details.items() if d["total_students"] == max_count), 0
    ) if max_count > 0 else 0
    total_students_all = sum(students_per_shift)
    total_shifts = len(sorted_details)
    avg_students = (
        round(total_students_all / total_shifts, 2) if total_shifts > 0 else 0.0
    )

    return {
        "total_courses": len(color_map),
        "total_students": total_students_all,
        "total_shifts": total_shifts,
        "max_students_shift": max_shift,
        "max_students_count": max_count,
        "avg_students_per_shift": avg_students,
        "shift_details": sorted_details,
    }
