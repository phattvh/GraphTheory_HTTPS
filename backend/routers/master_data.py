"""API Routers cho Quản lý Dữ liệu Danh mục & Đăng ký thi (TV2 - UC02 đến UC06).

Bao gồm:
- Ngày 4: Kỳ thi (/api/v1/ky-thi - UC02) & Môn học (/api/v1/mon-hoc - UC04)
- Ngày 5: Sinh viên (/api/v1/sinh-vien - UC03) & Phòng thi (/api/v1/phong-thi - UC06)
- Ngày 6: Đăng ký thi (/api/v1/dang-ky-thi & /api/v1/ky-thi/{ky_thi_id}/dang-ky-thi - UC05)

Tham chiếu: docs/04. Database design.md, docs/06. Security and authorization.md,
          docs/08. Implementation plan.md, docs/09. Project structure.md
"""

from typing import Annotated, Any, List, Optional, Type, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, contains_eager

from backend.core.database import get_db
from backend.core.security import get_current_user, require_admin
from backend.models.models import DangKyThi, KyThi, MonHoc, NguoiDung, PhongThi, SinhVien
from backend.schemas.master_data import (
    DangKyThiCreate,
    DangKyThiDetailOut,
    ExamStatus,
    KyThiCreate,
    KyThiOut,
    KyThiUpdate,
    MAX_PG_BIGINT,
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

router = APIRouter(prefix="/api/v1")

ModelT = TypeVar("ModelT")
PositiveBigIntId = Annotated[int, Path(..., gt=0, le=MAX_PG_BIGINT)]
PositiveBigIntQuery = Annotated[int, Query(gt=0, le=MAX_PG_BIGINT)]
SkipParam = Annotated[int, Query(ge=0, le=100_000)]
LimitParam = Annotated[int, Query(ge=1, le=500)]


def _escape_like(keyword: str) -> str:
    """Escape ký tự wildcard SQL LIKE để tìm kiếm theo đúng chuỗi người dùng nhập."""
    return keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _apply_text_search(query: Any, q: Optional[str], *columns: Any) -> Any:
    """Áp dụng bộ lọc ILIKE không phân biệt hoa thường trên nhiều cột nếu có từ khóa."""
    if q is not None and q.strip():
        pattern = f"%{_escape_like(q.strip())}%"
        query = query.filter(or_(*(col.ilike(pattern, escape="\\") for col in columns)))
    return query


def _get_or_404(
    db: Session, model: Type[ModelT], record_id: int, not_found_detail: str
) -> ModelT:
    """Lấy bản ghi theo khóa chính id hoặc trả về 404 Not Found."""
    record = db.query(model).filter(model.id == record_id).first()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found_detail,
        )
    return record


def _ensure_unique_value(
    db: Session, model: Type[Any], column: Any, value: Any, conflict_detail: str
) -> None:
    """Kiểm tra trùng mã nghiệp vụ trước khi chèn bản ghi mới."""
    exists = db.query(model.id).filter(column == value).first()
    if exists is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )


