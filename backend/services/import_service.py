"""Dịch vụ đọc và kiểm tra dữ liệu nhập hàng loạt từ CSV/Excel (UC07 - Ngày 8).

Phụ trách: TV2 (Backend: CSDL & Dữ liệu đầu vào)
Tham chiếu: docs/06. Security and authorization.md & docs/08. Implementation plan.md
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, datetime
import io
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Optional
from zipfile import BadZipFile

from fastapi import UploadFile
import multipart  # noqa: F401 - bảo đảm python-multipart sẵn sàng cho UploadFile
import openpyxl
from openpyxl.utils.exceptions import InvalidFileException
from pydantic import BaseModel, ConfigDict, StringConstraints, ValidationError
from typing_extensions import Annotated

from backend.schemas.master_data import (
    KyThiCreate,
    MonHocCreate,
    PhongThiCreate,
    SinhVienCreate,
)

MAX_IMPORT_FILE_BYTES = 5 * 1024 * 1024  # 5 MB theo chuẩn OWASP A04 Upload Abuse
UPLOAD_READ_CHUNK_BYTES = 64 * 1024
MAX_IMPORT_ROWS = 50_000
ALLOWED_IMPORT_EXTENSIONS = (".csv", ".xlsx")

ImportEntity = Literal["ky_thi", "mon_hoc", "sinh_vien", "phong_thi", "dang_ky_thi"]
ImportFormat = Literal["csv", "xlsx"]


class DangKyThiImportRow(BaseModel):
    """Schema kiểm tra từng dòng import Đăng ký thi theo khóa nghiệp vụ."""

    model_config = ConfigDict(extra="forbid")

    ma_ky_thi: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
    ma_mon: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
    mssv: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]


@dataclass(frozen=True)
class EntityImportSpec:
    """Định nghĩa cấu trúc cột, schema Pydantic và khóa duy nhất trong tệp cho từng thực thể."""

    entity: ImportEntity
    label: str
    schema: type[BaseModel]
    allowed_headers: tuple[str, ...]
    required_headers: tuple[str, ...]
    string_fields: frozenset[str] = frozenset()
    int_fields: frozenset[str] = frozenset()
    defaulted_int_fields: frozenset[str] = frozenset()
    date_fields: frozenset[str] = frozenset()
    bool_fields: frozenset[str] = frozenset()
    unique_key_fn: Optional[Callable[[BaseModel], tuple[Any, ...]]] = None


def _entity_specs() -> dict[ImportEntity, EntityImportSpec]:
    """Khởi tạo bảng đặc tả cột cho 5 thực thể hỗ trợ import."""
    return {
        "ky_thi": EntityImportSpec(
            entity="ky_thi",
            label="Kỳ thi",
            schema=KyThiCreate,
            allowed_headers=(
                "ma_ky_thi",
                "ten_ky_thi",
                "ngay_bat_dau",
                "ngay_ket_thuc",
                "so_ca_moi_ngay",
                "trang_thai",
            ),
            required_headers=("ma_ky_thi", "ten_ky_thi", "ngay_bat_dau", "ngay_ket_thuc"),
            string_fields=frozenset({"ma_ky_thi", "ten_ky_thi", "trang_thai"}),
            int_fields=frozenset({"so_ca_moi_ngay"}),
            defaulted_int_fields=frozenset({"so_ca_moi_ngay"}),
            date_fields=frozenset({"ngay_bat_dau", "ngay_ket_thuc"}),
            unique_key_fn=lambda r: (r.ma_ky_thi,),
        ),
        "mon_hoc": EntityImportSpec(
            entity="mon_hoc",
            label="Môn học",
            schema=MonHocCreate,
            allowed_headers=("ma_mon", "ten_mon", "thoi_luong_phut", "so_tin_chi"),
            required_headers=("ma_mon", "ten_mon"),
            string_fields=frozenset({"ma_mon", "ten_mon"}),
            int_fields=frozenset({"thoi_luong_phut", "so_tin_chi"}),
            defaulted_int_fields=frozenset({"thoi_luong_phut", "so_tin_chi"}),
            unique_key_fn=lambda r: (r.ma_mon,),
        ),
        "sinh_vien": EntityImportSpec(
            entity="sinh_vien",
            label="Sinh viên",
            schema=SinhVienCreate,
            allowed_headers=("mssv", "ho_ten", "email", "lop_sinh_hoat"),
            required_headers=("mssv", "ho_ten"),
            string_fields=frozenset({"mssv", "ho_ten", "email", "lop_sinh_hoat"}),
            unique_key_fn=lambda r: (r.mssv,),
        ),
        "phong_thi": EntityImportSpec(
            entity="phong_thi",
            label="Phòng thi",
            schema=PhongThiCreate,
            allowed_headers=("ma_phong", "ten_phong", "suc_chua", "toa_nha", "dang_su_dung"),
            required_headers=("ma_phong", "ten_phong", "suc_chua"),
            string_fields=frozenset({"ma_phong", "ten_phong", "toa_nha"}),
            int_fields=frozenset({"suc_chua"}),
            bool_fields=frozenset({"dang_su_dung"}),
            unique_key_fn=lambda r: (r.ma_phong,),
        ),
        "dang_ky_thi": EntityImportSpec(
            entity="dang_ky_thi",
            label="Đăng ký thi",
            schema=DangKyThiImportRow,
            allowed_headers=("ma_ky_thi", "ma_mon", "mssv"),
            required_headers=("ma_ky_thi", "ma_mon", "mssv"),
            string_fields=frozenset({"ma_ky_thi", "ma_mon", "mssv"}),
            unique_key_fn=lambda r: (r.ma_ky_thi, r.ma_mon, r.mssv),
        ),
    }


ENTITY_IMPORT_SPECS: dict[ImportEntity, EntityImportSpec] = _entity_specs()


@dataclass(frozen=True)
class ImportRowError:
    """Mô tả lỗi kiểm tra dữ liệu tại một dòng cụ thể trong tệp."""

    row_number: int
    messages: list[str]

    def format_message(self) -> str:
        return f"Dòng {self.row_number}: {'; '.join(self.messages)}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "row": self.row_number,
            "errors": list(self.messages),
            "message": self.format_message(),
        }


class ImportValidationError(ValueError):
    """Ngoại lệ khi tệp import sai định dạng, vượt dung lượng, sai cột hoặc chứa dòng lỗi."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        row_errors: Optional[list[ImportRowError]] = None,
    ) -> None:
        super().__init__(message)
        self.detail = message
        self.status_code = status_code
        self.row_errors = list(row_errors or [])

    def to_detail_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"message": self.detail}
        if self.row_errors:
            payload["errors"] = [err.to_dict() for err in self.row_errors]
        return payload


