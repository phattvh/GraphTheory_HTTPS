-- =============================================================================
-- HỆ THỐNG XẾP LỊCH THI TẬP TRUNG BẰNG THUẬT TOÁN TÔ MÀU ĐỒ THỊ
-- Database Initialization Script (PostgreSQL 16)
-- Phụ trách: TV2 (Backend: CSDL & Dữ liệu đầu vào)
-- Tham chiếu: docs/04. Database design.md
-- =============================================================================

-- =============================================================================
-- 1. BẢNG DANH MỤC ĐỘC LẬP
-- =============================================================================

-- 1.1. Bảng ky_thi: Thông tin các đợt thi (UC02)
CREATE TABLE IF NOT EXISTS ky_thi (
    id BIGSERIAL PRIMARY KEY,
    ma_ky_thi VARCHAR(50) NOT NULL UNIQUE,
    ten_ky_thi VARCHAR(255) NOT NULL,
    ngay_bat_dau DATE NOT NULL,
    ngay_ket_thuc DATE NOT NULL,
    so_ca_moi_ngay INT NOT NULL DEFAULT 4,
    trang_thai VARCHAR(20) NOT NULL DEFAULT 'khoi_tao',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_ky_thi_ngay CHECK (ngay_ket_thuc >= ngay_bat_dau),
    CONSTRAINT ck_ky_thi_so_ca CHECK (so_ca_moi_ngay > 0),
    CONSTRAINT ck_ky_thi_trang_thai CHECK (trang_thai IN ('khoi_tao', 'da_xep_lich', 'cong_bo'))
);

-- 1.2. Bảng mon_hoc: Danh mục môn thi / học phần (UC04)
CREATE TABLE IF NOT EXISTS mon_hoc (
    id BIGSERIAL PRIMARY KEY,
    ma_mon VARCHAR(20) NOT NULL UNIQUE,
    ten_mon VARCHAR(255) NOT NULL,
    thoi_luong_phut INT NOT NULL DEFAULT 90,
    so_tin_chi INT DEFAULT 3,
    CONSTRAINT ck_mon_hoc_thoi_luong CHECK (thoi_luong_phut > 0),
    CONSTRAINT ck_mon_hoc_tin_chi CHECK (so_tin_chi > 0)
);

-- 1.3. Bảng sinh_vien: Danh sách sinh viên (UC03)
CREATE TABLE IF NOT EXISTS sinh_vien (
    id BIGSERIAL PRIMARY KEY,
    mssv VARCHAR(20) NOT NULL UNIQUE,
    ho_ten VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    lop_sinh_hoat VARCHAR(50)
);

-- 1.4. Bảng phong_thi: Danh mục phòng thi (UC06)
CREATE TABLE IF NOT EXISTS phong_thi (
    id BIGSERIAL PRIMARY KEY,
    ma_phong VARCHAR(50) NOT NULL UNIQUE,
    ten_phong VARCHAR(100) NOT NULL,
    suc_chua INT NOT NULL,
    toa_nha VARCHAR(50),
    dang_su_dung BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT ck_phong_thi_suc_chua CHECK (suc_chua > 0)
);

-- =============================================================================
-- 2. BẢNG PHỤ THUỘC TẦNG 1
-- =============================================================================

-- 2.1. Bảng nguoi_dung: Tài khoản & Phân quyền Native JWT (UC01)
CREATE TABLE IF NOT EXISTS nguoi_dung (
    id BIGSERIAL PRIMARY KEY,
    ten_dang_nhap VARCHAR(50) NOT NULL UNIQUE,
    mat_khau_hash VARCHAR(255) NOT NULL,
    vai_tro VARCHAR(20) NOT NULL,
    mssv VARCHAR(20) UNIQUE,
    ho_ten VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_nguoi_dung_vai_tro CHECK (vai_tro IN ('admin', 'sinh_vien')),
    CONSTRAINT ck_sv_co_mssv CHECK (vai_tro != 'sinh_vien' OR mssv IS NOT NULL),
    CONSTRAINT fk_nguoi_dung_sinh_vien FOREIGN KEY (mssv) REFERENCES sinh_vien(mssv) ON DELETE SET NULL
);