def _commit_or_409(db: Session, conflict_detail: str) -> None:
    """Commit giao dịch CSDL, rollback và trả 409 nếu đụng ràng buộc toàn vẹn."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )


def _create_unique_record(
    db: Session,
    model: Type[ModelT],
    payload: Any,
    unique_column: Any,
    unique_value: Any,
    conflict_detail: str,
) -> ModelT:
    """Kiểm tra trùng khóa duy nhất, chèn bản ghi mới và trả về đối tượng ORM đã làm mới."""
    _ensure_unique_value(db, model, unique_column, unique_value, conflict_detail)
    record = model(**payload.model_dump())
    db.add(record)
    _commit_or_409(db, conflict_detail)
    db.refresh(record)
    return record


def _update_record(
    db: Session,
    model: Type[ModelT],
    record_id: int,
    not_found_detail: str,
    payload: Any,
    conflict_detail: str,
) -> ModelT:
    """Cập nhật từng phần bản ghi theo payload (exclude_unset=True)."""
    record = _get_or_404(db, model, record_id, not_found_detail)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    _commit_or_409(db, conflict_detail)
    db.refresh(record)
    return record


def _delete_record(
    db: Session,
    model: Type[Any],
    record_id: int,
    not_found_detail: str,
    conflict_detail: str,
) -> Response:
    """Xóa bản ghi theo id, trả 204 No Content hoặc 409 nếu vướng ràng buộc khóa ngoại."""
    record = _get_or_404(db, model, record_id, not_found_detail)
    db.delete(record)
    _commit_or_409(db, conflict_detail)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _serialize_registration(reg: DangKyThi) -> DangKyThiDetailOut:
    """Chuyển ORM DangKyThi kèm quan hệ JOIN thành schema DangKyThiDetailOut."""
    return DangKyThiDetailOut(
        id=reg.id,
        ky_thi_id=reg.ky_thi_id,
        sinh_vien_id=reg.sinh_vien_id,
        mon_hoc_id=reg.mon_hoc_id,
        created_at=reg.created_at,
        ma_ky_thi=reg.ky_thi.ma_ky_thi if reg.ky_thi else None,
        ten_ky_thi=reg.ky_thi.ten_ky_thi if reg.ky_thi else None,
        mssv=reg.sinh_vien.mssv if reg.sinh_vien else None,
        ho_ten=reg.sinh_vien.ho_ten if reg.sinh_vien else None,
        lop_sinh_hoat=reg.sinh_vien.lop_sinh_hoat if reg.sinh_vien else None,
        ma_mon=reg.mon_hoc.ma_mon if reg.mon_hoc else None,
        ten_mon=reg.mon_hoc.ten_mon if reg.mon_hoc else None,
    )


def _query_registrations(
    db: Session,
    ky_thi_id: Optional[int],
    mon_hoc_id: Optional[int],
    sinh_vien_id: Optional[int],
    q: Optional[str],
    skip: int,
    limit: int,
) -> List[DangKyThiDetailOut]:
    """Truy vấn danh sách đăng ký thi bằng một câu JOIN duy nhất (không phát sinh N+1)."""
    query = (
        db.query(DangKyThi)
        .join(KyThi, DangKyThi.ky_thi_id == KyThi.id)
        .join(SinhVien, DangKyThi.sinh_vien_id == SinhVien.id)
        .join(MonHoc, DangKyThi.mon_hoc_id == MonHoc.id)
        .options(
            contains_eager(DangKyThi.ky_thi),
            contains_eager(DangKyThi.sinh_vien),
            contains_eager(DangKyThi.mon_hoc),
        )
    )
    if ky_thi_id is not None:
        query = query.filter(DangKyThi.ky_thi_id == ky_thi_id)
    if mon_hoc_id is not None:
        query = query.filter(DangKyThi.mon_hoc_id == mon_hoc_id)
    if sinh_vien_id is not None:
        query = query.filter(DangKyThi.sinh_vien_id == sinh_vien_id)
    query = _apply_text_search(
        query,
        q,
        KyThi.ma_ky_thi,
        SinhVien.mssv,
        SinhVien.ho_ten,
        SinhVien.lop_sinh_hoat,
        MonHoc.ma_mon,
        MonHoc.ten_mon,
    )
    records = (
        query.order_by(MonHoc.ma_mon.asc(), SinhVien.mssv.asc(), DangKyThi.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_serialize_registration(reg) for reg in records]


# ===========================================================================
# 1. QUẢN LÝ KỲ THI — /api/v1/ky-thi (UC02)
# ===========================================================================
@router.get("/ky-thi", response_model=List[KyThiOut], tags=["Kỳ thi (UC02)"])
def list_ky_thi(
    q: Optional[str] = Query(
        default=None, max_length=100, description="Tìm theo mã hoặc tên kỳ thi"
    ),
    trang_thai: Optional[ExamStatus] = Query(
        default=None, description="Lọc theo trạng thái kỳ thi"
    ),
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    current_user: NguoiDung = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lấy danh sách kỳ thi (admin xem toàn bộ; sinh_vien chỉ xem kỳ thi cong_bo)."""
    query = db.query(KyThi)
    if current_user.vai_tro != "admin":
        if trang_thai is not None and trang_thai != "cong_bo":
            return []
        query = query.filter(KyThi.trang_thai == "cong_bo")
    elif trang_thai is not None:
        query = query.filter(KyThi.trang_thai == trang_thai)
    query = _apply_text_search(query, q, KyThi.ma_ky_thi, KyThi.ten_ky_thi)
    return query.order_by(KyThi.id.desc()).offset(skip).limit(limit).all()