@dataclass
class ImportParseResult:
    """Kết quả đọc và validate từng dòng dữ liệu CSV/Excel."""

    entity: ImportEntity
    file_format: ImportFormat
    filename: str
    headers: list[str]
    total_rows: int
    records: list[BaseModel] = field(default_factory=list)
    errors: list[ImportRowError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def valid_count(self) -> int:
        return len(self.records)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def raise_for_errors(self) -> None:
        """Ném ImportValidationError (HTTP 422) nếu tồn tại ít nhất một dòng dữ liệu lỗi."""
        if self.errors:
            preview = " | ".join(err.format_message() for err in self.errors[:5])
            suffix = f" (và {len(self.errors) - 5} dòng lỗi khác)" if len(self.errors) > 5 else ""
            raise ImportValidationError(
                f"Dữ liệu {ENTITY_IMPORT_SPECS[self.entity].label} có {len(self.errors)} dòng không hợp lệ: {preview}{suffix}",
                status_code=422,
                row_errors=self.errors,
            )

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "entity": self.entity,
            "file_format": self.file_format,
            "filename": self.filename,
            "headers": list(self.headers),
            "total_rows": self.total_rows,
            "valid_count": self.valid_count,
            "error_count": self.error_count,
            "is_valid": self.is_valid,
            "errors": [err.to_dict() for err in self.errors],
        }


