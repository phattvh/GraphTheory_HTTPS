"""Idempotent database seed script for GraphTheory_HTTPS (TV3 — Day 6).

Nạp dữ liệu mẫu chuẩn vào PostgreSQL 16 (chạy trong container fastapi):
- 1 kỳ thi mẫu (KTHK1_2026)
- 15 môn học (IT001..IT015)
- 100 sinh viên (22110001..22110100)
- 10 phòng thi (A101..C302)
- 300 lượt đăng ký thi (100 SV x 3 môn/SV, deterministic seed=42)
- 1 tài khoản sinh viên mẫu (sv01 / student123) gắn MSSV 22110001 để test Cổng Sinh viên & RBAC

Cách chạy:
    docker compose exec fastapi python scripts/seed.py
"""

from datetime import date
from pathlib import Path
import random
import sys
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.core.database import SessionLocal
from backend.core.security import get_password_hash
from backend.models.models import (
    DangKyThi,
    KyThi,
    MonHoc,
    NguoiDung,
    PhongThi,
    SinhVien,
)

SEED_RANDOM_STATE = 42
SEED_EXAM_CODE = "KTHK1_2026"
SEED_STUDENT_USERNAME = "sv01"
SEED_STUDENT_PASSWORD = "student123"

SEED_EXAM: Dict[str, Any] = {
    "ma_ky_thi": SEED_EXAM_CODE,
    "ten_ky_thi": "Thi Cuối Kỳ HK1 (2026 - 2027)",
    "ngay_bat_dau": date(2026, 12, 15),
    "ngay_ket_thuc": date(2026, 12, 22),
    "so_ca_moi_ngay": 4,
    "trang_thai": "khoi_tao",
}

SEED_COURSES: List[Dict[str, Any]] = [
    {"ma_mon": "IT001", "ten_mon": "Lý thuyết Đồ thị", "thoi_luong_phut": 90, "so_tin_chi": 3},
    {"ma_mon": "IT002", "ten_mon": "Cấu trúc Dữ liệu & Giải thuật", "thoi_luong_phut": 90, "so_tin_chi": 4},
    {"ma_mon": "IT003", "ten_mon": "Hệ Quản trị Cơ sở Dữ liệu PostgreSQL", "thoi_luong_phut": 90, "so_tin_chi": 3},
    {"ma_mon": "IT004", "ten_mon": "Lập trình Web", "thoi_luong_phut": 120, "so_tin_chi": 4},
    {"ma_mon": "IT005", "ten_mon": "An toàn & Bảo mật Thông tin", "thoi_luong_phut": 90, "so_tin_chi": 3},
    {"ma_mon": "IT006", "ten_mon": "Trí tuệ Nhân tạo", "thoi_luong_phut": 90, "so_tin_chi": 3},
    {"ma_mon": "IT007", "ten_mon": "Mạng Máy tính & Truyền thông", "thoi_luong_phut": 90, "so_tin_chi": 3},
    {"ma_mon": "IT008", "ten_mon": "Toán Rời rạc & Tổ hợp", "thoi_luong_phut": 90, "so_tin_chi": 3},
    {"ma_mon": "IT009", "ten_mon": "Giải tích 1", "thoi_luong_phut": 90, "so_tin_chi": 4},
    {"ma_mon": "IT010", "ten_mon": "Đại số Tuyến tính", "thoi_luong_phut": 90, "so_tin_chi": 3},
    {"ma_mon": "IT011", "ten_mon": "Kiến trúc Máy tính", "thoi_luong_phut": 90, "so_tin_chi": 3},
    {"ma_mon": "IT012", "ten_mon": "Lập trình Hướng đối tượng (OOP)", "thoi_luong_phut": 90, "so_tin_chi": 4},
    {"ma_mon": "IT013", "ten_mon": "Công nghệ Phần mềm", "thoi_luong_phut": 90, "so_tin_chi": 3},
    {"ma_mon": "IT014", "ten_mon": "Hệ điều hành", "thoi_luong_phut": 90, "so_tin_chi": 3},
    {"ma_mon": "IT015", "ten_mon": "Xác suất Thống kê", "thoi_luong_phut": 90, "so_tin_chi": 3},
]

