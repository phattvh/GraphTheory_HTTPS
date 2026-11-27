"""Kiểm thử tự động Ngày 3 (TV2): Models MonHoc, SinhVien, PhongThi & Pydantic v2 Schemas.

Chạy trong container fastapi:
    docker compose exec fastapi python tests/models_schemas_test.py
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError
from sqlalchemy import inspect, text

from backend.algorithms import (
    allocate_graph_schedule_rooms_ffd,
    allocate_graph_schedule_with_overflow,
    build_conflict_graph,
    dsatur_coloring,
    welsh_powell_coloring,
)
from backend.core.database import SessionLocal, engine
from backend.models import DangKyThi, KyThi, MonHoc, PhongThi, SinhVien
from backend.schemas import (
    DangKyThiCreate,
    KyThiCreate,
    KyThiUpdate,
    MonHocCreate,
    MonHocOut,
    MonHocUpdate,
    PhongThiCreate,
    PhongThiOut,
    PhongThiUpdate,
    SinhVienCreate,
    SinhVienOut,
    SinhVienUpdate,
)


def _assert_raises_validation_error(fn, label: str) -> None:
    try:
        fn()
    except ValidationError:
        return
    raise AssertionError(f"Expected ValidationError for: {label}")


def test_orm_columns_match_postgres_tables():
    """Đảm bảo các cột của MonHoc, SinhVien, PhongThi khớp 100% với bảng trong PostgreSQL."""
    inspector = inspect(engine)
    expected = {
        MonHoc: {"id", "ma_mon", "ten_mon", "thoi_luong_phut", "so_tin_chi"},
        SinhVien: {"id", "mssv", "ho_ten", "email", "lop_sinh_hoat"},
        PhongThi: {"id", "ma_phong", "ten_phong", "suc_chua", "toa_nha", "dang_su_dung"},
    }
    for model_cls, required_cols in expected.items():
        table_name = model_cls.__tablename__
        db_cols = {c["name"] for c in inspector.get_columns(table_name)}
        orm_cols = {c.name for c in model_cls.__table__.columns}
        assert required_cols.issubset(db_cols), f"Thiếu cột trong DB bảng {table_name}: {required_cols - db_cols}"
        assert orm_cols == required_cols, f"Model {model_cls.__name__} lệch cột: {orm_cols ^ required_cols}"
    print("✓ Test 1: Cột ORM của MonHoc, SinhVien, PhongThi khớp 100% với PostgreSQL.")


def test_schemas_validation_and_sanitization():
    """Kiểm tra validate, trim khoảng trắng và chặn giá trị biên không hợp lệ."""
    # MonHoc valid + trim
    mh_in = MonHocCreate(ma_mon="  IT3010  ", ten_mon="  Lý thuyết đồ thị  ")
    assert mh_in.ma_mon == "IT3010"
    assert mh_in.ten_mon == "Lý thuyết đồ thị"
    assert mh_in.thoi_luong_phut == 90
    assert mh_in.so_tin_chi == 3

    # MonHoc invalid cases
    _assert_raises_validation_error(lambda: MonHocCreate(ma_mon="   ", ten_mon="Môn"), "blank ma_mon")
    _assert_raises_validation_error(lambda: MonHocCreate(ma_mon="IT01", ten_mon="Môn", thoi_luong_phut=0), "thoi_luong_phut=0")
    _assert_raises_validation_error(lambda: MonHocCreate(ma_mon="IT01", ten_mon="Môn", so_tin_chi=-1), "so_tin_chi=-1")
    _assert_raises_validation_error(lambda: MonHocUpdate(ten_mon=None), "explicit null ten_mon in update")

    # SinhVien valid + blank optional normalization
    sv_in = SinhVienCreate(mssv=" 22110001 ", ho_ten=" Nguyễn Văn An ", email="   ", lop_sinh_hoat=" 22CNTT1 ")
    assert sv_in.mssv == "22110001"
    assert sv_in.ho_ten == "Nguyễn Văn An"
    assert sv_in.email is None
    assert sv_in.lop_sinh_hoat == "22CNTT1"

    _assert_raises_validation_error(lambda: SinhVienCreate(mssv="", ho_ten="An"), "empty mssv")
    _assert_raises_validation_error(lambda: SinhVienUpdate(ho_ten=None), "explicit null ho_ten in update")

    # PhongThi valid & invalid
    pt_in = PhongThiCreate(ma_phong=" TC-301 ", ten_phong=" Phòng TC 301 ", suc_chua=60, toa_nha="  ")
    assert pt_in.ma_phong == "TC-301"
    assert pt_in.toa_nha is None
    assert pt_in.dang_su_dung is True

    _assert_raises_validation_error(lambda: PhongThiCreate(ma_phong="P1", ten_phong="P1", suc_chua=0), "suc_chua=0")
    _assert_raises_validation_error(lambda: PhongThiUpdate(suc_chua=None), "explicit null suc_chua in update")
    _assert_raises_validation_error(lambda: PhongThiUpdate(dang_su_dung=None), "explicit null dang_su_dung in update")

    # KyThi date check & DangKyThi positive ids
    _assert_raises_validation_error(
        lambda: KyThiCreate(
            ma_ky_thi="KT1",
            ten_ky_thi="KT",
            ngay_bat_dau=date(2026, 6, 15),
            ngay_ket_thuc=date(2026, 6, 10),
        ),
        "ngay_ket_thuc < ngay_bat_dau",
    )
    _assert_raises_validation_error(
        lambda: KyThiUpdate(ngay_bat_dau=date(2026, 6, 15), ngay_ket_thuc=date(2026, 6, 10)),
        "KyThiUpdate date order",
    )
    _assert_raises_validation_error(
        lambda: DangKyThiCreate(ky_thi_id=0, sinh_vien_id=1, mon_hoc_id=1),
        "DangKyThi ky_thi_id=0",
    )

    # Edge cases: tràn số nguyên INT/BIGINT, ép kiểu bool->int, sai định dạng email, truyền thừa trường lạ
    _assert_raises_validation_error(
        lambda: PhongThiCreate(ma_phong="P_HUGE", ten_phong="Huge", suc_chua=10**12),
        "suc_chua overflow INT",
    )
    _assert_raises_validation_error(
        lambda: DangKyThiCreate(ky_thi_id=10**25, sinh_vien_id=1, mon_hoc_id=1),
        "ky_thi_id overflow BIGINT",
    )
    _assert_raises_validation_error(
        lambda: PhongThiCreate(ma_phong="P_BOOL", ten_phong="Bool", suc_chua=True),
        "bool as suc_chua",
    )
    _assert_raises_validation_error(
        lambda: MonHocCreate(ma_mon="IT02", ten_mon="Môn", thoi_luong_phut=True),
        "bool as thoi_luong_phut",
    )
    _assert_raises_validation_error(
        lambda: SinhVienCreate(mssv="22110002", ho_ten="An", email="not-an-email"),
        "invalid email format",
    )
    _assert_raises_validation_error(
        lambda: SinhVienUpdate(email="bad@@domain"),
        "invalid email in SinhVienUpdate",
    )
    _assert_raises_validation_error(
        lambda: MonHocUpdate(ma_mon="IMMUTABLE"),
        "extra forbidden field in MonHocUpdate",
    )
    _assert_raises_validation_error(
        lambda: PhongThiCreate(ma_phong="P2", ten_phong="P2", suc_chua=50, unknown_field=1),
        "extra forbidden field in PhongThiCreate",
    )
    print("✓ Test 2: Toàn bộ Pydantic v2 schemas validate chuẩn xác (hợp lệ & chặn lỗi).")


def test_orm_crud_and_pydantic_from_attributes():
    """Kiểm tra vòng đời ORM (Create -> Query -> Update -> Out serialization -> Cleanup) trên PostgreSQL."""
    db = SessionLocal()
    try:
        # 1. MonHoc
        mh_payload = MonHocCreate(
            ma_mon="TEST_D3_IT99",
            ten_mon="Môn kiểm thử Ngày 3",
            thoi_luong_phut=90,
            so_tin_chi=3,
        )
        mh_orm = MonHoc(**mh_payload.model_dump())
        db.add(mh_orm)
        db.flush()

        mh_upd = MonHocUpdate(thoi_luong_phut=120)
        for k, v in mh_upd.model_dump(exclude_unset=True).items():
            setattr(mh_orm, k, v)
        db.flush()
        mh_out = MonHocOut.model_validate(mh_orm)
        assert mh_out.id == mh_orm.id and mh_out.thoi_luong_phut == 120

        # 2. SinhVien
        sv_payload = SinhVienCreate(
            mssv="TESTD3_22119999",
            ho_ten="Sinh Viên Test Ngày 3",
            email="svtest@univ.edu.vn",
            lop_sinh_hoat="22CNTT-TEST",
        )
        sv_orm = SinhVien(**sv_payload.model_dump())
        db.add(sv_orm)
        db.flush()

        sv_upd = SinhVienUpdate(lop_sinh_hoat="22CNTT-UPDATED")
        for k, v in sv_upd.model_dump(exclude_unset=True).items():
            setattr(sv_orm, k, v)
        db.flush()
        sv_out = SinhVienOut.model_validate(sv_orm)
        assert sv_out.id == sv_orm.id and sv_out.lop_sinh_hoat == "22CNTT-UPDATED"

        # 3. PhongThi
        pt_payload = PhongThiCreate(
            ma_phong="TEST_D3_P999",
            ten_phong="Phòng thi Test Ngày 3",
            suc_chua=75,
            toa_nha="Nhà Test",
            dang_su_dung=True,
        )
        pt_orm = PhongThi(**pt_payload.model_dump())
        db.add(pt_orm)
        db.flush()

        pt_upd = PhongThiUpdate(suc_chua=80, dang_su_dung=False)
        for k, v in pt_upd.model_dump(exclude_unset=True).items():
            setattr(pt_orm, k, v)
        db.flush()
        pt_out = PhongThiOut.model_validate(pt_orm)
        assert pt_out.id == pt_orm.id and pt_out.suc_chua == 80 and pt_out.dang_su_dung is False

        # Rollback để không làm bẩn CSDL thật
        db.rollback()
        print("✓ Test 3: ORM <-> Pydantic Out (from_attributes=True) và giao dịch Postgres pass 100%.")
    finally:
        db.close()


def test_dang_ky_thi_self_join_and_algorithm_pipeline():
    """Kiểm chứng dữ liệu DangKyThi trong Postgres kết nối trơn tru với Graph Builder, DSatur, Welsh-Powell, FFD & Overflow."""
    db = SessionLocal()
    try:
        exam = KyThi(
            ma_ky_thi="KT_PIPE_D6",
            ten_ky_thi="Kỳ thi kiểm chứng Pipeline Đồ thị",
            ngay_bat_dau=date(2026, 9, 1),
            ngay_ket_thuc=date(2026, 9, 10),
        )
        m1 = MonHoc(ma_mon="PIPE_M1", ten_mon="Môn 1", thoi_luong_phut=90, so_tin_chi=3)
        m2 = MonHoc(ma_mon="PIPE_M2", ten_mon="Môn 2", thoi_luong_phut=90, so_tin_chi=3)
        m3 = MonHoc(ma_mon="PIPE_M3", ten_mon="Môn 3", thoi_luong_phut=90, so_tin_chi=3)
        sv1 = SinhVien(mssv="PIPE_SV1", ho_ten="SV 1")
        sv2 = SinhVien(mssv="PIPE_SV2", ho_ten="SV 2")
        sv3 = SinhVien(mssv="PIPE_SV3", ho_ten="SV 3")
        p1 = PhongThi(ma_phong="PIPE_P1", ten_phong="Phòng 1", suc_chua=50, dang_su_dung=True)
        p2 = PhongThi(ma_phong="PIPE_P2", ten_phong="Phòng 2", suc_chua=30, dang_su_dung=True)

        db.add_all([exam, m1, m2, m3, sv1, sv2, sv3, p1, p2])
        db.flush()

        # SV1: M1, M2, M3 (tam giác xung đột K3)
        # SV2: M1, M2 (tăng trọng số cạnh (M1, M2) lên 2)
        # SV3: M2 (M2 có 3 SV, M1 có 2 SV, M3 có 1 SV)
        regs = [
            DangKyThi(ky_thi_id=exam.id, sinh_vien_id=sv1.id, mon_hoc_id=m1.id),
            DangKyThi(ky_thi_id=exam.id, sinh_vien_id=sv1.id, mon_hoc_id=m2.id),
            DangKyThi(ky_thi_id=exam.id, sinh_vien_id=sv1.id, mon_hoc_id=m3.id),
            DangKyThi(ky_thi_id=exam.id, sinh_vien_id=sv2.id, mon_hoc_id=m1.id),
            DangKyThi(ky_thi_id=exam.id, sinh_vien_id=sv2.id, mon_hoc_id=m2.id),
            DangKyThi(ky_thi_id=exam.id, sinh_vien_id=sv3.id, mon_hoc_id=m2.id),
        ]
        db.add_all(regs)
        db.flush()

        # 1. Truy vấn Self-Join trực tiếp trên Postgres để đối chiếu trọng số xung đột
        edge_rows = db.execute(
            text(
                """
                SELECT m1.ma_mon, m2.ma_mon, COUNT(*) AS trong_so
                FROM dang_ky_thi dk1
                JOIN dang_ky_thi dk2
                  ON dk1.ky_thi_id = dk2.ky_thi_id
                 AND dk1.sinh_vien_id = dk2.sinh_vien_id
                 AND dk1.mon_hoc_id < dk2.mon_hoc_id
                JOIN mon_hoc m1 ON dk1.mon_hoc_id = m1.id
                JOIN mon_hoc m2 ON dk2.mon_hoc_id = m2.id
                WHERE dk1.ky_thi_id = :ky_thi_id
                GROUP BY m1.ma_mon, m2.ma_mon
                ORDER BY m1.ma_mon, m2.ma_mon
                """
            ),
            {"ky_thi_id": exam.id},
        ).fetchall()
        weights = {tuple(sorted((r[0], r[1]))): r[2] for r in edge_rows}
        assert weights == {
            ("PIPE_M1", "PIPE_M2"): 2,
            ("PIPE_M1", "PIPE_M3"): 1,
            ("PIPE_M2", "PIPE_M3"): 1,
        }, f"Self-Join weights mismatch: {weights}"

        # 2. Đưa danh sách đăng ký vào build_conflict_graph -> DSatur / Welsh-Powell -> FFD & Overflow
        reg_dicts = [
            {"mssv": sv1.mssv, "ma_mon": m1.ma_mon},
            {"mssv": sv1.mssv, "ma_mon": m2.ma_mon},
            {"mssv": sv1.mssv, "ma_mon": m3.ma_mon},
            {"mssv": sv2.mssv, "ma_mon": m1.ma_mon},
            {"mssv": sv2.mssv, "ma_mon": m2.ma_mon},
            {"mssv": sv3.mssv, "ma_mon": m2.ma_mon},
        ]
        G = build_conflict_graph(reg_dicts)
        assert G.number_of_nodes() == 3 and G.number_of_edges() == 3
        assert G["PIPE_M1"]["PIPE_M2"]["weight"] == 2
        assert G.nodes["PIPE_M2"]["size"] == 3

        dsatur_res = dsatur_coloring(G)
        wp_res = welsh_powell_coloring(G)
        # Đồ thị đầy đủ K3 bắt buộc sắc số = 3 và 0% xung đột ở cả hai thuật toán
        assert dsatur_res["total_colors"] == 3 and dsatur_res["is_valid"] and dsatur_res["conflicts_count"] == 0
        assert wp_res["total_colors"] == 3 and wp_res["is_valid"] and wp_res["conflicts_count"] == 0

        rooms = [
            {"ma_phong": p1.ma_phong, "ten_phong": p1.ten_phong, "suc_chua": p1.suc_chua, "dang_su_dung": True},
            {"ma_phong": p2.ma_phong, "ten_phong": p2.ten_phong, "suc_chua": p2.suc_chua, "dang_su_dung": True},
        ]
        ffd_res = allocate_graph_schedule_rooms_ffd(G, dsatur_res["color_map"], rooms)
        assert ffd_res["is_all_successful"] is True
        assert ffd_res["total_shifts"] == 3
        assert ffd_res["total_courses"] == 3
        assert ffd_res["total_allocations_count"] == 3
        assert ffd_res["total_unallocated_count"] == 0

        overflow_res = allocate_graph_schedule_with_overflow(
            G=G,
            color_map=dsatur_res["color_map"],
            rooms=rooms,
            allow_room_splitting=True,
            allow_shift_spilling=True,
        )
        assert overflow_res["is_all_successful"] is True
        assert overflow_res["is_conflict_free"] is True
        assert overflow_res["total_unallocated_count"] == 0

        db.rollback()
        print("✓ Test 4: DangKyThi Self-Join Postgres -> Graph Builder -> DSatur/Welsh-Powell -> FFD & Overflow pass 100%.")
    finally:
        db.close()


def test_orm_check_constraints_and_transactional_scope():
    """Đảm bảo 12 CheckConstraint trong ORM khớp 100% init.sql và transactional_scope rollback nguyên tử."""
    from sqlalchemy import CheckConstraint
    from backend.core.database import Base
    from backend.services import transactional_scope

    expected_checks = {
        "ck_nguoi_dung_vai_tro",
        "ck_sv_co_mssv",
        "ck_ky_thi_ngay",
        "ck_ky_thi_so_ca",
        "ck_ky_thi_trang_thai",
        "ck_mon_hoc_thoi_luong",
        "ck_mon_hoc_tin_chi",
        "ck_phong_thi_suc_chua",
        "ck_ca_thi_stt",
        "ck_ca_thi_gio",
        "ck_ca_thi_thuat_toan",
        "ck_lich_thi_so_luong",
    }
    orm_checks = {
        constraint.name
        for table in Base.metadata.tables.values()
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint) and constraint.name
    }
    assert expected_checks.issubset(orm_checks), (
        f"Thiếu CheckConstraint trong Base.metadata: {expected_checks - orm_checks}"
    )

    # Kiểm chứng transactional_scope tự động rollback khi xảy ra ngoại lệ giữa chừng
    probe_code = "MH_TX_ROLLBACK_PROBE"
    db = SessionLocal()
    try:
        db.query(MonHoc).filter(MonHoc.ma_mon == probe_code).delete()
        db.commit()

        try:
            with transactional_scope(db):
                db.add(MonHoc(ma_mon=probe_code, ten_mon="Probe Rollback", thoi_luong_phut=90))
                db.flush()
                raise RuntimeError("Giả lập lỗi giữa pipeline để kiểm tra rollback")
        except RuntimeError:
            pass

        leaked = db.query(MonHoc).filter(MonHoc.ma_mon == probe_code).first()
        assert leaked is None, "transactional_scope phải rollback sạch bản ghi dở dang khi có lỗi"
        print("✓ Test 5: 12 CheckConstraint ORM & backend.services.transactional_scope đạt 100%.")
    finally:
        db.close()


if __name__ == "__main__":
    print("=== BẮT ĐẦU KIỂM THỬ NGÀY 3-6 (TV2: Models, Schemas & Graph Pipeline) ===")
    try:
        test_orm_columns_match_postgres_tables()
        test_schemas_validation_and_sanitization()
        test_orm_crud_and_pydantic_from_attributes()
        test_dang_ky_thi_self_join_and_algorithm_pipeline()
        test_orm_check_constraints_and_transactional_scope()
        print("=== TẤT CẢ CÁC BƯỚC KIỂM THỬ MODELS, SCHEMAS & PIPELINE ĐÃ ĐẠT 100% ===")
    except AssertionError as err:
        print(f"✗ LỖI KIỂM THỬ: {err}")
        sys.exit(1)
    except Exception as exc:
        print(f"✗ LỖI KHÔNG MONG MUỐN: {exc}")
        sys.exit(1)