def get_entity_spec(entity: str) -> EntityImportSpec:
    """Lấy đặc tả import theo tên thực thể; báo lỗi rõ ràng nếu thực thể không được hỗ trợ."""
    normalized = (entity or "").strip().lower()
    if normalized not in ENTITY_IMPORT_SPECS:
        supported = ", ".join(ENTITY_IMPORT_SPECS.keys())
        raise ImportValidationError(
            f"Thực thể '{entity}' không được hỗ trợ import. Hợp lệ: {supported}.",
            status_code=400,
        )
    return ENTITY_IMPORT_SPECS[normalized]  # type: ignore[index]


def detect_import_format(filename: Optional[str]) -> ImportFormat:
    """Kiểm tra phần mở rộng tệp upload theo allowlist .csv / .xlsx."""
    clean_name = (filename or "").strip()
    if not clean_name:
        raise ImportValidationError("Thiếu tên tệp upload.", status_code=400)

    suffix = Path(clean_name).suffix.lower()
    if suffix not in ALLOWED_IMPORT_EXTENSIONS:
        raise ImportValidationError(
            f"Chỉ hỗ trợ định dạng tệp {', '.join(ALLOWED_IMPORT_EXTENSIONS)} (đã nhận '{suffix or 'không có phần mở rộng'}').",
            status_code=400,
        )
    return "csv" if suffix == ".csv" else "xlsx"


def validate_file_size(content: bytes) -> None:
    """Chặn tệp rỗng hoặc vượt ngưỡng 5 MB."""
    if not content:
        raise ImportValidationError("Tệp tải lên đang rỗng.", status_code=400)
    if len(content) > MAX_IMPORT_FILE_BYTES:
        raise ImportValidationError(
            f"Dung lượng tệp vượt quá giới hạn tối đa {MAX_IMPORT_FILE_BYTES // (1024 * 1024)} MB.",
            status_code=413,
        )


