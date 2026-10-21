# Quy ước nhóm

## Git
- Nhánh `main` luôn chạy được và `pytest` xanh. Không push thẳng vào `main`.
- Mỗi người một nhánh theo việc: `feat/heuristic`, `feat/alphabeta`, `feat/mcts`, `feat/cnn`, `feat/arena`, `feat/ui`.
- Pull request nhỏ, ít nhất 1 người review trước khi merge.
- Commit message: `loại: nội dung ngắn` (feat, fix, test, docs, exp). Ví dụ `feat: add alpha-beta agent`.
- Không commit checkpoint lớn (>50MB) hoặc log thô quá nặng; ghi đường dẫn tải trong README nếu cần.

## Code
- Python ≥ 3.10, type hints cho hàm công khai, mỗi agent một file trong `agents/`.
- Agent không in ra màn hình trong `select_action`; dùng logger.
- Mỗi agent có test: nước đi luôn hợp lệ, thắng ngay khi có thể, chặn khi đối thủ sắp thắng, thắng Random.
- Mọi tham số ngẫu nhiên nhận `seed`.

## Log thí nghiệm
Mỗi bản ghi một dòng JSON có tối thiểu: `run`, `agent_x`, `agent_o`, `winner`, `moves`, `seed`, `budget_mode`.
Số đo thời gian: `time_per_move` (giây), `nodes` hoặc `simulations`, `ram_mb` khi có.

## Quy trình mỗi tuần
- Họp ngắn đầu tuần chia việc, cuối tuần merge và chạy lại toàn bộ test.
- Ghi số liệu và biểu đồ ngay khi chạy xong để dùng cho báo cáo.