-- 2.2. Bảng dang_ky_thi: Danh sách sinh viên đăng ký thi (UC05, UC07)
-- Cung cấp dữ liệu để Self-Join dựng đồ thị xung đột G = (V, E, W)
CREATE TABLE IF NOT EXISTS dang_ky_thi (
    id BIGSERIAL PRIMARY KEY,
    ky_thi_id BIGINT NOT NULL REFERENCES ky_thi(id) ON DELETE CASCADE,
    sinh_vien_id BIGINT NOT NULL REFERENCES sinh_vien(id) ON DELETE CASCADE,
    mon_hoc_id BIGINT NOT NULL REFERENCES mon_hoc(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_dang_ky UNIQUE (ky_thi_id, sinh_vien_id, mon_hoc_id)
);

-- 2.3. Bảng ca_thi: Ca thi (UC08 - Màu gán từ thuật toán DSatur / Welsh-Powell)
CREATE TABLE IF NOT EXISTS ca_thi (
    id BIGSERIAL PRIMARY KEY,
    ky_thi_id BIGINT NOT NULL REFERENCES ky_thi(id) ON DELETE CASCADE,
    stt_ca INT NOT NULL,
    ngay_thi DATE NOT NULL,
    gio_bat_dau TIME NOT NULL,
    gio_ket_thuc TIME NOT NULL,
    thuat_toan VARCHAR(30) NOT NULL DEFAULT 'DSATUR',
    CONSTRAINT ck_ca_thi_stt CHECK (stt_ca > 0),
    CONSTRAINT ck_ca_thi_gio CHECK (gio_ket_thuc > gio_bat_dau),
    CONSTRAINT ck_ca_thi_thuat_toan CHECK (thuat_toan IN ('DSATUR', 'WELSH_POWELL')),
    CONSTRAINT uq_ca_thi UNIQUE (ky_thi_id, stt_ca)
);

-- =============================================================================
-- 3. BẢNG PHỤ THUỘC TẦNG 2
-- =============================================================================

-- 3.1. Bảng lich_thi: Kết quả phân phòng và xếp lịch chi tiết (UC08 - FFD Bin Packing)
CREATE TABLE IF NOT EXISTS lich_thi (
    id BIGSERIAL PRIMARY KEY,
    ca_thi_id BIGINT NOT NULL REFERENCES ca_thi(id) ON DELETE CASCADE,
    mon_hoc_id BIGINT NOT NULL REFERENCES mon_hoc(id) ON DELETE CASCADE,
    phong_thi_id BIGINT NOT NULL REFERENCES phong_thi(id) ON DELETE RESTRICT,
    so_luong_sv INT NOT NULL,
    ghi_chu VARCHAR(255),
    CONSTRAINT ck_lich_thi_so_luong CHECK (so_luong_sv > 0),
    CONSTRAINT uq_lich_phong UNIQUE (ca_thi_id, phong_thi_id)
);

-- =============================================================================
-- 4. ĐÁNH CHỈ MỤC BỔ SUNG (INDEXING STRATEGY)
-- =============================================================================

-- 4.1. Tối ưu đếm số SV mỗi môn (tập đỉnh V) và Self-Join tìm cạnh xung đột (tập cạnh E)
CREATE INDEX IF NOT EXISTS idx_dang_ky_thi_ky_thi_mon ON dang_ky_thi(ky_thi_id, mon_hoc_id);
CREATE INDEX IF NOT EXISTS idx_dang_ky_thi_ky_thi_sv  ON dang_ky_thi(ky_thi_id, sinh_vien_id);

-- 4.2. Tối ưu truy vấn ca thi theo kỳ thi và lịch thi trên FullCalendar
CREATE INDEX IF NOT EXISTS idx_ca_thi_ky_thi          ON ca_thi(ky_thi_id);
CREATE INDEX IF NOT EXISTS idx_lich_thi_ca_thi        ON lich_thi(ca_thi_id);
CREATE INDEX IF NOT EXISTS idx_lich_thi_mon_hoc       ON lich_thi(mon_hoc_id);

-- =============================================================================
-- 5. SEED TÀI KHOẢN ADMIN MẶC ĐỊNH CHO MÔI TRƯỜNG DEV/DEMO
-- Mật khẩu mặc định: admin123 (được băm bằng bcrypt, cost factor 12)
-- =============================================================================
INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau_hash, vai_tro, ho_ten, email)
VALUES (
    'admin',
    '$2b$12$vP7lBCkdmRqOg4.tVNt26.VgNq85ByD2HxuX4m9grMVsm9s1Se.kW',
    'admin',
    'Quản trị viên Hệ thống',
    'admin@graphtheory.edu.vn'
)
ON CONFLICT (ten_dang_nhap) DO NOTHING;
