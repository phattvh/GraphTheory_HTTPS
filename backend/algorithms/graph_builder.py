"""Module for constructing and analyzing exam conflict graphs.

Mô hình hóa toán học:
Đồ thị xung đột vô hướng có trọng số G = (V, E, W):
- Tập đỉnh V: Mỗi đỉnh v đại diện cho một môn thi. Thuộc tính `size` là số thí sinh đăng ký môn.
- Tập cạnh E: Cạnh (u, v) tồn tại khi có ít nhất 1 sinh viên thi chung cả 2 môn.
- Trọng số W: w(u, v) là số lượng sinh viên thi chung môn u và môn v.
- Bậc đỉnh deg(v): Số lượng môn thi xung đột với môn v.
"""

from collections import defaultdict
from itertools import combinations
from typing import Any, Dict, List, Optional, Union
import networkx as nx


def build_conflict_graph(
    registrations: List[Union[Dict[str, Any], tuple, list]],
    courses: Optional[List[Dict[str, Any]]] = None,
) -> nx.Graph:
    """Xây dựng đồ thị xung đột G = (V, E, W) từ danh sách đăng ký thi.

    Args:
        registrations: Danh sách lượt đăng ký thi.
                       Chấp nhận dict dạng {'mssv': '...', 'ma_mon': '...'}
                       hoặc tuple/list dạng (mssv, ma_mon).
        courses: Danh sách thông tin môn học (tùy chọn) để gán thêm metadata
                 (ví dụ: ten_mon, khoa_quan_ly). Nếu môn không có sinh viên
                 nào đăng ký thì vẫn được thêm vào đồ thị như một đỉnh cô lập.

    Returns:
        nx.Graph: Đồ thị xung đột vô hướng có trọng số cạnh và kích thước đỉnh.
    """
    G = nx.Graph()

    # 1. Nạp danh mục môn học ban đầu nếu được cung cấp
    if courses:
        for course in courses:
            if not isinstance(course, dict):
                continue
            raw_ma = course.get("ma_mon")
            if raw_ma is None or str(raw_ma).strip() == "":
                raw_ma = course.get("ma_mon_hoc")
            raw_ten = course.get("ten_mon")
            if raw_ten is None or str(raw_ten).strip() == "":
                raw_ten = course.get("ten_mon_hoc", "")
            ma_mon = "" if raw_ma is None else str(raw_ma).strip()
            if ma_mon:
                G.add_node(
                    ma_mon,
                    ma_mon=ma_mon,
                    ten_mon="" if raw_ten is None else str(raw_ten).strip(),
                    size=0,
                )

    # 2. Gom nhóm môn thi theo từng sinh viên & thống kê số lượng SV mỗi môn
    student_courses: Dict[str, set] = defaultdict(set)
    course_student_count: Dict[str, int] = defaultdict(int)

    for reg in registrations:
        if isinstance(reg, dict):
            raw_mssv = reg.get("mssv")
            if raw_mssv is None or str(raw_mssv).strip() == "":
                raw_mssv = reg.get("ma_sinh_vien")
            raw_mon = reg.get("ma_mon")
            if raw_mon is None or str(raw_mon).strip() == "":
                raw_mon = reg.get("ma_mon_hoc")
        elif isinstance(reg, (list, tuple)) and len(reg) >= 2:
            raw_mssv, raw_mon = reg[0], reg[1]
        else:
            continue
        
        mssv = "" if raw_mssv is None else str(raw_mssv).strip()
        ma_mon = "" if raw_mon is None else str(raw_mon).strip()

        if not mssv or not ma_mon:
            continue

        if ma_mon not in student_courses[mssv]:
            student_courses[mssv].add(ma_mon)
            course_student_count[ma_mon] += 1

    # 3. Tạo/Cập nhật các đỉnh môn học với thuộc tính `size` (số thí sinh)
    for ma_mon, count in course_student_count.items():
        if not G.has_node(ma_mon):
            G.add_node(ma_mon, ma_mon=ma_mon, ten_mon="", size=count)
        else:
            G.nodes[ma_mon]["size"] = count

    # 4. Tạo các cạnh xung đột (E) và cộng dồn trọng số xung đột (W)
    # Nếu một sinh viên đăng ký n môn, tạo xung đột giữa mọi cặp (u, v) trong n môn đó
    for mssv, enrolled_courses in student_courses.items():
        if len(enrolled_courses) < 2:
            continue

        for u, v in combinations(enrolled_courses, 2):
            if G.has_edge(u, v):
                G[u][v]["weight"] += 1
            else:
                G.add_edge(u, v, weight=1)

    return G


def get_graph_metrics(G: nx.Graph) -> Dict[str, Any]:
    """Tính toán các chỉ số thống kê cơ bản của đồ thị xung đột.

    Args:
        G: Đồ thị xung đột NetworkX.

    Returns:
        Dict chứa các chỉ số:
        - total_nodes: Tổng số môn thi (|V|)
        - total_edges: Tổng số cặp môn xung đột (|E|)
        - density: Mật độ đồ thị (2|E| / (|V|(|V|-1)))
        - max_degree: Bậc lớn nhất
        - min_degree: Bậc nhỏ nhất
        - avg_degree: Bậc trung bình
        - degrees: Dictionary {ma_mon: degree} sắp xếp giảm dần theo bậc
        - isolated_nodes: Danh sách môn không xung đột với bất kỳ môn nào
    """
    total_nodes = G.number_of_nodes()
    total_edges = G.number_of_edges()

    if total_nodes == 0:
        return {
            "total_nodes": 0,
            "total_edges": 0,
            "density": 0.0,
            "max_degree": 0,
            "min_degree": 0,
            "avg_degree": 0.0,
            "degrees": {},
            "isolated_nodes": [],
        }

    degree_dict = dict(G.degree())
    sorted_degrees = dict(
        sorted(degree_dict.items(), key=lambda item: item[1], reverse=True)
    )

    degrees_list = list(degree_dict.values())
    max_deg = max(degrees_list)
    min_deg = min(degrees_list)
    avg_deg = round(sum(degrees_list) / total_nodes, 2)
    density = round(nx.density(G), 4)

    isolated = [node for node, deg in degree_dict.items() if deg == 0]

    return {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "density": density,
        "max_degree": max_deg,
        "min_degree": min_deg,
        "avg_degree": avg_deg,
        "degrees": sorted_degrees,
        "isolated_nodes": isolated,
    }