def _is_blank_cell(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def _is_blank_row(row: Iterable[Any]) -> bool:
    return all(_is_blank_cell(cell) for cell in row)


def _read_csv_rows(content: bytes) -> list[list[Any]]:
    """Đọc toàn bộ dòng từ bytes CSV (hỗ trợ UTF-8 BOM từ Excel)."""
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ImportValidationError(
            "Tệp CSV phải được mã hóa chuẩn UTF-8 (hoặc UTF-8 BOM).",
            status_code=400,
        ) from exc

    reader = csv.reader(io.StringIO(text, newline=""))
    rows: list[list[Any]] = []
    for index, row in enumerate(reader, start=1):
        if index > MAX_IMPORT_ROWS + 1:
            raise ImportValidationError(
                f"Số dòng dữ liệu vượt quá giới hạn cho phép ({MAX_IMPORT_ROWS} dòng).",
                status_code=400,
            )
        rows.append(row)
    return rows


def _read_xlsx_rows(content: bytes) -> list[list[Any]]:
    """Đọc sheet đầu tiên từ tệp Excel .xlsx ở chế độ chỉ đọc an toàn."""
    workbook = None
    try:
        workbook = openpyxl.load_workbook(
            io.BytesIO(content),
            read_only=True,
            data_only=True,
        )
        sheet = workbook.active
        if sheet is None:
            raise ImportValidationError("Tệp Excel không có trang tính (worksheet) nào.", status_code=400)

        rows: list[list[Any]] = []
        for index, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            if index > MAX_IMPORT_ROWS + 1:
                raise ImportValidationError(
                    f"Số dòng dữ liệu vượt quá giới hạn cho phép ({MAX_IMPORT_ROWS} dòng).",
                    status_code=400,
                )
            rows.append(list(row))
        return rows
    except ImportValidationError:
        raise
    except (InvalidFileException, BadZipFile, KeyError, ValueError, OSError) as exc:
        raise ImportValidationError(
            "Tệp Excel (.xlsx) không hợp lệ hoặc bị hỏng cấu trúc.",
            status_code=400,
        ) from exc
    finally:
        if workbook is not None:
            workbook.close()


def _extract_and_validate_headers(raw_header_row: list[Any], spec: EntityImportSpec) -> list[str]:
    """Chuẩn hóa và kiểm tra cấu trúc cột tiêu đề ở dòng 1."""
    trimmed = list(raw_header_row)
    while trimmed and _is_blank_cell(trimmed[-1]):
        trimmed.pop()

    if not trimmed:
        raise ImportValidationError("Thiếu dòng tiêu đề cột ở dòng 1.", status_code=400)

    normalized_headers: list[str] = []
    seen: set[str] = set()
    duplicates: list[str] = []

    for col_idx, raw_cell in enumerate(trimmed, start=1):
        if _is_blank_cell(raw_cell):
            raise ImportValidationError(
                f"Tên cột tiêu đề ở vị trí thứ {col_idx} đang bị trống.",
                status_code=400,
            )
        col_name = str(raw_cell).strip().lower()
        if col_name in seen and col_name not in duplicates:
            duplicates.append(col_name)
        seen.add(col_name)
        normalized_headers.append(col_name)

    if duplicates:
        raise ImportValidationError(
            f"Cột tiêu đề bị trùng lặp: {', '.join(duplicates)}.",
            status_code=400,
        )

    allowed_set = set(spec.allowed_headers)
    unknown = [col for col in normalized_headers if col not in allowed_set]
    if unknown:
        raise ImportValidationError(
            f"Cột không hợp lệ cho {spec.label}: {', '.join(unknown)}. Các cột cho phép: {', '.join(spec.allowed_headers)}.",
            status_code=400,
        )

    missing = [req for req in spec.required_headers if req not in seen]
    if missing:
        raise ImportValidationError(
            f"Thiếu cột bắt buộc cho {spec.label}: {', '.join(missing)}.",
            status_code=400,
        )

    return normalized_headers


def _coerce_string_cell(raw_value: Any) -> Any:
    """Chuẩn hóa giá trị ô dạng chuỗi (kể cả mã số do Excel tự ép sang int/float)."""
    if raw_value is None:
        return None
    if isinstance(raw_value, bool):
        return raw_value  # Để Pydantic từ chối boolean truyền nhầm vào trường chuỗi
    if isinstance(raw_value, int):
        return str(raw_value)
    if isinstance(raw_value, float):
        return str(int(raw_value)) if raw_value.is_integer() else str(raw_value)
    if isinstance(raw_value, str):
        return raw_value.strip()
    return raw_value


def _coerce_int_cell(raw_value: Any) -> Any:
    """Chuẩn hóa ô số nguyên: giữ nguyên bool/số lẻ để Pydantic bắt lỗi chính xác."""
    if raw_value is None:
        return None
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, int):
        return raw_value
    if isinstance(raw_value, float):
        return int(raw_value) if raw_value.is_integer() else raw_value
    if isinstance(raw_value, str):
        stripped = raw_value.strip()
        if stripped == "":
            return None
        return stripped
    return raw_value


def _coerce_date_cell(raw_value: Any) -> Any:
    """Chuẩn hóa ô ngày: nhận đối tượng date/datetime từ Excel hoặc chuỗi ISO YYYY-MM-DD."""
    if isinstance(raw_value, datetime):
        return raw_value.date()
    if isinstance(raw_value, date):
        return raw_value
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, (int, float)):
        raise ValueError("Ngày phải ở định dạng YYYY-MM-DD hoặc ô ngày Excel hợp lệ.")
    if isinstance(raw_value, str):
        stripped = raw_value.strip()
        if not stripped:
            return None
        try:
            return date.fromisoformat(stripped)
        except ValueError as exc:
            raise ValueError("Ngày phải theo đúng định dạng YYYY-MM-DD.") from exc
    return raw_value


