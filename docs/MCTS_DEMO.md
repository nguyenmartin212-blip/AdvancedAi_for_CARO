# Kịch bản demo phần MCTS

Bộ video và slide bao quát toàn dự án nằm ở [PROJECT_DEMO.md](PROJECT_DEMO.md). Tài liệu này giữ riêng phần MCTS để tham khảo khi trình bày thuật toán.

Bản ghi ngày 27/11/2026 dài 3 phút, độ phân giải 1280×720, 12 fps. Video có phụ đề tiếng Việt, không có lời thu âm. Web dùng MCTS với 400 mô phỏng, c=1.4; CLI dùng tối đa 2.000 mô phỏng và giới hạn mềm 50 ms/nước.

- [Video Web và CLI](demo/mcts_demo_vi.mp4)
- [Slide phần thành viên 2](demo/MCTS_TV2.pptx): sáu trang, kèm ghi chú thuyết trình, biểu đồ và bảng có thể chỉnh sửa.
- [Phụ đề](demo/captions_vi.srt), [lời dẫn](demo/narration_vi.txt) và [đầu ra CLI](demo/cli_transcript.txt).
- [Thông tin bản ghi](demo/demo_manifest.json) lưu lịch sử nước đi, cấu hình và SHA-256 của log nguồn; [thông số video](demo/video_metadata.json) ghi định dạng MPEG-4 và số khung hình.

| Phần | Thao tác | Nội dung giải thích |
| --- | --- | --- |
| 0:00–0:30 | Khởi chạy Web bằng launcher của nhóm, chọn MCTS | Giới thiệu bàn 9×9, luật freestyle từ 5 quân liên tiếp |
| 0:30–1:20 | Chơi Người–Máy, chọn X/O và đánh vài nước | MCTS tìm thắng/chặn ở gốc, sau đó tìm kiếm bằng UCT và rollout |
| 1:20–2:00 | Chuyển Máy–Máy: MCTS gặp Heuristic | Quan sát diễn biến; giải thích một tình huống MCTS bỏ sót chiến thuật nếu có |
| 2:00–2:40 | Chạy CLI với `--time-limit 0.05 --simulations 2000`, thử nhập sai và thoát bằng `q` | Giải thích tọa độ 0–8, kiểm tra đầu vào và giới hạn thời gian mềm |
| 2:40–3:30 | Mở bảng Ablation 2 và một log JSONL | Chỉ cấu hình, số ván, đổi bên X/O, seed, điểm và P95; nêu giới hạn của mẫu đo |

Ảnh chụp từ lần chạy nằm trong [demo/screenshots](demo/screenshots). Hai thế thắng/chặn là thế kiểm thử dựng từ lịch sử hợp lệ, được ghi rõ trong video; nước trả lời do agent MCTS thực hiện. Với action = hàng × 9 + cột, lịch sử trước nước thắng là `[36, 9, 37, 10, 38, 11, 39, 12]`, trước nước chặn là `[40, 0, 49, 1, 41, 2, 50, 3]`. Seed dùng cho các lượt chạy trực tiếp là 0.

Ảnh `mcts_heuristic_loss.png` mở lại ván #39, seed 19, MCTS đi X thua Heuristic đi O từ `mcts_sensitivity_40_s400_c1.4_vs_heuristic.jsonl`. Đây là ván trong bộ thực nghiệm 960 ván, khác với ván AI–AI chạy trực tiếp trong video. Kết quả tổng hợp lấy từ CSV đã đối chiếu log, không suy ra tỷ lệ thắng từ riêng các ảnh minh họa.

Các mốc trong bản ghi: 0:08 Người–Máy; 0:53 thắng ngay; 1:14 chặn bắt buộc; 1:34 Máy–Máy; 1:54 xem lại ván thua; 2:03 CLI; 2:30 bảng Ablation 2. Bảng thao tác bên trên là kịch bản tham khảo khi trình bày trực tiếp.
