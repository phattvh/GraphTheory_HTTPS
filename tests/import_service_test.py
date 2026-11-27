"""Kiểm thử tự động Ngày 8 (TV2): backend/services/import_service.py (UC07).

Chạy trong container fastapi:
    docker compose exec fastapi python tests/import_service_test.py
"""

import asyncio
from datetime import date, datetime
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import openpyxl
from starlette.datastructures import UploadFile as StarletteUploadFile
from starlette.requests import Request

from backend.schemas import (
    KyThiCreate,
    MonHocCreate,
    PhongThiCreate,
    SinhVienCreate,
)
from backend.services import (
    DangKyThiImportRow,
    ImportValidationError,
    parse_import_bytes,
    parse_upload_file,
)
from backend.services.import_service import MAX_IMPORT_FILE_BYTES


def _make_xlsx_bytes(rows: list[list[object]]) -> bytes:
    """Tạo nội dung tệp .xlsx trong bộ nhớ bằng openpyxl."""
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    wb.close()
    return buf.getvalue()


def _assert_import_error(fn, expected_status: int, keyword: str, label: str) -> None:
    try:
        fn()
    except ImportValidationError as exc:
        assert exc.status_code == expected_status, (
            f"[{label}] expected status {expected_status}, got {exc.status_code}: {exc.detail}"
        )
        assert keyword.lower() in exc.detail.lower(), (
            f"[{label}] expected '{keyword}' in '{exc.detail}'"
        )
        return
    raise AssertionError(f"[{label}] Expected ImportValidationError")


def test_csv_utf8_bom_all_entities_and_defaults():
    """Đọc CSV UTF-8 BOM cho 5 thực thể, bỏ qua dòng trống và tự áp dụng giá trị mặc định."""
    sv_csv = (
        "\ufeffmssv,ho_ten,email,lop_sinh_hoat\r\n"
        "22110001,Nguyễn Văn An,an.nv@univ.edu.vn,22CNTT1\r\n"
        "22110002,Trần Thị Bình,,\r\n"
        ",,,\r\n"
    ).encode("utf-8")
    sv_res = parse_import_bytes("sinh_vien", sv_csv, "sinh_vien.csv")
    assert sv_res.is_valid and sv_res.file_format == "csv"
    assert sv_res.total_rows == 2 and sv_res.valid_count == 2
    assert isinstance(sv_res.records[0], SinhVienCreate)
    assert sv_res.records[1].email is None and sv_res.records[1].lop_sinh_hoat is None

    # Thiếu cột tùy chọn nhưng vẫn đủ cột bắt buộc -> dùng default Pydantic (90 phút, 3 tín chỉ)
    mh_csv = "ma_mon,ten_mon\nIT3010,Lý thuyết đồ thị\n".encode("utf-8")
    mh_res = parse_import_bytes("mon_hoc", mh_csv, "mon_hoc.csv")
    assert mh_res.is_valid and isinstance(mh_res.records[0], MonHocCreate)
    assert mh_res.records[0].thoi_luong_phut == 90 and mh_res.records[0].so_tin_chi == 3

    pt_csv = (
        "ma_phong,ten_phong,suc_chua,toa_nha,dang_su_dung\n"
        "TC-301,Phòng TC 301,60,Nhà TC,\n"
        "TC-302,Phòng TC 302,45,,false\n"
    ).encode("utf-8")
    pt_res = parse_import_bytes("phong_thi", pt_csv, "phong.csv")
    assert pt_res.is_valid and isinstance(pt_res.records[0], PhongThiCreate)
    assert pt_res.records[0].dang_su_dung is True
    assert pt_res.records[1].toa_nha is None and pt_res.records[1].dang_su_dung is False

    kt_csv = (
        "ma_ky_thi,ten_ky_thi,ngay_bat_dau,ngay_ket_thuc,so_ca_moi_ngay,trang_thai\n"
        "KTHK1_2027,Thi HK1,2027-01-10,2027-01-20,,\n"
    ).encode("utf-8")
    kt_res = parse_import_bytes("ky_thi", kt_csv, "ky_thi.csv")
    assert kt_res.is_valid and isinstance(kt_res.records[0], KyThiCreate)
    assert kt_res.records[0].so_ca_moi_ngay == 4
    assert kt_res.records[0].trang_thai == "khoi_tao"

    dk_csv = "ma_ky_thi,ma_mon,mssv\nKTHK1_2027,IT3010,22110001\n".encode("utf-8")
    dk_res = parse_import_bytes("dang_ky_thi", dk_csv, "dang_ky.csv")
    assert dk_res.is_valid and isinstance(dk_res.records[0], DangKyThiImportRow)
    assert dk_res.records[0].mssv == "22110001"


