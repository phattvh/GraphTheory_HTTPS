"""API Routers cho Quản lý Dữ liệu Danh mục (TV2 - UC02, UC03, UC04, UC06).

Bao gồm:
- Ngày 4: Kỳ thi (/api/v1/ky-thi - UC02) & Môn học (/api/v1/mon-hoc - UC04)
- Ngày 5: Sinh viên (/api/v1/sinh-vien - UC03) & Phòng thi (/api/v1/phong-thi - UC06)

Tham chiếu: docs/04. Database design.md, docs/06. Security and authorization.md,
          docs/08. Implementation plan.md, docs/09. Project structure.md
"""

from typing import Annotated, Any, List, Optional, Type, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import get_current_user, require_admin
from backend.models.models import KyThi, MonHoc, NguoiDung, PhongThi, SinhVien
from backend.schemas.master_data import (
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