SEED_ROOMS: List[Dict[str, Any]] = [
    {"ma_phong": "A101", "ten_phong": "Giảng đường A101", "suc_chua": 100, "toa_nha": "Nhà A", "dang_su_dung": True},
    {"ma_phong": "A102", "ten_phong": "Giảng đường A102", "suc_chua": 80, "toa_nha": "Nhà A", "dang_su_dung": True},
    {"ma_phong": "A103", "ten_phong": "Giảng đường A103", "suc_chua": 90, "toa_nha": "Nhà A", "dang_su_dung": True},
    {"ma_phong": "B201", "ten_phong": "Phòng thi B201", "suc_chua": 60, "toa_nha": "Nhà B", "dang_su_dung": True},
    {"ma_phong": "B202", "ten_phong": "Phòng thi B202", "suc_chua": 60, "toa_nha": "Nhà B", "dang_su_dung": True},
    {"ma_phong": "B203", "ten_phong": "Phòng thi B203", "suc_chua": 50, "toa_nha": "Nhà B", "dang_su_dung": True},
    {"ma_phong": "B204", "ten_phong": "Phòng thi B204", "suc_chua": 50, "toa_nha": "Nhà B", "dang_su_dung": True},
    {"ma_phong": "C301", "ten_phong": "Phòng máy C301", "suc_chua": 45, "toa_nha": "Nhà C", "dang_su_dung": True},
    {"ma_phong": "C302", "ten_phong": "Phòng máy C302", "suc_chua": 40, "toa_nha": "Nhà C", "dang_su_dung": True},
    {"ma_phong": "C303", "ten_phong": "Phòng máy C303", "suc_chua": 40, "toa_nha": "Nhà C", "dang_su_dung": True},
]

_LAST_NAMES = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng"]
_MIDDLE_NAMES = ["Văn", "Thị", "Minh", "Quốc", "Ngọc", "Hoàng", "Thanh", "Đức", "Anh", "Gia"]
_FIRST_NAMES = ["An", "Bình", "Châu", "Dũng", "Hà", "Hải", "Hưng", "Khôi", "Linh", "Nam"]
_CLASSES = ["22CNTT1", "22CNTT2", "22KTPM1", "22HTTT1"]


