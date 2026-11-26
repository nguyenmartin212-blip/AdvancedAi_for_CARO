# Quy ước nhóm

## Git
- Nhánh `main` luôn chạy được và `pytest` xanh. Không push thẳng vào `main` và không dồn toàn bộ code lên sát ngày nộp.
- Mỗi người một nhánh theo việc: `feat/heuristic`, `feat/alphabeta`, `feat/ablation-search`, `feat/mcts`, `feat/mcts-time`, `feat/cnn`, `feat/rl-mcts`, `feat/arena`, `feat/eval-suite`, `feat/ui`, `feat/notebooks`.
- Cấu hình `git config user.name` và `user.email` khớp tài khoản GitHub cá nhân; dùng Issues/Projects và Pull Request (ít nhất 1 người review trước khi merge) để lưu minh chứng trên GitHub Insights.
- Commit message: `loại: nội dung ngắn` (feat, fix, test, docs, exp). Ví dụ `feat: add alpha-beta agent`.
- Không commit checkpoint lớn (>50MB) hoặc log thô quá nặng; ghi đường dẫn tải trong README nếu cần.

## Code
- Python ≥ 3.10, type hints cho hàm công khai, mỗi agent một file trong `agents/`.
- Agent không in ra màn hình trong `select_action`; dùng logger.
- Mỗi agent có test: nước đi luôn hợp lệ, thắng ngay khi có thể, chặn khi đối thủ sắp thắng, thắng Random.
- Mọi tham số ngẫu nhiên nhận `seed`.

## Log thí nghiệm & Đánh giá cuối kỳ
- Mỗi bản ghi một dòng JSON có tối thiểu: `run`, `agent_x`, `agent_o`, `winner`, `moves`, `seed`, `budget_mode`.
- Số đo chi phí & thống kê: `time_per_move` trung bình và độ trễ `p95` (giây), `nodes` hoặc `simulations`, `ram_mb`/`vram_mb` khi có, điểm chuẩn hóa `score = (wins + 0.5 * draws) / games` và khoảng tin cậy 95% (Wilson/Bootstrap).
- Giải đấu chính thức chạy tối thiểu `100` ván/cặp (khuyến nghị `200`), cân bằng lượt đi trước X/O ở cả hai chế độ `compute` và `time`, kèm tối thiểu 02 thí nghiệm ablation.
- Dữ liệu huấn luyện Level 5/6 phải khử trùng lặp và tách `train/val/test` theo đơn vị ván cờ; lưu rõ `seed`, siêu tham số, phần cứng và thời gian train.

## Quy trình mỗi tuần
- Họp ngắn đầu tuần chia việc, cuối tuần merge và chạy lại toàn bộ test.
- Ghi số liệu và biểu đồ ngay khi chạy xong để dùng cho báo cáo.