def test_xlsx_excel_coercion_and_header_flexibility():
    """Đọc .xlsx với openpyxl: ép mã số int/float sang str, date/datetime chuẩn, đảo thứ tự cột."""
    sv_xlsx = _make_xlsx_bytes([
        [" Ho_Ten ", "MSSV", None, None],  # đảo thứ tự + hoa thường + ô trống cuối dòng header
        ["Lê Hoàng Cường", 22110003],
        ["Phạm Minh Dung", 22110004.0],
        [None, None],
    ])
    sv_res = parse_import_bytes("sinh_vien", sv_xlsx, "students.xlsx")
    assert sv_res.is_valid and sv_res.file_format == "xlsx"
    assert sv_res.headers == ["ho_ten", "mssv"]
    assert sv_res.records[0].mssv == "22110003"
    assert sv_res.records[1].mssv == "22110004"

    kt_xlsx = _make_xlsx_bytes([
        ["ma_ky_thi", "ten_ky_thi", "ngay_bat_dau", "ngay_ket_thuc", "so_ca_moi_ngay"],
        ["HK2_2027", "Thi HK2", datetime(2027, 6, 1, 8, 0), date(2027, 6, 15), 5.0],
    ])
    kt_res = parse_import_bytes("ky_thi", kt_xlsx, "kythi.xlsx")
    assert kt_res.is_valid
    assert kt_res.records[0].ngay_bat_dau == date(2027, 6, 1)
    assert kt_res.records[0].so_ca_moi_ngay == 5


def test_file_and_header_validation_errors():
    """Chặn thực thể lạ, sai đuôi tệp, tệp rỗng, >5MB, hỏng .xlsx, sai mã hóa CSV, sai cột."""
    _assert_import_error(
        lambda: parse_import_bytes("nguoi_dung", b"a,b\n1,2\n", "users.csv"),
        400,
        "không được hỗ trợ",
        "unsupported entity",
    )
    _assert_import_error(
        lambda: parse_import_bytes("sinh_vien", b"mssv,ho_ten\n1,A\n", "sv.xls"),
        400,
        ".csv, .xlsx",
        "unsupported extension",
    )
    _assert_import_error(
        lambda: parse_import_bytes("sinh_vien", b"", "sv.csv"),
        400,
        "rỗng",
        "empty bytes",
    )
    _assert_import_error(
        lambda: parse_import_bytes("sinh_vien", b"a" * (MAX_IMPORT_FILE_BYTES + 1), "big.csv"),
        413,
        "5 MB",
        "oversize file",
    )
    _assert_import_error(
        lambda: parse_import_bytes("sinh_vien", b"PK\x03\x04corrupted", "bad.xlsx"),
        400,
        "hỏng",
        "corrupt xlsx",
    )
    _assert_import_error(
        lambda: parse_import_bytes("sinh_vien", b"\xff\xfeinvalid_utf8", "bad_enc.csv"),
        400,
        "UTF-8",
        "non utf8 csv",
    )
    _assert_import_error(
        lambda: parse_import_bytes("sinh_vien", b"mssv,email\n22110001,a@b.c\n", "missing.csv"),
        400,
        "ho_ten",
        "missing required header",
    )
    _assert_import_error(
        lambda: parse_import_bytes("sinh_vien", b"mssv,ho_ten,hack\n22110001,An,1\n", "unknown.csv"),
        400,
        "hack",
        "unknown header",
    )
    _assert_import_error(
        lambda: parse_import_bytes("sinh_vien", b"mssv,ho_ten,mssv\n1,An,2\n", "dup.csv"),
        400,
        "trùng lặp",
        "duplicate header",
    )
    _assert_import_error(
        lambda: parse_import_bytes("sinh_vien", b"mssv,,ho_ten\n1,,An\n", "blank_col.csv"),
        400,
        "vị trí thứ 2",
        "blank intermediate header",
    )
    _assert_import_error(
        lambda: parse_import_bytes("sinh_vien", b"mssv,ho_ten\n", "header_only.csv"),
        400,
        "không chứa dòng dữ liệu",
        "header only file",
    )