@router.get("/ky-thi/{ky_thi_id}", response_model=KyThiOut, tags=["Kỳ thi (UC02)"])
def get_ky_thi(
    ky_thi_id: PositiveBigIntId,
    current_user: NguoiDung = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lấy chi tiết một kỳ thi theo ID (sinh_vien chỉ được xem kỳ thi cong_bo)."""
    exam = _get_or_404(db, KyThi, ky_thi_id, "Không tìm thấy kỳ thi.")
    if current_user.vai_tro != "admin" and exam.trang_thai != "cong_bo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kỳ thi chưa được công bố.",
        )
    return exam


@router.post(
    "/ky-thi",
    response_model=KyThiOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Kỳ thi (UC02)"],
)
def create_ky_thi(
    payload: KyThiCreate,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Tạo mới một kỳ thi (chỉ admin)."""
    return _create_unique_record(
        db,
        KyThi,
        payload,
        KyThi.ma_ky_thi,
        payload.ma_ky_thi,
        f"Mã kỳ thi '{payload.ma_ky_thi}' đã tồn tại.",
    )


@router.put("/ky-thi/{ky_thi_id}", response_model=KyThiOut, tags=["Kỳ thi (UC02)"])
def update_ky_thi(
    ky_thi_id: PositiveBigIntId,
    payload: KyThiUpdate,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Cập nhật thông tin kỳ thi (chỉ admin)."""
    exam = _get_or_404(db, KyThi, ky_thi_id, "Không tìm thấy kỳ thi.")
    update_data = payload.model_dump(exclude_unset=True)

    # Đối chiếu chéo với ngày hiện có trong DB khi chỉ cập nhật một đầu ngày
    effective_start = update_data.get("ngay_bat_dau", exam.ngay_bat_dau)
    effective_end = update_data.get("ngay_ket_thuc", exam.ngay_ket_thuc)
    if effective_end < effective_start:
        raise HTTPException(
            status_code=422,
            detail="Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu.",
        )

    for key, value in update_data.items():
        setattr(exam, key, value)

    _commit_or_409(db, "Cập nhật kỳ thi thất bại do xung đột dữ liệu.")
    db.refresh(exam)
    return exam


@router.delete(
    "/ky-thi/{ky_thi_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Kỳ thi (UC02)"],
)
def delete_ky_thi(
    ky_thi_id: PositiveBigIntId,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Xóa kỳ thi (chỉ admin; CASCADE dọn sạch dang_ky_thi, ca_thi, lich_thi)."""
    return _delete_record(
        db,
        KyThi,
        ky_thi_id,
        "Không tìm thấy kỳ thi.",
        "Không thể xóa kỳ thi do ràng buộc dữ liệu liên quan.",
    )


# ===========================================================================
# 2. QUẢN LÝ MÔN HỌC / HỌC PHẦN — /api/v1/mon-hoc (UC04)
# ===========================================================================
@router.get("/mon-hoc", response_model=List[MonHocOut], tags=["Môn học (UC04)"])
def list_mon_hoc(
    q: Optional[str] = Query(
        default=None, max_length=100, description="Tìm theo mã môn hoặc tên môn"
    ),
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lấy danh sách môn học (chỉ admin)."""
    query = _apply_text_search(db.query(MonHoc), q, MonHoc.ma_mon, MonHoc.ten_mon)
    return (
        query.order_by(MonHoc.ma_mon.asc(), MonHoc.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/mon-hoc/{mon_hoc_id}", response_model=MonHocOut, tags=["Môn học (UC04)"])
def get_mon_hoc(
    mon_hoc_id: PositiveBigIntId,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lấy chi tiết một môn học theo ID (chỉ admin)."""
    return _get_or_404(db, MonHoc, mon_hoc_id, "Không tìm thấy môn học.")


@router.post(
    "/mon-hoc",
    response_model=MonHocOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Môn học (UC04)"],
)
def create_mon_hoc(
    payload: MonHocCreate,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Tạo mới một môn học / học phần (chỉ admin)."""
    return _create_unique_record(
        db,
        MonHoc,
        payload,
        MonHoc.ma_mon,
        payload.ma_mon,
        f"Mã môn '{payload.ma_mon}' đã tồn tại.",
    )


@router.put("/mon-hoc/{mon_hoc_id}", response_model=MonHocOut, tags=["Môn học (UC04)"])
def update_mon_hoc(
    mon_hoc_id: PositiveBigIntId,
    payload: MonHocUpdate,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Cập nhật thông tin môn học (chỉ admin)."""
    return _update_record(
        db,
        MonHoc,
        mon_hoc_id,
        "Không tìm thấy môn học.",
        payload,
        "Cập nhật môn học thất bại do xung đột dữ liệu.",
    )


@router.delete(
    "/mon-hoc/{mon_hoc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Môn học (UC04)"],
)
def delete_mon_hoc(
    mon_hoc_id: PositiveBigIntId,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Xóa môn học theo ID (chỉ admin)."""
    return _delete_record(
        db,
        MonHoc,
        mon_hoc_id,
        "Không tìm thấy môn học.",
        "Không thể xóa môn học do ràng buộc dữ liệu liên quan.",
    )


# ===========================================================================
# 3. QUẢN LÝ SINH VIÊN — /api/v1/sinh-vien (UC03 - Ngày 5)
# ===========================================================================
@router.get("/sinh-vien", response_model=List[SinhVienOut], tags=["Sinh viên (UC03)"])
def list_sinh_vien(
    q: Optional[str] = Query(
        default=None,
        max_length=100,
        description="Tìm theo MSSV, họ tên, email hoặc lớp sinh hoạt",
    ),
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lấy danh sách sinh viên (chỉ admin)."""
    query = _apply_text_search(
        db.query(SinhVien),
        q,
        SinhVien.mssv,
        SinhVien.ho_ten,
        SinhVien.email,
        SinhVien.lop_sinh_hoat,
    )
    return (
        query.order_by(SinhVien.mssv.asc(), SinhVien.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/sinh-vien/{sinh_vien_id}", response_model=SinhVienOut, tags=["Sinh viên (UC03)"]
)
def get_sinh_vien(
    sinh_vien_id: PositiveBigIntId,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lấy chi tiết một sinh viên theo ID (chỉ admin)."""
    return _get_or_404(db, SinhVien, sinh_vien_id, "Không tìm thấy sinh viên.")


@router.post(
    "/sinh-vien",
    response_model=SinhVienOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Sinh viên (UC03)"],
)
def create_sinh_vien(
    payload: SinhVienCreate,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Tạo mới một sinh viên (chỉ admin)."""
    return _create_unique_record(
        db,
        SinhVien,
        payload,
        SinhVien.mssv,
        payload.mssv,
        f"MSSV '{payload.mssv}' đã tồn tại.",
    )


@router.put(
    "/sinh-vien/{sinh_vien_id}", response_model=SinhVienOut, tags=["Sinh viên (UC03)"]
)
def update_sinh_vien(
    sinh_vien_id: PositiveBigIntId,
    payload: SinhVienUpdate,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Cập nhật thông tin sinh viên (chỉ admin)."""
    return _update_record(
        db,
        SinhVien,
        sinh_vien_id,
        "Không tìm thấy sinh viên.",
        payload,
        "Cập nhật sinh viên thất bại do xung đột dữ liệu.",
    )


@router.delete(
    "/sinh-vien/{sinh_vien_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Sinh viên (UC03)"],
)
def delete_sinh_vien(
    sinh_vien_id: PositiveBigIntId,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Xóa sinh viên theo ID (chỉ admin; trả 409 nếu còn tài khoản sinh viên gắn MSSV)."""
    return _delete_record(
        db,
        SinhVien,
        sinh_vien_id,
        "Không tìm thấy sinh viên.",
        "Không thể xóa sinh viên do còn tài khoản hoặc dữ liệu liên quan.",
    )


# ===========================================================================
# 4. QUẢN LÝ PHÒNG THI — /api/v1/phong-thi (UC06 - Ngày 5)
# ===========================================================================
@router.get("/phong-thi", response_model=List[PhongThiOut], tags=["Phòng thi (UC06)"])
def list_phong_thi(
    q: Optional[str] = Query(
        default=None, max_length=100, description="Tìm theo mã phòng, tên phòng hoặc tòa nhà"
    ),
    dang_su_dung: Optional[bool] = Query(
        default=None, description="Lọc theo trạng thái khả dụng của phòng"
    ),
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lấy danh sách phòng thi (chỉ admin)."""
    query = db.query(PhongThi)
    if dang_su_dung is not None:
        query = query.filter(PhongThi.dang_su_dung == dang_su_dung)
    query = _apply_text_search(
        query, q, PhongThi.ma_phong, PhongThi.ten_phong, PhongThi.toa_nha
    )
    return (
        query.order_by(PhongThi.ma_phong.asc(), PhongThi.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/phong-thi/{phong_thi_id}", response_model=PhongThiOut, tags=["Phòng thi (UC06)"]
)
def get_phong_thi(
    phong_thi_id: PositiveBigIntId,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lấy chi tiết một phòng thi theo ID (chỉ admin)."""
    return _get_or_404(db, PhongThi, phong_thi_id, "Không tìm thấy phòng thi.")


@router.post(
    "/phong-thi",
    response_model=PhongThiOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Phòng thi (UC06)"],
)
def create_phong_thi(
    payload: PhongThiCreate,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Tạo mới một phòng thi (chỉ admin)."""
    return _create_unique_record(
        db,
        PhongThi,
        payload,
        PhongThi.ma_phong,
        payload.ma_phong,
        f"Mã phòng '{payload.ma_phong}' đã tồn tại.",
    )


@router.put(
    "/phong-thi/{phong_thi_id}", response_model=PhongThiOut, tags=["Phòng thi (UC06)"]
)
def update_phong_thi(
    phong_thi_id: PositiveBigIntId,
    payload: PhongThiUpdate,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Cập nhật thông tin phòng thi (chỉ admin)."""
    return _update_record(
        db,
        PhongThi,
        phong_thi_id,
        "Không tìm thấy phòng thi.",
        payload,
        "Cập nhật phòng thi thất bại do xung đột dữ liệu.",
    )


@router.delete(
    "/phong-thi/{phong_thi_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Phòng thi (UC06)"],
)
def delete_phong_thi(
    phong_thi_id: PositiveBigIntId,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Xóa phòng thi theo ID (chỉ admin; trả 409 nếu phòng đang được gán trong lịch thi)."""
    return _delete_record(
        db,
        PhongThi,
        phong_thi_id,
        "Không tìm thấy phòng thi.",
        "Không thể xóa phòng thi đang được sử dụng trong lịch thi.",
    )


# ===========================================================================
# 5. QUẢN LÝ ĐĂNG KÝ THI — /api/v1/dang-ky-thi (UC05 - Ngày 6)
# ===========================================================================
@router.get(
    "/dang-ky-thi",
    response_model=List[DangKyThiDetailOut],
    tags=["Đăng ký thi (UC05)"],
)
def list_dang_ky_thi(
    ky_thi_id: Optional[PositiveBigIntQuery] = Query(
        default=None, description="Lọc danh sách đăng ký theo ID kỳ thi"
    ),
    mon_hoc_id: Optional[PositiveBigIntQuery] = Query(
        default=None, description="Lọc theo ID môn học"
    ),
    sinh_vien_id: Optional[PositiveBigIntQuery] = Query(
        default=None, description="Lọc theo ID sinh viên"
    ),
    q: Optional[str] = Query(
        default=None,
        max_length=100,
        description="Tìm theo mã kỳ thi, MSSV, họ tên, lớp, mã môn hoặc tên môn",
    ),
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lấy danh sách sinh viên đăng ký dự thi theo kỳ thi / môn học (chỉ admin)."""
    return _query_registrations(db, ky_thi_id, mon_hoc_id, sinh_vien_id, q, skip, limit)


@router.get(
    "/ky-thi/{ky_thi_id}/dang-ky-thi",
    response_model=List[DangKyThiDetailOut],
    tags=["Đăng ký thi (UC05)"],
)
def list_dang_ky_by_ky_thi(
    ky_thi_id: PositiveBigIntId,
    mon_hoc_id: Optional[PositiveBigIntQuery] = Query(
        default=None, description="Lọc theo ID môn học trong kỳ thi"
    ),
    sinh_vien_id: Optional[PositiveBigIntQuery] = Query(
        default=None, description="Lọc theo ID sinh viên trong kỳ thi"
    ),
    q: Optional[str] = Query(
        default=None,
        max_length=100,
        description="Tìm theo MSSV, họ tên, lớp, mã môn hoặc tên môn",
    ),
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lấy danh sách đăng ký thi của một kỳ thi cụ thể (chỉ admin)."""
    _get_or_404(db, KyThi, ky_thi_id, "Không tìm thấy kỳ thi.")
    return _query_registrations(db, ky_thi_id, mon_hoc_id, sinh_vien_id, q, skip, limit)


@router.get(
    "/dang-ky-thi/{dang_ky_id}",
    response_model=DangKyThiDetailOut,
    tags=["Đăng ký thi (UC05)"],
)
def get_dang_ky_thi(
    dang_ky_id: PositiveBigIntId,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lấy chi tiết một bản ghi đăng ký thi theo ID (chỉ admin)."""
    reg = (
        db.query(DangKyThi)
        .join(KyThi, DangKyThi.ky_thi_id == KyThi.id)
        .join(SinhVien, DangKyThi.sinh_vien_id == SinhVien.id)
        .join(MonHoc, DangKyThi.mon_hoc_id == MonHoc.id)
        .options(
            contains_eager(DangKyThi.ky_thi),
            contains_eager(DangKyThi.sinh_vien),
            contains_eager(DangKyThi.mon_hoc),
        )
        .filter(DangKyThi.id == dang_ky_id)
        .first()
    )
    if reg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy bản ghi đăng ký thi.",
        )
    return _serialize_registration(reg)


@router.post(
    "/dang-ky-thi",
    response_model=DangKyThiDetailOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Đăng ký thi (UC05)"],
)
def create_dang_ky_thi(
    payload: DangKyThiCreate,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Thêm sinh viên đăng ký môn thi trong kỳ thi (chỉ admin; chống đăng ký trùng)."""
    exam = _get_or_404(db, KyThi, payload.ky_thi_id, "Không tìm thấy kỳ thi.")
    student = _get_or_404(
        db, SinhVien, payload.sinh_vien_id, "Không tìm thấy sinh viên."
    )
    course = _get_or_404(db, MonHoc, payload.mon_hoc_id, "Không tìm thấy môn học.")

    conflict_msg = "Sinh viên đã đăng ký môn học này trong kỳ thi."
    duplicate = (
        db.query(DangKyThi.id)
        .filter(
            DangKyThi.ky_thi_id == payload.ky_thi_id,
            DangKyThi.sinh_vien_id == payload.sinh_vien_id,
            DangKyThi.mon_hoc_id == payload.mon_hoc_id,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_msg)

    reg = DangKyThi(**payload.model_dump())
    db.add(reg)
    _commit_or_409(db, conflict_msg)
    db.refresh(reg)
    reg.ky_thi = exam
    reg.sinh_vien = student
    reg.mon_hoc = course
    return _serialize_registration(reg)


@router.delete(
    "/dang-ky-thi/{dang_ky_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Đăng ký thi (UC05)"],
)
def delete_dang_ky_thi(
    dang_ky_id: PositiveBigIntId,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Xóa sinh viên khỏi danh sách đăng ký môn thi (chỉ admin)."""
    return _delete_record(
        db,
        DangKyThi,
        dang_ky_id,
        "Không tìm thấy bản ghi đăng ký thi.",
        "Không thể xóa bản ghi đăng ký thi.",
    )
