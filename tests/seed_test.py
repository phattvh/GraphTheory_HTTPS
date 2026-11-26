"""Automated tests for scripts/seed.py (TV3 — Day 6).

Verifies:
1. Running seed_database() twice is 100% idempotent (0 new rows on 2nd run, no IntegrityError).
2. PostgreSQL contains the exact seeded dataset: 1 exam, 15 courses, 100 students, 10 rooms, 300 registrations, and demo student account sv01.
3. End-to-end graph pipeline (build_conflict_graph -> dsatur_coloring -> allocate_graph_schedule_with_overflow) succeeds with 0% conflicts and 300/300 students allocated.
"""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.algorithms import (
    allocate_graph_schedule_with_overflow,
    build_conflict_graph,
    dsatur_coloring,
)
from backend.core.database import SessionLocal
from backend.core.security import verify_password
from backend.models.models import (
    DangKyThi,
    KyThi,
    MonHoc,
    NguoiDung,
    PhongThi,
    SinhVien,
)
from scripts.seed import (
    SEED_COURSES,
    SEED_EXAM_CODE,
    SEED_ROOMS,
    SEED_STUDENT_PASSWORD,
    SEED_STUDENT_USERNAME,
    seed_database,
)


def test_seed_idempotency_and_counts() -> None:
    first = seed_database()
    assert first["totals"]["exams"] == 1
    assert first["totals"]["courses"] == 15
    assert first["totals"]["students"] == 100
    assert first["totals"]["rooms"] == 10
    assert first["totals"]["registrations"] == 300

    # Chạy lần 2 phải hoàn toàn idempotent (không thêm trùng dòng nào)
    second = seed_database()
    assert all(count == 0 for count in second["created"].values()), (
        f"Expected 0 created records on 2nd run, got: {second['created']}"
    )
    assert second["totals"] == first["totals"]
    print("[PASS] seed_database() idempotent (1 exam, 15 courses, 100 students, 10 rooms, 300 registrations).")


def test_seeded_student_account() -> None:
    db = SessionLocal()
    try:
        user = (
            db.query(NguoiDung)
            .filter(NguoiDung.ten_dang_nhap == SEED_STUDENT_USERNAME)
            .first()
        )
        assert user is not None, "Thiếu tài khoản sinh viên mẫu sv01"
        assert user.vai_tro == "sinh_vien"
        assert user.mssv == "22110001"
        assert verify_password(SEED_STUDENT_PASSWORD, user.mat_khau_hash)
    finally:
        db.close()
    print("[PASS] Seeded student user sv01 linked to MSSV 22110001 with valid bcrypt hash.")


def test_seeded_data_runs_graph_and_ffd_pipeline() -> None:
    db = SessionLocal()
    try:
        exam = db.query(KyThi).filter(KyThi.ma_ky_thi == SEED_EXAM_CODE).first()
        assert exam is not None

        courses = [
            {"ma_mon": c.ma_mon, "ten_mon": c.ten_mon}
            for c in db.query(MonHoc)
            .filter(MonHoc.ma_mon.in_([x["ma_mon"] for x in SEED_COURSES]))
            .all()
        ]
        regs_rows = (
            db.query(SinhVien.mssv, MonHoc.ma_mon)
            .join(DangKyThi, DangKyThi.sinh_vien_id == SinhVien.id)
            .join(MonHoc, DangKyThi.mon_hoc_id == MonHoc.id)
            .filter(DangKyThi.ky_thi_id == exam.id)
            .all()
        )
        rooms = [
            {
                "ma_phong": r.ma_phong,
                "ten_phong": r.ten_phong,
                "suc_chua": r.suc_chua,
                "dang_su_dung": r.dang_su_dung,
            }
            for r in db.query(PhongThi)
            .filter(PhongThi.ma_phong.in_([x["ma_phong"] for x in SEED_ROOMS]))
            .all()
        ]
    finally:
        db.close()

    assert len(regs_rows) == 300
    reg_tuples = [(row[0], row[1]) for row in regs_rows]
    G = build_conflict_graph(reg_tuples, courses=courses)
    assert G.number_of_nodes() == 15
    assert G.number_of_edges() > 0

    coloring = dsatur_coloring(G)
    assert coloring["is_valid"] is True
    assert coloring["total_colors"] >= 3

    ffd = allocate_graph_schedule_with_overflow(
        G=G,
        color_map=coloring["color_map"],
        rooms=rooms,
        allow_room_splitting=True,
        allow_shift_spilling=True,
    )
    assert ffd["is_all_successful"] is True
    assert ffd["is_conflict_free"] is True
    assert ffd["total_unallocated_count"] == 0
    total_allocated_sv = sum(
        s["total_students_allocated"] for s in ffd["shifts_allocation"].values()
    )
    assert total_allocated_sv == 300
    print(
        f"[PASS] Seeded 300-registration graph ({G.number_of_nodes()} nodes, "
        f"{G.number_of_edges()} edges) colored in {coloring['total_colors']} shifts "
        f"-> FFD allocated {total_allocated_sv}/300 SV with 0% conflicts."
    )


def main() -> int:
    test_seed_idempotency_and_counts()
    test_seeded_student_account()
    test_seeded_data_runs_graph_and_ffd_pipeline()
    print("ALL SEED TESTS PASSED!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