def test_row_level_validation_and_duplicate_key_detection():
    """Validate từng dòng qua Pydantic: gom đủ lỗi theo đúng số dòng + phát hiện trùng khóa."""
    sv_csv = (
        "mssv,ho_ten,email,lop_sinh_hoat\n"
        "22110001,Nguyễn Văn An,an@univ.edu.vn,22CNTT1\n"   # Dòng 2: hợp lệ
        ",Trần Thị Bình,bad_email,22CNTT1\n"               # Dòng 3: thiếu mssv + sai email
        "22110001,Nguyễn Trùng Mã,ok@univ.edu.vn,22CNTT1\n" # Dòng 4: trùng mssv dòng 2
        "22110005,Lê Dư Cột,ok@univ.edu.vn,22CNTT1,EXTRA\n" # Dòng 5: dư cột
    ).encode("utf-8")

    res = parse_import_bytes("sinh_vien", sv_csv, "rows.csv")
    assert not res.is_valid
    assert res.total_rows == 4
    assert res.valid_count == 1
    assert res.error_count == 3
    assert [err.row_number for err in res.errors] == [3, 4, 5]
    assert "22110001" in res.errors[1].format_message()
    assert "dòng 2" in res.errors[1].format_message().lower()

    _assert_import_error(
        lambda: parse_import_bytes("sinh_vien", sv_csv, "rows.csv", raise_on_row_errors=True),
        422,
        "Dòng 3:",
        "raise_on_row_errors",
    )

    # Kiểm tra bool bị ép vào int & số thập phân lẻ trong Excel cho Phòng thi
    pt_xlsx = _make_xlsx_bytes([
        ["ma_phong", "ten_phong", "suc_chua", "dang_su_dung"],
        ["P101", "Phòng 101", True, True],
        ["P102", "Phòng 102", 60.5, False],
    ])
    pt_res = parse_import_bytes("phong_thi", pt_xlsx, "bad_rooms.xlsx")
    assert pt_res.error_count == 2
    assert [err.row_number for err in pt_res.errors] == [2, 3]

    # Kiểm tra ngày kết thúc < ngày bắt đầu & chuỗi ngày sai định dạng ở Kỳ thi
    kt_csv = (
        "ma_ky_thi,ten_ky_thi,ngay_bat_dau,ngay_ket_thuc\n"
        "K1,Kỳ 1,2027-01-20,2027-01-10\n"
        "K2,Kỳ 2,10/01/2027,2027-01-20\n"
    ).encode("utf-8")
    kt_res = parse_import_bytes("ky_thi", kt_csv, "bad_exams.csv")
    assert kt_res.error_count == 2
    assert [err.row_number for err in kt_res.errors] == [2, 3]


def test_python_multipart_upload_file_integration():
    """Kiểm tra tích hợp đọc UploadFile & multipart/form-data thực tế qua python-multipart."""
    payload = "ma_mon,ten_mon,thoi_luong_phut,so_tin_chi\nIT001,Nhập môn lập trình,120,4\n".encode("utf-8")
    upload = StarletteUploadFile(filename="mon_hoc.csv", file=io.BytesIO(payload))
    parsed = asyncio.run(parse_upload_file("mon_hoc", upload))
    assert parsed.is_valid and parsed.records[0].ma_mon == "IT001"

    # Kiểm tra chặn sớm UploadFile vượt quá 5 MB khi đọc từng chunk
    oversize_upload = StarletteUploadFile(
        filename="oversize.csv",
        file=io.BytesIO(b"a" * (MAX_IMPORT_FILE_BYTES + 1)),
    )
    _assert_import_error(
        lambda: asyncio.run(parse_upload_file("mon_hoc", oversize_upload)),
        413,
        "5 MB",
        "upload_file oversize",
    )

    # Kiểm tra phân tích luồng multipart/form-data thực tế qua Starlette Request + python-multipart
    xlsx_bytes = _make_xlsx_bytes([
        ["ma_phong", "ten_phong", "suc_chua"],
        ["B1-201", "Giảng đường B1-201", 80],
    ])
    boundary = "----GraphTheoryTestBoundary7MA4YWxkTrZu0gW"
    multipart_body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="rooms.xlsx"\r\n'
        "Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n"
    ).encode("utf-8") + xlsx_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    async def _run_asgi_multipart():
        sent = False

        async def _receive():
            nonlocal sent
            if sent:
                return {"type": "http.request", "body": b"", "more_body": False}
            sent = True
            return {"type": "http.request", "body": multipart_body, "more_body": False}

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/import/phong_thi",
            "headers": [
                (
                    b"content-type",
                    f"multipart/form-data; boundary={boundary}".encode("ascii"),
                ),
                (b"content-length", str(len(multipart_body)).encode("ascii")),
            ],
        }
        request = Request(scope, _receive)
        form = await request.form()
        try:
            uploaded_file = form["file"]
            return await parse_upload_file("phong_thi", uploaded_file)
        finally:
            await form.close()

    res = asyncio.run(_run_asgi_multipart())
    assert res.is_valid and res.file_format == "xlsx"
    assert res.valid_count == 1
    assert res.records[0].ma_phong == "B1-201"
    assert res.records[0].suc_chua == 80


def main():
    test_csv_utf8_bom_all_entities_and_defaults()
    test_xlsx_excel_coercion_and_header_flexibility()
    test_file_and_header_validation_errors()
    test_row_level_validation_and_duplicate_key_detection()
    test_python_multipart_upload_file_integration()
    print("[PASS] Tat ca 5 nhom kiem thu import_service_test.py (UC07) deu dat 100%.")


if __name__ == "__main__":
    main()
