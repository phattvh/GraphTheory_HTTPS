# Quy tắc làm việc Git & Kiểm thử dự án

Mọi thay đổi mã nguồn trong dự án phải tuân thủ nghiêm ngặt các quy tắc dưới đây:

## 1. Quy tắc Commit & Kiểm thử

- **Commit nhỏ, tách bạch (Atomic Commits):** Làm xong một chức năng nhỏ hoặc một phần việc nhỏ thì commit ngay. Không gộp nhiều tính năng, sửa lỗi hoặc đổi cấu trúc vào chung một commit.
- **Làm tới đâu, test tới đó:** Với mỗi chức năng hoàn thành, bắt buộc vừa kiểm thử thủ công (test tay) vừa tạo/cập nhật file test tự động tương ứng (ví dụ: `<ten_chuc_nang>_test.py`) và chạy **pass toàn bộ** trước khi commit.
- **Kiểm thử độc lập khi dùng AI:** Khi dùng AI để review hoặc kiểm thử chức năng, khuyến nghị mở một khung chat (conversation) mới độc lập để tránh thiên vị ngữ cảnh từ phiên viết code.
- **Dọn sạch trước khi commit:** Xóa toàn bộ file tạm, code nháp, log thử nghiệm và các file không liên quan trước khi commit.
- **Dùng `.gitignore` đầy đủ:** Đảm bảo không commit các file cấu hình bí mật (`.env`), môi trường ảo, cache (`__pycache__`, `.pytest_cache`), log hoặc file tạm.
- **Quy ước Commit Message (Conventional Commits):** Viết ngắn gọn, nêu rõ làm gì và vì sao làm, dùng tiền tố thống nhất:
  - `feat:` thêm chức năng mới *(VD: `feat: add login validation`)*
  - `fix:` sửa lỗi
  - `test:` thêm hoặc cập nhật file test *(VD: `test: add login_test.py`)*
  - `refactor:` chỉnh sửa code nhưng không thay đổi logic/chức năng
  - `chore:` dọn dẹp, cập nhật cấu hình hoặc file phụ

## 2. Quy tắc Quản lý Nhánh (Branching)

- **Nhánh `main`:** Chỉ nhận code đã được kiểm thử ổn định thông qua Merge / Pull Request (không push trực tiếp).
- **Nhánh `test`:** Dùng để gộp và kiểm thử tích hợp code trước khi đẩy lên `main` *(do trưởng nhóm / người phụ trách quản lý)*.
- **Nhánh chức năng / sửa lỗi riêng biệt:** Mỗi chức năng hoặc bug làm trên một nhánh riêng với tên rõ ràng:
  - `feat/<ten-chuc-nang>` *(VD: `feat/user-login`)*
  - `fix/<ten-loi>` *(VD: `fix/cart-total`)*
  - `test/<ten-chuc-nang>` *(VD: `test/user-login`)*
- **Đồng bộ trước khi tách và trước khi merge:** Luôn `pull` / `merge` code mới nhất từ nhánh gốc trước khi mở nhánh mới và trước khi merge ngược lại để hạn chế xung đột.
- **Dọn nhánh sau khi merge:** Xóa nhánh tính năng/sửa lỗi sau khi đã merge xong và không còn sử dụng.
