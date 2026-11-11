# Gomoku (Caro) 9×9 – Multi-level Game AI

Đồ án cuối kỳ *Trí tuệ nhân tạo nâng cao*. Nhóm xây dựng và so sánh các agent chơi Gomoku 9×9. Bàn cờ dùng luật freestyle. Từ 5 quân liên tiếp theo hàng, cột hoặc đường chéo là thắng. Bàn đầy mà chưa có bên thắng thì hòa.

## Chạy bản hiện tại

Cần Python 3.10 trở lên. Mở PowerShell tại thư mục gốc của repo rồi chạy:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install numpy pytest
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.quick_match random random -n 20
```

Trên Linux hoặc macOS, dùng `python3 -m venv .venv` và thay đường dẫn Python bằng `.venv/bin/python`. Khi làm đến giao diện Pygame hoặc phần huấn luyện PyTorch, cài thêm các gói trong [requirements.txt](requirements.txt). GPU là tùy chọn.

## Tiến độ các level

| Level | Agent | Trạng thái |
| --- | --- | --- |
| 1 | Random | Đã có, tên registry là `random` |
| 2 | Heuristic / Rule-based | Cần triển khai trong mốc hiện tại |
| 3 | Minimax + Alpha-Beta | Cần triển khai trong mốc hiện tại |
| 4 | MCTS / UCT | Cần triển khai trong mốc hiện tại |
| 5 | CNN policy (+value), học có giám sát | Kế hoạch sau mốc hiện tại |
| 6 | Reinforcement Learning (self-play) | Kế hoạch sau mốc hiện tại |
| 7 | AlphaGo-inspired | Khuyến khích |
| 8 | AlphaZero-inspired | Khuyến khích |

Level 7–8 áp dụng ý tưởng từ AlphaGo và AlphaZero ở quy mô đồ án. Sách *AlphaGo Simplified* của Mark Liu là tài liệu tham khảo thuật toán. Xem chương 2 cho luật thắng/chặn, chương 5–7 cho Minimax và Alpha-Beta, chương 8 cho MCTS/UCT.

## Phân công mốc hiện tại

Mốc hoàn thành gồm bốn agent chơi được qua cùng registry, một lượt round-robin có log và một ván người đấu AI qua terminal. Tên file dưới đây là đầu ra dự kiến, trừ các file đã có trong repo.

### Thành viên 1 · Heuristic và Alpha-Beta

- **PR 1 — `feat/heuristic`.** Tạo `agents/heuristic.py` và `agents/test_heuristic.py`. Viết `evaluate(game, player)` để chấm thế cờ từ góc nhìn của `player`. Chấm các chuỗi theo bốn hướng, tính cả ô trống ở đầu chuỗi. Ưu tiên nước thắng ngay, rồi chặn nước thắng ngay của đối thủ, sau đó mới dùng điểm thế cờ. Đăng ký tên `heuristic`.
- **PR 2 — `feat/alphabeta`.** Tạo `agents/alphabeta.py` và `agents/test_alphabeta.py`. Dùng lại `evaluate()`. Tìm kiếm trên một bản `clone()`, dùng `step()` và `undo()` cho mỗi nhánh. Xử lý thế kết thúc trước khi kiểm tra độ sâu. Sắp xếp nước ứng viên để ưu tiên nước mạnh, giữ nước thắng hoặc chặn bắt buộc trước khi giới hạn số ứng viên. Đăng ký tên `alphabeta` và hỗ trợ tham số `depth`.
- **Nghiệm thu.** Cả hai bot trả nước hợp lệ, chọn nước thắng ngay, chặn được thế chỉ có một ô chặn và giữ nguyên trạng thái đầu vào. Alpha-Beta chạy thử ở độ sâu 2, sau đó đo ở độ sâu 3. Chạy đối kháng từng bot với Random và lưu số liệu thực tế.

### Thành viên 2 · MCTS và demo terminal

- **PR 1 — `feat/mcts`.** Tạo `agents/mcts.py` và `agents/test_mcts.py`. Cài chọn nút bằng UCT, mở rộng, mô phỏng và cập nhật ngược. Quy định rõ góc nhìn lưu giá trị tại mỗi nút và kiểm tra việc đổi dấu giữa hai lượt. Dùng RNG nhận `seed`, hỗ trợ `simulations` và `c`, đăng ký tên `mcts`. Bắt đầu với 50–100 mô phỏng để kiểm thử nhanh. Dùng kiểm tra thắng/chặn ở gốc để xử lý các thế chiến thuật đơn giản.
- **PR 2 — `feat/cli`.** Tạo `scripts/play_cli.py`. Người chơi chọn tên bot qua registry, nhập hàng/cột từ 0 đến 8, thấy bàn cờ sau mỗi lượt và được nhập lại nếu sai hoặc ô đã có quân. In kết quả và dừng khi thắng hoặc hòa. Dựng CLI với Random ngay khi cần một bot để thử.
- **Nghiệm thu.** Hai instance MCTS cùng seed và cùng cấu hình chọn cùng nước trong một thế thử. MCTS qua các test chiến thuật và giữ nguyên trạng thái đầu vào. Chơi hết một ván qua CLI và kiểm tra ít nhất một lần nhập sai.

### Thành viên 3 · Arena, GitHub và tích hợp

- **PR — `feat/arena`.** Tạo `arena/round_robin.py` và `arena/test_round_robin.py`. Tái dùng `play_game()` và `JsonlLogger`. Mỗi cặp đấu chạy hai lượt đổi X/O với cùng seed khai cuộc. Tạo agent mới cho từng ván và giữ tương thích với lệnh `scripts.quick_match` hiện tại.
- **Log và tổng hợp.** Ghi mỗi ván một dòng JSONL gồm `run`, `agent_x`, `agent_o`, `winner`, `moves`, `seed`, `budget_mode` và `time_per_move` tính bằng giây cho các nước do agent chọn. In bảng thắng, hòa, thua và thời gian trung bình. Nhận ngân sách hoặc cấu hình từ CLI để chạy smoke test với ít mô phỏng.
- **GitHub và nghiệm thu.** Kiểm tra repo chung, giao Issues, theo dõi PR và chạy test sau khi merge. Với bốn agent, chạy đủ sáu cặp và hai ván đổi bên mỗi cặp. Kiểm tra có 12 bản ghi kết quả, khai cuộc giống nhau trong mỗi cặp đổi bên, tổng thắng/hòa/thua khớp log và README có lệnh chạy cuối cùng.

### Trình tự tích hợp

1. Chốt ngay tên registry `random`, `heuristic`, `alphabeta`, `mcts`, giao diện `select_action(game) -> int` và các trường log. Thành viên 3 dựng arena bằng Random. Thành viên 2 có thể làm MCTS và CLI song song với Thành viên 1.
2. Merge Heuristic trước Alpha-Beta. MCTS, CLI và arena có thể merge độc lập khi test xanh. Mỗi PR của agent thêm dòng import module trong `agents/__init__.py` để factory được đăng ký. Khi cập nhật nhánh, giữ đủ các import đã merge.
3. Sau khi đủ bốn bot, chạy lại toàn bộ test, chạy round-robin với cấu hình nhỏ và chơi một ván demo. Lưu lệnh và kết quả đã chạy vào PR tích hợp hoặc Issue tổng. Cập nhật trạng thái level trong README sau khi kiểm tra trên `main`.

## Quy ước triển khai

- Bàn cờ dùng `board[r, c]`, với `0` là ô trống, `1` là X đi trước và `-1` là O. Action trên bàn 9×9 bằng `r` nhân 9 cộng `c`.
- Agent kế thừa `Agent` và trả một action hợp lệ từ `select_action(game)`. Dùng `game.clone()` khi mô phỏng nước đi để giữ nguyên trạng thái của bên gọi.
- Đặt factory có decorator `@register("ten_agent")` trong module agent. Import `register` từ `agents.registry` và import module mới ở `agents/__init__.py`. Factory nhận `seed` và các tham số cấu hình tương ứng.
- `Gomoku.encode()` trả ba lớp kích thước `9×9` theo thứ tự quân của bên sắp đi, quân đối thủ, nước vừa đánh. Sau mốc hiện tại có thể dùng Alpha-Beta để sinh nhãn cho CNN Level 5.
- Tham số mặc định ở [configs/default.json](configs/default.json). Xem [docs/CONVENTIONS.md](docs/CONVENTIONS.md) để biết quy ước test, log và commit.

## Làm việc trên GitHub

Nếu làm từ thư mục giải nén có sẵn lịch sử Git, dùng `git remote -v` để xác nhận `origin` trỏ về repo chung. Thành viên chưa có bản local clone repo sau khi chủ repo mời qua **Settings → Collaborators → Add people**.

Mỗi đầu việc có một Issue, người phụ trách và nhánh riêng. Ví dụ cho Heuristic:

```powershell
git switch main
git pull --ff-only origin main
git switch -c feat/heuristic
# Sau khi sửa và chạy test
git add agents/heuristic.py agents/test_heuristic.py agents/__init__.py
git commit -m "feat: add heuristic agent"
git push -u origin feat/heuristic
```

Mở PR vào `main`, liên kết Issue bằng `Closes #<số issue>` và ghi lệnh kiểm thử đã chạy. Nhóm review ít nhất một người trước khi merge và giữ `main` ở trạng thái chạy được. Khi cập nhật `.gitignore`, thêm `.venv/` và `.env`. Log thô và checkpoint lớn được lưu riêng. README ghi đường dẫn lấy dữ liệu cần để tái chạy.

## Cấu trúc thư mục

| Thư mục | Nội dung |
| --- | --- |
| `game/` | Engine Gomoku và test |
| `agents/` | Giao diện Agent, registry và các bot |
| `arena/` | Chạy một ván, sau đó mở rộng sang round-robin |
| `scripts/` | Lệnh chạy thử và demo terminal |
| `configs/`, `utils/` | Cấu hình, seed và logger JSONL |
| `train/`, `ui/` | Phần huấn luyện và giao diện Pygame dự kiến |
| `logs/`, `checkpoints/`, `notebooks/` | Kết quả chạy, trọng số và phân tích |
| `docs/` | Quy ước nhóm |

## Nộp bài

Theo checklist của nhóm, đóng gói `NhomXX_TenGame_TTNTNC_HoTen_MaSV.zip` gồm mã nguồn, README, log, checkpoint, báo cáo, slide và poster. Báo cáo các thí nghiệm đã thực sự chạy, kèm cấu hình, seed và số ván.