def _coerce_bool_cell(raw_value: Any) -> Any:
    """Chuẩn hóa ô boolean: true/false/1/0 hoặc để None nếu rỗng."""
    if raw_value is None:
        return None
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, int):
        if raw_value in (0, 1):
            return bool(raw_value)
        return raw_value
    if isinstance(raw_value, float):
        if raw_value in (0.0, 1.0):
            return bool(int(raw_value))
        return raw_value
    if isinstance(raw_value, str):
        lowered = raw_value.strip().lower()
        if lowered == "":
            return None
        if lowered in ("true", "1", "yes"):
            return True
        if lowered in ("false", "0", "no"):
            return False
        return raw_value.strip()
    return raw_value


def _build_row_payload(
    headers: list[str],
    raw_row: list[Any],
    spec: EntityImportSpec,
) -> tuple[dict[str, Any], list[str]]:
    """Ánh xạ một dòng thô thành dict theo header và thu thập lỗi tiền xử lý (nếu có)."""
    payload: dict[str, Any] = {}
    pre_errors: list[str] = []

    if len(raw_row) > len(headers) and any(not _is_blank_cell(cell) for cell in raw_row[len(headers) :]):
        pre_errors.append(
            f"Có dữ liệu dư thừa ngoài {len(headers)} cột tiêu đề đã khai báo."
        )

    for col_idx, field_name in enumerate(headers):
        raw_val = raw_row[col_idx] if col_idx < len(raw_row) else None

        if field_name in spec.date_fields:
            try:
                coerced = _coerce_date_cell(raw_val)
            except ValueError as exc:
                pre_errors.append(f"{field_name}: {exc}")
                continue
            payload[field_name] = coerced
        elif field_name in spec.int_fields:
            coerced = _coerce_int_cell(raw_val)
            if coerced is None and field_name in spec.defaulted_int_fields:
                continue  # Dùng giá trị mặc định khai báo trên Pydantic schema
            payload[field_name] = coerced
        elif field_name in spec.bool_fields:
            coerced = _coerce_bool_cell(raw_val)
            if coerced is None and field_name == "dang_su_dung":
                continue  # Mặc định True khi bỏ trống trong CSV/Excel
            payload[field_name] = coerced
        elif field_name in spec.string_fields:
            coerced = _coerce_string_cell(raw_val)
            # Khi ô string bị bỏ trống nhưng đây là trường tùy chọn (vd: trang_thai mặc định)
            if field_name == "trang_thai" and (coerced is None or coerced == ""):
                continue
            payload[field_name] = coerced
        else:
            payload[field_name] = raw_val

    return payload, pre_errors


def _format_pydantic_error(exc: ValidationError) -> list[str]:
    """Chuyển danh sách lỗi Pydantic ValidationError thành thông báo gọn, rõ tên trường."""
    messages: list[str] = []
    for err in exc.errors():
        loc_parts = [str(part) for part in err.get("loc", ()) if part != "__root__"]
        field_prefix = f"{'.'.join(loc_parts)}: " if loc_parts else ""
        msg = err.get("msg", "Dữ liệu không hợp lệ")
        messages.append(f"{field_prefix}{msg}")
    return messages