def build_seed_students(count: int = 100) -> List[Dict[str, str]]:
    """Tạo danh sách 100 sinh viên mẫu (22110001..22110100) có tính lặp lại."""
    students: List[Dict[str, str]] = []
    for idx in range(count):
        mssv = f"2211{idx + 1:04d}"
        ho = _LAST_NAMES[idx % len(_LAST_NAMES)]
        dem = _MIDDLE_NAMES[(idx // len(_LAST_NAMES)) % len(_MIDDLE_NAMES)]
        ten = _FIRST_NAMES[(idx * 3 + 1) % len(_FIRST_NAMES)]
        lop = _CLASSES[idx % len(_CLASSES)]
        students.append(
            {
                "mssv": mssv,
                "ho_ten": f"{ho} {dem} {ten}",
                "email": f"sv{mssv}@univ.edu.vn",
                "lop_sinh_hoat": lop,
            }
        )
    return students


def build_seed_registration_pairs(
    student_codes: List[str],
    course_codes: List[str],
    courses_per_student: int = 3,
    seed: int = SEED_RANDOM_STATE,
) -> List[Tuple[str, str]]:
    """Sinh chính xác 300 cặp (mssv, ma_mon) phân bố theo nhóm lớp để tạo đồ thị xung đột thực tế."""
    rng = random.Random(seed)
    pairs: List[Tuple[str, str]] = []

    # Chia 15 môn thành các nhóm theo khối kiến thức để tạo cụm cạnh xung đột rõ rệt
    cohort_pools = [
        course_codes[0:8],   # 22CNTT1: đồ thị, CTDL, CSDL, Web, ATTT, AI, Mạng, Toán RR
        course_codes[2:10],  # 22CNTT2: chồng lấn mạnh với CNTT1
        course_codes[5:13],  # 22KTPM1: AI, Mạng, Toán RR, GT1, ĐSTT, KTMT, OOP, CNPM
        course_codes[7:15],  # 22HTTT1: Toán RR -> XSTK
    ]

    for idx, mssv in enumerate(student_codes):
        pool = cohort_pools[idx % len(cohort_pools)]
        # Mỗi SV chọn 2 môn trong khối lớp + 1 môn tự chọn toàn trường (không trùng)
        chosen = rng.sample(pool, min(courses_per_student - 1, len(pool)))
        remaining = [c for c in course_codes if c not in chosen]
        chosen.append(rng.choice(remaining))
        for ma_mon in sorted(chosen):
            pairs.append((mssv, ma_mon))

    return pairs


def seed_database(db: Optional[Session] = None) -> Dict[str, Any]:
    """Nạp dữ liệu mẫu theo cơ chế idempotent trong một giao dịch ACID."""
    owns_session = db is None
    session = db if db is not None else SessionLocal()

    created = {
        "exams": 0,
        "courses": 0,
        "students": 0,
        "rooms": 0,
        "registrations": 0,
        "users": 0,
    }

    try:
        # 1. Kỳ thi mẫu (1 kỳ thi)
        exam = session.query(KyThi).filter(KyThi.ma_ky_thi == SEED_EXAM_CODE).first()
        if exam is None:
            exam = KyThi(**SEED_EXAM)
            session.add(exam)
            session.flush()
            created["exams"] = 1

        # 2. Môn học mẫu (15 môn)
        existing_courses = {
            c.ma_mon: c
            for c in session.query(MonHoc)
            .filter(MonHoc.ma_mon.in_([c["ma_mon"] for c in SEED_COURSES]))
            .all()
        }
        for c_data in SEED_COURSES:
            if c_data["ma_mon"] not in existing_courses:
                course = MonHoc(**c_data)
                session.add(course)
                existing_courses[c_data["ma_mon"]] = course
                created["courses"] += 1
        session.flush()

        # 3. Sinh viên mẫu (100 SV)
        seed_students = build_seed_students(100)
        existing_students = {
            s.mssv: s
            for s in session.query(SinhVien)
            .filter(SinhVien.mssv.in_([s["mssv"] for s in seed_students]))
            .all()
        }
        for s_data in seed_students:
            if s_data["mssv"] not in existing_students:
                student = SinhVien(**s_data)
                session.add(student)
                existing_students[s_data["mssv"]] = student
                created["students"] += 1
        session.flush()

        # 4. Phòng thi mẫu (10 phòng)
        existing_rooms = {
            r.ma_phong: r
            for r in session.query(PhongThi)
            .filter(PhongThi.ma_phong.in_([r["ma_phong"] for r in SEED_ROOMS]))
            .all()
        }
        for r_data in SEED_ROOMS:
            if r_data["ma_phong"] not in existing_rooms:
                room = PhongThi(**r_data)
                session.add(room)
                existing_rooms[r_data["ma_phong"]] = room
                created["rooms"] += 1
        session.flush()

        # 5. Đăng ký thi mẫu (300 lượt đăng ký)
        reg_pairs = build_seed_registration_pairs(
            student_codes=[s["mssv"] for s in seed_students],
            course_codes=[c["ma_mon"] for c in SEED_COURSES],
            courses_per_student=3,
        )
        existing_regs = {
            (r.sinh_vien_id, r.mon_hoc_id)
            for r in session.query(DangKyThi.sinh_vien_id, DangKyThi.mon_hoc_id)
            .filter(DangKyThi.ky_thi_id == exam.id)
            .all()
        }
        for mssv, ma_mon in reg_pairs:
            sv_id = existing_students[mssv].id
            mh_id = existing_courses[ma_mon].id
            if (sv_id, mh_id) not in existing_regs:
                session.add(
                    DangKyThi(
                        ky_thi_id=exam.id,
                        sinh_vien_id=sv_id,
                        mon_hoc_id=mh_id,
                    )
                )
                existing_regs.add((sv_id, mh_id))
                created["registrations"] += 1

        # 6. Tài khoản sinh viên mẫu (sv01 -> 22110001)
        demo_sv = existing_students["22110001"]
        demo_user = (
            session.query(NguoiDung)
            .filter(NguoiDung.ten_dang_nhap == SEED_STUDENT_USERNAME)
            .first()
        )
        if demo_user is None:
            session.add(
                NguoiDung(
                    ten_dang_nhap=SEED_STUDENT_USERNAME,
                    mat_khau_hash=get_password_hash(SEED_STUDENT_PASSWORD),
                    vai_tro="sinh_vien",
                    mssv=demo_sv.mssv,
                    ho_ten=demo_sv.ho_ten,
                    email=demo_sv.email,
                )
            )
            created["users"] = 1

        session.commit()

        totals = {
            "exams": session.query(KyThi).filter(KyThi.ma_ky_thi == SEED_EXAM_CODE).count(),
            "courses": session.query(MonHoc)
            .filter(MonHoc.ma_mon.in_([c["ma_mon"] for c in SEED_COURSES]))
            .count(),
            "students": session.query(SinhVien)
            .filter(SinhVien.mssv.in_([s["mssv"] for s in seed_students]))
            .count(),
            "rooms": session.query(PhongThi)
            .filter(PhongThi.ma_phong.in_([r["ma_phong"] for r in SEED_ROOMS]))
            .count(),
            "registrations": session.query(DangKyThi)
            .filter(DangKyThi.ky_thi_id == exam.id)
            .count(),
        }
        return {"exam_id": exam.id, "created": created, "totals": totals}
    except Exception:
        session.rollback()
        raise
    finally:
        if owns_session:
            session.close()


def main() -> int:
    result = seed_database()
    c = result["created"]
    t = result["totals"]
    print("=== NẠP DỮ LIỆU MẪU THÀNH CÔNG (scripts/seed.py) ===")
    print(f"  - Kỳ thi ({SEED_EXAM_CODE}):     tổng {t['exams']:>3} (thêm mới: {c['exams']})")
    print(f"  - Môn học (IT001..IT015):  tổng {t['courses']:>3} (thêm mới: {c['courses']})")
    print(f"  - Sinh viên (22110001..):  tổng {t['students']:>3} (thêm mới: {c['students']})")
    print(f"  - Phòng thi (A101..C303):  tổng {t['rooms']:>3} (thêm mới: {c['rooms']})")
    print(f"  - Đăng ký thi:             tổng {t['registrations']:>3} (thêm mới: {c['registrations']})")
    print(f"  - Tài khoản SV mẫu (sv01): thêm mới {c['users']} (pass dev: {SEED_STUDENT_PASSWORD})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
