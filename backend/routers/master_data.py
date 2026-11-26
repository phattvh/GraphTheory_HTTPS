"""API Routers cho Quản lý Dữ liệu Danh mục (TV2 - UC02, UC04).

Hiện thực Ngày 4: CRUD Kỳ thi (/api/v1/ky-thi) và Môn học (/api/v1/mon-hoc).
Tham chiếu: docs/04. Database design.md, docs/08. Implementation plan.md, docs/09. Project structure.md
"""

from typing import Annotated, Any, List, Optional, Type, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import get_current_user, require_admin
from backend.models.models import KyThi, MonHoc, NguoiDung
from backend.schemas.master_data import (
    ExamStatus,
    KyThiCreate,
    KyThiOut,
    KyThiUpdate,
    MAX_PG_BIGINT,
    MonHocCreate,
    MonHocOut,
    MonHocUpdate,
)

router = APIRouter(prefix="/api/v1")

ModelT = TypeVar("ModelT")
PositiveBigIntId = Annotated[int, Path(..., gt=0, le=MAX_PG_BIGINT)]
SkipParam = Annotated[int, Query(ge=0, le=100_000)]
LimitParam = Annotated[int, Query(ge=1, le=500)]


def _escape_like(keyword: str) -> str:
    """Escape ký tự wildcard SQL LIKE để tìm kiếm theo đúng chuỗi người dùng nhập."""
    return keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


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
    """Commit giao dịch CSDL, rollback và trả 409 nếu đụng ràng buộc UNIQUE đồng thời."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )


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
    if q is not None and q.strip():
        pattern = f"%{_escape_like(q.strip())}%"
        query = query.filter(
            or_(
                KyThi.ma_ky_thi.ilike(pattern, escape="\\"),
                KyThi.ten_ky_thi.ilike(pattern, escape="\\"),
            )
        )
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
    conflict_msg = f"Mã kỳ thi '{payload.ma_ky_thi}' đã tồn tại."
    _ensure_unique_value(db, KyThi, KyThi.ma_ky_thi, payload.ma_ky_thi, conflict_msg)

    exam = KyThi(**payload.model_dump())
    db.add(exam)
    _commit_or_409(db, conflict_msg)
    db.refresh(exam)
    return exam


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
    exam = _get_or_404(db, KyThi, ky_thi_id, "Không tìm thấy kỳ thi.")
    db.delete(exam)
    _commit_or_409(db, "Không thể xóa kỳ thi do ràng buộc dữ liệu liên quan.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
    query = db.query(MonHoc)
    if q is not None and q.strip():
        pattern = f"%{_escape_like(q.strip())}%"
        query = query.filter(
            or_(
                MonHoc.ma_mon.ilike(pattern, escape="\\"),
                MonHoc.ten_mon.ilike(pattern, escape="\\"),
            )
        )
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
    conflict_msg = f"Mã môn '{payload.ma_mon}' đã tồn tại."
    _ensure_unique_value(db, MonHoc, MonHoc.ma_mon, payload.ma_mon, conflict_msg)

    course = MonHoc(**payload.model_dump())
    db.add(course)
    _commit_or_409(db, conflict_msg)
    db.refresh(course)
    return course


@router.put("/mon-hoc/{mon_hoc_id}", response_model=MonHocOut, tags=["Môn học (UC04)"])
def update_mon_hoc(
    mon_hoc_id: PositiveBigIntId,
    payload: MonHocUpdate,
    _admin: NguoiDung = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Cập nhật thông tin môn học (chỉ admin)."""
    course = _get_or_404(db, MonHoc, mon_hoc_id, "Không tìm thấy môn học.")
    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(course, key, value)

    _commit_or_409(db, "Cập nhật môn học thất bại do xung đột dữ liệu.")
    db.refresh(course)
    return course


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
    course = _get_or_404(db, MonHoc, mon_hoc_id, "Không tìm thấy môn học.")
    db.delete(course)
    _commit_or_409(db, "Không thể xóa môn học do ràng buộc dữ liệu liên quan.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
