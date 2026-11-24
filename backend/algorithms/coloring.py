"""Module for exam graph vertex coloring algorithms.

Triển khai thuật toán tô màu đồ thị (Vertex Coloring Problem) ứng dụng cho xếp lịch thi:
- Thuật toán chính: DSatur (Degree of Saturation) theo Daniel Brélaz (1979).
- Thuật toán đối chứng: Welsh–Powell (Static Degree Ordering / largest_first).
- Đảm bảo 100% ràng buộc cứng: Không có 2 môn kề nhau (có sinh viên thi chung) nào bị trùng ca thi.
"""

from collections import defaultdict
import time
from typing import Any, Dict, List
import networkx as nx


def _empty_coloring_result() -> Dict[str, Any]:
    """Khởi tạo dictionary kết quả tô màu rỗng độc lập (tránh shared reference)."""
    return {
        "color_map": {},
        "total_colors": 0,
        "shifts": {},
        "is_valid": True,
        "conflicts_count": 0,
        "conflict_pairs": [],
    }


def _run_coloring(G: nx.Graph, strategy: str) -> Dict[str, Any]:
    """Hàm nội bộ thực thi thuật toán tô màu tham lam NetworkX và kiểm chứng ràng buộc cứng."""
    if G is None or not isinstance(G, nx.Graph) or G.number_of_nodes() == 0:
        return _empty_coloring_result()

    # Đảm bảo đồ thị là vô hướng (tránh lỗi tô trùng màu khi truyền nx.DiGraph)
    graph = G.to_undirected() if G.is_directed() else G

    # 1. Thực thi thuật toán tô màu từ NetworkX (trả về 0-indexed colors)
    raw_coloring = nx.greedy_color(graph, strategy=strategy)

    # 2. Chuẩn hóa sang 1-indexed ca thi (Ca 1, Ca 2, ...)
    color_map: Dict[Any, int] = {
        node: raw_color + 1 for node, raw_color in raw_coloring.items()
    }

    # 3. Gom nhóm danh sách môn thi theo từng ca thi
    shifts_dict: Dict[int, List[Any]] = defaultdict(list)
    for node, shift_id in color_map.items():
        shifts_dict[shift_id].append(node)

    # Sắp xếp danh sách ca thi tăng dần và danh sách môn ổn định (hỗ trợ cả int và str)
    sorted_shifts: Dict[int, List[Any]] = {
        shift: sorted(courses, key=str)
        for shift, courses in sorted(shifts_dict.items())
    }

    # 4. Kiểm chứng ràng buộc cứng & bóc tách chi tiết các cạnh vi phạm:
    # Với mọi cạnh (u, v) in E: color(u) != color(v)
    conflict_pairs: List[Dict[str, Any]] = []
    for u, v in graph.edges():
        if u != v and color_map.get(u) == color_map.get(v):
            conflict_pairs.append({
                "course_u": u,
                "course_v": v,
                "shift": color_map.get(u),
                "weight": graph[u][v].get("weight", 1),
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
        - conflict_pairs: Danh sách các cặp môn vi phạm (nếu có)
    """
    return _run_coloring(G, strategy="DSATUR")


def welsh_powell_coloring(G: nx.Graph) -> Dict[str, Any]:
    """Tô màu đồ thị xung đột bằng thuật toán phỏng đoán tham lam Welsh–Powell.

    Nguyên lý:
    1. Sắp xếp danh sách các đỉnh theo thứ tự bậc giảm dần: deg(v_1) >= deg(v_2) >= ... >= deg(v_n).
    2. Duyệt qua danh sách đỉnh chưa tô, gán màu c = 1 cho đỉnh đầu tiên và các đỉnh không kề với các đỉnh đã tô màu c.
    3. Tăng c = c + 1 và lặp lại cho đến khi toàn bộ các đỉnh được tô màu.
    (Trong NetworkX, thuật toán tương ứng chính xác với strategy="largest_first").

    Args:
        G: Đồ thị xung đột NetworkX (G = (V, E, W)).

    Returns:
        Dict chứa:
        - color_map: Dictionary {ma_mon: ca_thi} (ca_thi đánh số từ 1)
        - total_colors: Tổng số ca thi cần thiết (sắc số xấp xỉ)
        - shifts: Dictionary {ca_thi: [danh_sach_ma_mon]}
        - is_valid: True nếu 100% các cạnh không bị trùng màu (0% xung đột)
        - conflicts_count: Số cạnh vi phạm ràng buộc cứng (phải bằng 0)
        - conflict_pairs: Danh sách các cặp môn vi phạm (nếu có)
    """
    return _run_coloring(G, strategy="largest_first")


def get_schedule_summary(G: nx.Graph, color_map: Dict[Any, int]) -> Dict[str, Any]:
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
            "courses": sorted(data["courses"], key=str),
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


def compare_coloring_algorithms(G: nx.Graph) -> Dict[str, Any]:
    """So sánh toàn diện và đối chứng hiệu năng giữa thuật toán DSatur và Welsh–Powell.

    Args:
        G: Đồ thị xung đột NetworkX (G = (V, E, W)).

    Returns:
        Dict chứa:
        - dsatur: Kết quả chi tiết của DSatur kèm thời gian chạy (ms) và thống kê tải trọng
        - welsh_powell: Kết quả chi tiết của Welsh-Powell kèm thời gian chạy (ms) và thống kê tải trọng
        - comparison:
            - dsatur_colors: Số ca thi của DSatur
            - welsh_powell_colors: Số ca thi của Welsh-Powell
            - color_difference: welsh_powell_colors - dsatur_colors (>= 0 nếu DSatur tối ưu hơn hoặc bằng)
            - winner: "DSATUR" | "WELSH_POWELL" | "TIE"
            - dsatur_time_ms: Thời gian chạy DSatur (ms)
            - welsh_powell_time_ms: Thời gian chạy Welsh-Powell (ms)
            - both_valid: True nếu cả 2 thuật toán đều đạt 0% xung đột
    """
    if G is None or not isinstance(G, nx.Graph) or G.number_of_nodes() == 0:
        def _empty_benchmark_entry() -> Dict[str, Any]:
            entry = _empty_coloring_result()
            entry["execution_time_ms"] = 0.0
            entry["summary"] = get_schedule_summary(G, {})
            return entry

        return {
            "dsatur": _empty_benchmark_entry(),
            "welsh_powell": _empty_benchmark_entry(),
            "comparison": {
                "dsatur_colors": 0,
                "welsh_powell_colors": 0,
                "color_difference": 0,
                "winner": "TIE",
                "dsatur_time_ms": 0.0,
                "welsh_powell_time_ms": 0.0,
                "both_valid": True,
            },
        }

    # 1. Đo lường và thực thi DSatur
    start_dsatur = time.perf_counter()
    dsatur_res = dsatur_coloring(G)
    dsatur_time_ms = round((time.perf_counter() - start_dsatur) * 1000, 4)
    dsatur_summary = get_schedule_summary(G, dsatur_res["color_map"])
    dsatur_res["execution_time_ms"] = dsatur_time_ms
    dsatur_res["summary"] = dsatur_summary

    # 2. Đo lường và thực thi Welsh-Powell
    start_wp = time.perf_counter()
    wp_res = welsh_powell_coloring(G)
    wp_time_ms = round((time.perf_counter() - start_wp) * 1000, 4)
    wp_summary = get_schedule_summary(G, wp_res["color_map"])
    wp_res["execution_time_ms"] = wp_time_ms
    wp_res["summary"] = wp_summary

    # 3. Phân tích đối sánh
    dsatur_colors = dsatur_res["total_colors"]
    wp_colors = wp_res["total_colors"]
    diff = wp_colors - dsatur_colors

    if dsatur_colors < wp_colors:
        winner = "DSATUR"
    elif dsatur_colors > wp_colors:
        winner = "WELSH_POWELL"
    else:
        winner = "TIE"

    both_valid = dsatur_res["is_valid"] and wp_res["is_valid"]

    return {
        "dsatur": dsatur_res,
        "welsh_powell": wp_res,
        "comparison": {
            "dsatur_colors": dsatur_colors,
            "welsh_powell_colors": wp_colors,
            "color_difference": diff,
            "winner": winner,
            "dsatur_time_ms": dsatur_time_ms,
            "welsh_powell_time_ms": wp_time_ms,
            "both_valid": both_valid,
        },
    }
