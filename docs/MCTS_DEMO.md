# Kịch bản demo phần MCTS

Thời lượng dự kiến 3–4 phút. Dùng giao diện và checkpoint hiện có của nhóm. Lưu video thực tế riêng sau khi quay.

| Phần | Thao tác | Nội dung giải thích |
| --- | --- | --- |
| 0:00–0:30 | Khởi chạy Web bằng launcher của nhóm, chọn MCTS | Giới thiệu bàn 9×9, luật freestyle từ 5 quân liên tiếp |
| 0:30–1:20 | Chơi Người–Máy, chọn X/O và đánh vài nước | MCTS tìm thắng/chặn ở gốc, sau đó tìm kiếm bằng UCT và rollout |
| 1:20–2:00 | Chuyển Máy–Máy: MCTS gặp Heuristic | Quan sát diễn biến; giải thích một tình huống MCTS bỏ sót chiến thuật nếu có |
| 2:00–2:40 | Chạy CLI với `--time-limit 0.05 --simulations 2000`, thử nhập sai và thoát bằng `q` | Giải thích tọa độ 0–8, kiểm tra đầu vào và giới hạn thời gian mềm |
| 2:40–3:30 | Mở bảng Ablation 2 và một log JSONL | Chỉ cấu hình, số ván, đổi bên X/O, seed, điểm và P95; nêu giới hạn của mẫu đo |

Ảnh cần chụp khi quay: nước thắng ngay, thế chỉ có một ô chặn, một tình huống MCTS thua Heuristic và thông báo nhập sai trong CLI. Ghi rõ agent, cấu hình và seed của từng ảnh. Không dùng một ảnh minh họa để kết luận tỷ lệ thắng.

Nội dung slide phần MCTS có thể chia thành bốn trang: quy ước giá trị và UCT; ngân sách mô phỏng/thời gian; thiết kế Ablation 2; kết quả và nhận xét. Số liệu lấy trực tiếp từ log của run được trích dẫn trong tài liệu thực nghiệm.