def parse_import_bytes(
    entity: str,
    content: bytes,
    filename: str,
    *,
    raise_on_row_errors: bool = False,
) -> ImportParseResult:
    """Đọc bytes CSV/Excel, kiểm tra cấu trúc cột và validate từng dòng bằng Pydantic v2.

    Tham số:
        entity: Tên thực thể ('ky_thi', 'mon_hoc', 'sinh_vien', 'phong_thi', 'dang_ky_thi').
        content: Nội dung nhị phân của tệp đã tải lên.
        filename: Tên tệp gốc dùng để xác định định dạng .csv / .xlsx.
        raise_on_row_errors: Nếu True, tự động ném ImportValidationError (422) khi có dòng lỗi.
    """
    spec = get_entity_spec(entity)
    file_format = detect_import_format(filename)
    validate_file_size(content)

    raw_rows = _read_csv_rows(content) if file_format == "csv" else _read_xlsx_rows(content)
    if not raw_rows:
        raise ImportValidationError("Tệp không có nội dung dòng tiêu đề.", status_code=400)

    headers = _extract_and_validate_headers(raw_rows[0], spec)

    records: list[BaseModel] = []
    row_errors: list[ImportRowError] = []
    seen_keys: dict[tuple[Any, ...], int] = {}
    total_data_rows = 0

    for row_number, raw_row in enumerate(raw_rows[1:], start=2):
        if _is_blank_row(raw_row):
            continue
        total_data_rows += 1

        payload, pre_errors = _build_row_payload(headers, raw_row, spec)
        messages: list[str] = list(pre_errors)

        model_obj: Optional[BaseModel] = None
        if not pre_errors:
            try:
                model_obj = spec.schema.model_validate(payload)
            except ValidationError as exc:
                messages.extend(_format_pydantic_error(exc))

        if model_obj is not None and spec.unique_key_fn is not None:
            natural_key = spec.unique_key_fn(model_obj)
            if natural_key in seen_keys:
                first_row = seen_keys[natural_key]
                key_display = ", ".join(str(item) for item in natural_key)
                messages.append(
                    f"Trùng khóa nghiệp vụ ({key_display}) đã xuất hiện ở dòng {first_row}."
                )
            else:
                seen_keys[natural_key] = row_number

        if messages:
            row_errors.append(ImportRowError(row_number=row_number, messages=messages))
        elif model_obj is not None:
            records.append(model_obj)

    if total_data_rows == 0:
        raise ImportValidationError(
            "Tệp chỉ có dòng tiêu đề, không chứa dòng dữ liệu nào.",
            status_code=400,
        )

    result = ImportParseResult(
        entity=spec.entity,
        file_format=file_format,
        filename=filename,
        headers=headers,
        total_rows=total_data_rows,
        records=records,
        errors=row_errors,
    )
    if raise_on_row_errors:
        result.raise_for_errors()
    return result


async def read_upload_file_bounded(
    upload_file: UploadFile,
    *,
    max_bytes: int = MAX_IMPORT_FILE_BYTES,
) -> tuple[str, bytes]:
    """Đọc UploadFile (qua python-multipart) theo từng chunk để chặn sớm tệp quá dung lượng."""
    filename = (upload_file.filename or "").strip()
    detect_import_format(filename)

    chunks: list[bytes] = []
    total_size = 0
    while True:
        chunk = await upload_file.read(UPLOAD_READ_CHUNK_BYTES)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_bytes:
            raise ImportValidationError(
                f"Dung lượng tệp vượt quá giới hạn tối đa {max_bytes // (1024 * 1024)} MB.",
                status_code=413,
            )
        chunks.append(chunk)

    content = b"".join(chunks)
    validate_file_size(content)
    return filename, content


async def parse_upload_file(
    entity: str,
    upload_file: UploadFile,
    *,
    raise_on_row_errors: bool = False,
) -> ImportParseResult:
    """Đọc và kiểm tra tệp FastAPI UploadFile (multipart/form-data) cho UC07."""
    # Kiểm tra thực thể trước khi đọc luồng file lớn
    get_entity_spec(entity)
    filename, content = await read_upload_file_bounded(upload_file)
    return parse_import_bytes(
        entity=entity,
        content=content,
        filename=filename,
        raise_on_row_errors=raise_on_row_errors,
    )


__all__ = [
    "ALLOWED_IMPORT_EXTENSIONS",
    "DangKyThiImportRow",
    "ENTITY_IMPORT_SPECS",
    "EntityImportSpec",
    "ImportEntity",
    "ImportFormat",
    "ImportParseResult",
    "ImportRowError",
    "ImportValidationError",
    "MAX_IMPORT_FILE_BYTES",
    "MAX_IMPORT_ROWS",
    "detect_import_format",
    "get_entity_spec",
    "parse_import_bytes",
    "parse_upload_file",
    "read_upload_file_bounded",
    "validate_file_size",
]
