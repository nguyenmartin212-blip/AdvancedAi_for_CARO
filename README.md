# Gomoku (Caro) 9×9 – Multi-level Game AI

Đồ án cuối kỳ *Trí tuệ nhân tạo nâng cao*. Nhóm xây dựng và so sánh các agent chơi Gomoku 9×9. Bàn cờ dùng luật freestyle. Từ 5 quân liên tiếp theo hàng, cột hoặc đường chéo là thắng. Bàn đầy mà chưa có bên thắng thì hòa.

## Mô hình hóa bài toán & Câu hỏi nghiên cứu

- **Tính chất môi trường:** Gomoku 9×9 freestyle (`k = 5`, chấp nhận chuỗi ≥ 5) là trò chơi hai người chơi luân phiên (`X = +1` đi trước, `O = -1` đi sau), **quan sát đầy đủ**, **xác định**, **tổng bằng không** và **hữu hạn** (tối đa 81 nước; cận trên không gian cấu hình `3^81 ≈ 4.43 × 10^38`, hệ số rẽ nhánh đầu ván là 81).
- **Trạng thái, hành động & phần thưởng:** Trạng thái lưu bằng lưới `board[9, 9] ∈ {-1, 0, 1}` cùng người sắp đi `player ∈ {+1, -1}` (hoặc tensor bất biến lượt đi `encode()` kích thước `(3, 9, 9)`). Hành động hợp lệ `a = 9r + c ∈ [0, 80]` tại các ô trống; phần thưởng cuối ván từ góc nhìn người chơi là `+1` (thắng), `-1` (thua), `0` (hòa).
- **Câu hỏi nghiên cứu trọng tâm:**
  - **RQ1:** Trên bàn Caro 9×9, trong cùng ngân sách thời gian suy nghĩ mỗi nước (`~50–65 ms/nước`), MCTS/UCT với rollout ngẫu nhiên có vượt Minimax + Alpha-Beta dùng hàm lượng giá cửa sổ `4^n` hay không?
  - **RQ2:** Tác tử học từ dữ liệu/tự chơi (Level 5 CNN / Level 6 RL) cải thiện tỷ lệ thắng thế nào so với heuristic tĩnh hoặc khi tích hợp dẫn hướng cho cây MCTS?

## Chạy nhanh 1-Click & Web Deploy (Không cần Docker)

Không cần cài Docker hay cấu hình thủ công:

- **Windows (1-Click):** Nháy đúp trực tiếp file [run_caro.bat](run_caro.bat) tại thư mục gốc. Script tự tạo `.venv` (nếu chưa có), cài gói tối thiểu và mở trình duyệt với bàn cờ Caro 9×9 hỗ trợ cả **Người đấu AI** (chọn quân X/O, hoàn tác) và **AI đấu AI** (tự chọn 2 agent bất kỳ đối đầu tự động hoặc đi từng bước).
- **macOS / Linux:** Chạy `bash run_caro.sh` (hoặc gọi trực tiếp `.\.venv\Scripts\python.exe -X utf8 -m scripts.web_app`).
- **Deploy đám mây miễn phí (không cần Docker):** Đẩy repo lên GitHub rồi kết nối trực tiếp với **Render.com** (*New → Blueprint / Web Service*); file [render.yaml](render.yaml) tự cài bản Python + PyTorch CPU nhẹ và khởi chạy máy chủ tại `0.0.0.0:$PORT` kèm health-check `/healthz`.

## Chạy qua dòng lệnh (CLI & Kiểm thử)

Cần Python 3.10 trở lên. Mở PowerShell tại thư mục gốc của repo rồi chạy:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install numpy pytest
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.quick_match random random -n 20
.\.venv\Scripts\python.exe -m scripts.quick_match alphabeta heuristic -n 20 --seed 0
.\.venv\Scripts\python.exe -m arena.round_robin --agents random heuristic alphabeta mcts --seed 0
```

Trên Linux hoặc macOS, dùng `python3 -m venv .venv` và thay đường dẫn Python bằng `.venv/bin/python`. Khi làm đến giao diện Pygame hoặc phần huấn luyện PyTorch, cài thêm các gói trong [requirements.txt](requirements.txt). GPU là tùy chọn.

## MCTS và demo terminal (Thành viên 2)

Nhánh `feat/mcts-cli` bổ sung bot `mcts` và lệnh chơi qua terminal, theo cùng giao diện Agent/registry của bot Heuristic đã có. Chạy tại thư mục gốc repo:

```powershell
.\.venv\Scripts\python.exe -m scripts.play_cli random --seed 0
.\.venv\Scripts\python.exe -m scripts.play_cli mcts --side o --seed 0 --simulations 100 --c 1.4
.\.venv\Scripts\python.exe -m scripts.quick_match mcts random -n 12 --seed 0
.\.venv\Scripts\python.exe -m pytest -q
```

Người chơi mặc định cầm X và đi trước; `--side o` cho AI đi trước. Nhập `hàng cột`, ví dụ `4 4`, với tọa độ từ 0 đến 8. Nhập sai định dạng, ngoài bàn hoặc vào ô đã có quân thì được nhập lại. Bàn cờ hiện sau mỗi nước; khi thắng hoặc hòa, chương trình in kết quả và dừng. Nhập `q`, Ctrl+C hoặc kết thúc đầu vào để thoát. Các lời nhắc và kết quả dùng tiếng Việt. Xem `--help` để biết tùy chọn; bot lấy từ registry nên dùng được cả `random`, `heuristic` và `mcts`.

MCTS gồm chọn nút theo UCT, mở rộng, mô phỏng ngẫu nhiên đến hết ván và cập nhật ngược. Mỗi nút lưu tổng kết quả theo góc nhìn **bên sắp đi tại nút đó**. Khi chọn con, lấy âm giá trị trung bình của con; khi cập nhật ngược, đổi dấu qua mỗi lượt. Nước cuối được chọn theo số lần thăm, rồi điểm trung bình từ góc nhìn gốc. Bot kiểm tra thắng ngay trước, sau đó chặn đối thủ ở gốc; mọi mô phỏng dùng bản sao để giữ nguyên trạng thái đầu vào.

Factory nhận `seed`, `simulations` (số nguyên dương) và `c` (hữu hạn, không âm). Mặc định của lớp là 100 mô phỏng; cấu hình chung hiện tại dùng 400. CLI cho phép ghi đè để chạy demo nhanh. Cùng seed, cấu hình và chuỗi lời gọi cho cùng nước đi. Rollout hiện dùng nước ngẫu nhiên, chưa có đánh giá học máy hay giới hạn thời gian; ngân sách mô phỏng thấp có thể bỏ sót chiến thuật sâu.

Kiểm tra thực tế trên nhánh này (15/11/2026, Python 3.15.1, NumPy 2.5.4):

- `pytest -q`: **48 test đạt**, gồm chiến thuật thắng/chặn, cùng seed, giữ nguyên đầu vào, góc nhìn UCT/cập nhật ngược, ván hòa và các trường hợp nhập terminal.
- Lệnh `quick_match` ở trên: **MCTS thắng 12, thua 0, hòa 0** trước Random; 400 mô phỏng/nước, `c=1.4`, seed gốc 0, đổi bên từng ván và 2 nước khai cuộc ngẫu nhiên theo runner hiện có. Đây là mẫu kiểm tra nhỏ, chưa phải đánh giá sức mạnh tổng quát.
- Chạy `scripts.play_cli random --seed 0` qua đầu vào terminal đã chuẩn bị: kết thúc sau 9 nước, người chơi X thắng; đã thử sai định dạng, tọa độ âm/ngoài bàn và ô đã có quân.

## Arena đánh giá chuẩn & Notebook phân tích (Thành viên 3)

Module [arena/round_robin.py](arena/round_robin.py) tổ chức giải đấu vòng tròn đổi bên đối xứng (cùng `seed` khai cuộc cho 2 lượt cầm X/O của mỗi cặp), hỗ trợ cả hai chế độ ngân sách **`compute`** (cấu hình mặc định minh bạch) và **`time`** (cùng giới hạn giây/nước), ghi log JSONL chi tiết ra `logs/<run>.jsonl`, đồng thời tổng hợp `score = (thắng + 0.5 × hòa) / số_ván`, khoảng tin cậy **Wilson 95%**, thời gian trung bình/nước, độ trễ **P95**, số `nodes`/`simulations`, ma trận đối đầu và thống kê lợi thế đi trước:

```powershell
# Kiểm thử nhanh (20 ván, 5 agent) và toàn bộ bộ unit/integration tests
.\.venv\Scripts\python.exe -m arena.round_robin --agents random heuristic alphabeta mcts cnn --seed 0 --matrix
.\.venv\Scripts\python.exe -m pytest -q

# Giải đấu chính thức 100 ván/cặp × 10 cặp = 1.000 ván/chế độ (tổng 2.000 ván) cho báo cáo cuối kỳ
.\.venv\Scripts\python.exe -m arena.round_robin --agents random heuristic alphabeta mcts cnn -n 100 --budget-mode compute --seed 0 --matrix --run rr_compute_100
.\.venv\Scripts\python.exe -m arena.round_robin --agents random heuristic alphabeta mcts cnn -n 100 --budget-mode time --seconds-per-move 0.05 --seed 1000 --matrix --run rr_time_100
```

Notebook [notebooks/analysis.ipynb](notebooks/analysis.ipynb) đọc trực tiếp `logs/*.jsonl` và xuất bảng tổng hợp cùng 4 bộ biểu đồ (`head_to_head_matrix.png`, `score_and_latency.png`, `side_advantage_and_length.png`, `cnn_learning_and_ablation1.png`) vào `notebooks/figures/`.

### Kết quả thực nghiệm 2.000 ván (5 agent Level 1–5, `opening_moves=2`)

1. **Chế độ `compute`** (`-n 100`, `--seed 0`, 1.000 ván; `alphabeta depth=3`, `mcts simulations=400, c=1.4`, `cnn channels=48`):

| Agent | Thắng | Hòa | Thua | Điểm (`score`) | CI 95% (Wilson) | Thời gian/nước (s) | P95 (s) | Nodes/Sims |
| --- | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: |
| `alphabeta` | 360 | 28 | 12 | 0.935 | `[0.91, 0.96]` | 0.051666 | 0.110720 | 157.1 |
| `cnn` | 258 | 35 | 107 | 0.689 | `[0.64, 0.73]` | 0.001168 | 0.001886 | — |
| `heuristic` | 245 | 9 | 146 | 0.624 | `[0.58, 0.67]` | 0.001299 | 0.002845 | — |
| `mcts` | 101 | 0 | 299 | 0.253 | `[0.21, 0.30]` | 0.054437 | 0.086779 | 400.0 |
| `random` | 0 | 0 | 400 | 0.000 | `[0.00, 0.01]` | 0.000012 | 0.000025 | — |

2. **Chế độ `time`** (`-n 100`, `--seconds-per-move 0.05`, `--seed 1000`, 1.000 ván; tự hiệu chuẩn `alphabeta depth=3`, `mcts simulations=359`):

| Agent | Thắng | Hòa | Thua | Điểm (`score`) | CI 95% (Wilson) | Thời gian/nước (s) | P95 (s) | Nodes/Sims |
| --- | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: |
| `alphabeta` | 365 | 21 | 14 | 0.939 | `[0.91, 0.96]` | 0.048688 | 0.100183 | 155.6 |
| `cnn` | 252 | 36 | 112 | 0.675 | `[0.63, 0.72]` | 0.001051 | 0.001664 | — |
| `heuristic` | 245 | 17 | 138 | 0.634 | `[0.59, 0.68]` | 0.001204 | 0.002465 | — |
| `mcts` | 101 | 0 | 299 | 0.253 | `[0.21, 0.30]` | 0.045642 | 0.068296 | 359.0 |
| `random` | 0 | 0 | 400 | 0.000 | `[0.00, 0.01]` | 0.000011 | 0.000023 | — |

- **Nhận xét cho RQ1, RQ2 & lợi thế đi trước:**
  - **RQ1:** Ở cùng ngân sách thời gian suy nghĩ (`~46–54 ms/nước`), `alphabeta` (`score = 0.935–0.939`, ~156–157 nút/nước) thắng tuyệt đối `mcts` thuần rollout ngẫu nhiên (`100-0-0`), do không gian 81 ô của bàn 9×9 làm nhiễu playout ngẫu nhiên khi chưa có heuristic hoặc mạng học sâu dẫn hướng.
  - **RQ2:** Tác tử `cnn` Level 5 chỉ cần 1 lượt suy luận thẳng (`~1.1 ms/nước`, nhanh hơn `alphabeta`/`mcts` ~45 lần và nhanh hơn cả `heuristic`) nhưng đạt hạng 2 chung cuộc ở cả hai chế độ (`0.689` ở `compute`, `0.675` ở `time`), thắng tuyệt đối `random` (`100-0-0`) và `mcts` (`100-0-0`), **vượt `heuristic` đối đầu trực tiếp ở cả hai chế độ** (`54-8-38` tại `compute`, `47-16-37` tại `time`), đồng thời cầm hòa/thắng `31/100` ván (`4-27-69`) trước `alphabeta` độ sâu 3 ở chế độ `compute`.
  - **Cân bằng lượt đi:** Thiết kế đổi bên đối xứng cùng khai cuộc giữ tỷ lệ thắng giữa X và O cân bằng sát nhau (`compute`: X thắng `49.2%`, O thắng `47.2%`, hòa `3.6%`, độ dài trung bình `18.0` nước/ván; `time`: X thắng `49.6%`, O thắng `46.7%`, hòa `3.7%`).

## Ablation Tìm kiếm & Tác tử CNN Level 5 (Thành viên 1)

Chạy kiểm chứng Ablation 1 cho Minimax/Alpha-Beta. Cài PyTorch CPU để thử checkpoint CNN đi kèm hoặc huấn luyện lại:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.ablation_search --positions 20 -n 40 --seed 0
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -X utf8 -m scripts.play_cli cnn --seed 0
.\.venv\Scripts\python.exe -X utf8 -m train.train_cnn --games 600 --epochs 18 --seed 42
.\.venv\Scripts\python.exe -X utf8 -m arena.round_robin --agents random heuristic alphabeta mcts cnn -n 100 --seed 0 --matrix --run rr_compute_100
```

- **Ablation 1 (`scripts/ablation_search.py`, 20 thế trung cuộc và 40 ván/cặp).** Khi giữ cùng tập và thứ tự ứng viên, cắt tỉa Alpha-Beta giữ nguyên **20/20** lựa chọn và giảm **58,2%** số nút (1.110,0 xuống 464,0), từ 27,1 xuống 12,0 ms/nước. Cấu hình đầy đủ bật thêm ưu tiên chiến thuật và xếp hạng ứng viên. Cấu hình này duyệt trung bình 226,7 nút, mất 70,9 ms/nước và thắng 40/40 ván trước cấu hình tắt xếp hạng. Độ sâu 3 đạt điểm 0,5625 trước độ sâu 2 (13 thắng, 19 hòa, 8 thua).
- **Huấn luyện CNN Level 5 (`train/train_cnn.py`, `checkpoints/cnn_9x9.pt`).** Sinh 600 ván bao phủ khai cuộc toàn bàn (`legal_actions()`) với Alpha-Beta sâu 2, Heuristic và Random (252,2s trên CPU), tăng trọng số `3.5×` cho các thế thắng/chặn bắt buộc và che mặt nạ logit ô đã đánh ngay trong hàm mất mát. Tách nghiêm ngặt theo đơn vị ván (420 train, 90 validation, 90 test), loại 2.117 trạng thái trùng (`18.798` thế cờ duy nhất), rồi áp dụng 8 phép đối xứng D4 cho tập train để thu được `107.936` mẫu. Checkpoint tốt nhất ở epoch 7 (~415 KiB, thời gian train 356,2s) đạt **47,57% Top-1**, **69,72% Top-3** và **value MSE 0,2619** trên tập test độc lập.
- **Đối kháng chính thức 5 agent (2.000 ván = 1.000 `compute` + 1.000 `time`, 100 ván/cặp/chế độ).** `cnn` thắng tuyệt đối 200/200 ván trước `random` và 200/200 ván trước `mcts`, thắng đối đầu `heuristic` ở cả hai chế độ (`54-8-38` tại `compute`, `47-16-37` tại `time`), đồng thời đạt `4-27-69` (`compute`) và `5-20-75` (`time`) trước `alphabeta` độ sâu 3 dù không dùng tìm kiếm cây.

## Tiến độ các level

| Level | Agent | Trạng thái |
| --- | --- | --- |
| 1 | Random | Đã có, tên registry là `random` |
| 2 | Heuristic / Rule-based | Đã có, tên registry là `heuristic` |
| 3 | Minimax + Alpha-Beta | Đã có, tên registry là `alphabeta` |
| 4 | MCTS / UCT | Đã có, tên registry là `mcts` |
| 5 | CNN policy (+value), học có giám sát | Đã có, tên registry là `cnn` (`checkpoints/cnn_9x9.pt`) |
| 6 | Reinforcement Learning (self-play) | Bắt buộc tối thiểu 01 agent ở Level 5 hoặc 6 (khuyến khích làm cả 5 và 6) |
| 7 | AlphaGo-inspired | Khuyến khích (+điểm cộng nếu có thực nghiệm thuyết phục) |
| 8 | AlphaZero-inspired | Khuyến khích (+điểm cộng nếu có thực nghiệm thuyết phục) |

> **Lưu ý thuật ngữ:** Level 7–8 là phiên bản mô phỏng cảm hứng từ AlphaGo/AlphaZero ở quy mô bàn 9×9, cần ghi rõ các thành phần đã/chưa hiện thực và không dùng mạng chưa qua huấn luyện làm bằng chứng triển khai.

Tài liệu tham khảo cốt lõi cho thiết kế thuật toán và thực nghiệm:

- **Mark Liu**, *AlphaGo Simplified: Rule-Based AI and Deep Learning in Everyday Games* (CRC Press, 2024; file `Liu - Rule-Based AI Games.pdf` đính kèm gồm Phần I Ch. 1–8, mã nguồn Ch. 9–21 của sách tại `https://github.com/markhliu/AlphaGoSimplified`):
  - **Ch. 1–3:** Tách môi trường không đồ họa (tăng tốc train/arena) và bản có cửa sổ đồ họa (demo); chiến lược nhìn trước 1–3 bước (thắng ngay, chặn `block`, tránh nước tự mở đường thua `to_avoid`, tạo tấn công đôi `double attack`).
  - **Ch. 4–7:** Minimax đệ quy, cắt tỉa độ sâu, kiểm chứng thời gian tiết kiệm của Alpha-Beta và hàm lượng giá thế cờ `v(s) ∈ [-1, 1]` tại nút cắt độ sâu.
  - **Ch. 8:** MCTS/UCT (`c ≈ 1.4`) với 4 pha Selection–Expansion–Simulation–Backpropagation và khảo sát số lượt mô phỏng.
  - **Ch. 9–11:** Huấn luyện mạng CNN Policy có giám sát từ dữ liệu đối đầu chuyên gia (kết hợp MCTS và Minimax/Alpha-Beta).
  - **Ch. 12–15:** Học tăng cường tự chơi (Self-play Policy Gradient tinh chỉnh từ Policy Network, vector hóa) và huấn luyện Value Network dự đoán `P(thắng) - P(thua) ∈ [-1, 1]`.
  - **Ch. 16–21:** Tích hợp Policy/Value Network vào cây MCTS (AlphaGo-inspired) và mạng hai đầu Policy–Value + PUCT + đấu loại checkpoint (AlphaZero-inspired).
- **Stuart Russell & Peter Norvig**, *Artificial Intelligence: A Modern Approach* (4th ed., 2021): Mô hình hóa tác tử thông minh và tìm kiếm đối kháng (Adversarial Search).
- **Richard S. Sutton & Andrew G. Barto**, *Reinforcement Learning: An Introduction* (2nd ed., 2018): MDP, Monte Carlo, TD/Q-learning, Policy Gradient và tự chơi (Self-play).

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

## Bổ sung nhiệm vụ giai đoạn hoàn thiện cuối kỳ (3 thành viên)

Đối chiếu trạng thái repo hiện tại với đề cương `TTNTNC_De_tai_cuoi_ky_Game_AI.pdf`, sách *AlphaGo Simplified* (Mark Liu) và quy định nộp bài của giảng viên, các nghiệp vụ **chưa hoàn thiện** cần triển khai tiếp gồm:

1. **Bài toán & Câu hỏi nghiên cứu:** Phát biểu rõ tối thiểu 02 câu hỏi nghiên cứu định lượng (ví dụ: *RQ1 — Trong cùng ngân sách thời gian suy nghĩ mỗi nước trên bàn 9×9, MCTS/UCT có vượt Alpha-Beta không? RQ2 — Tác tử học được từ dữ liệu/tự chơi cải thiện tỷ lệ thắng thế nào so với heuristic tĩnh hoặc khi kết hợp MCTS?*) và phân tích không gian trạng thái Caro 9×9.
2. **Tác tử học được (Bắt buộc):** CNN Level 5 đã có pipeline, checkpoint đã huấn luyện và kết quả trên tập test tách theo ván. Bổ sung đường cong học từ log huấn luyện vào notebook báo cáo cuối kỳ.
3. **Đánh giá công bằng & Ablation (Bắt buộc):** Nâng giải đấu từ 12 ván smoke test lên **≥ 100 ván/cặp** (khuyến nghị 200 ván/cặp), đo đủ **02 chế độ ngân sách** (`compute` mặc định và `time` cùng giây/nước), bổ sung `score = (thắng + 0.5 × hòa) / tổng_ván`, độ trễ `p95`, số nút duyệt (`nodes`) / số mô phỏng (`simulations`), khoảng tin cậy 95% (Wilson/Bootstrap) và **tối thiểu 02 nghiên cứu cắt giảm/độ nhạy (ablation/sensitivity)**.
4. **Giao diện đồ họa & Học liệu nộp:** Giao diện đồ họa chơi Người–Máy & Máy–Máy trên Web (`ui/web_index.html`, `scripts/web_app.py`, `run_caro.bat`) và notebook sinh bảng/biểu đồ (`notebooks/analysis.ipynb`) đã được Thành viên 3 triển khai; nhóm cần hoàn thiện nốt Ablation 2 của MCTS, video demo, báo cáo 5 chương (bản mềm + 01 bản in), slide, poster và lịch sử GitHub minh bạch.

### Thành viên 1 · Tối ưu/Ablation Tìm kiếm & Tác tử CNN Học có giám sát (Level 5)

- **PR 3 — `feat/ablation-search` (Hoàn thiện Level 2–3 theo Liu Ch. 2–7).**
  - Trong `agents/heuristic.py`: Tài liệu hóa rõ thứ tự ưu tiên luật, xử lý xung đột luật và phân tích các thế tấn công đôi (open-three / open-four) hoặc nước đi mở đường thua sau 2 bước (tương tự cơ chế chặn/tránh ở Liu Ch. 3).
  - Trong `agents/alphabeta.py`: Bổ sung bộ đếm `last_nodes` (số nút duyệt mỗi nước) và tham số `use_pruning: bool = True`, `use_ordering: bool = True` để thực hiện **Ablation 1**: so sánh Minimax không cắt tỉa với Alpha-Beta có cắt tỉa (kiểm chứng chọn cùng nước tối ưu nhưng giảm số nút và thời gian như Liu Ch. 6), đồng thời khảo sát `depth=2` vs. `depth=3`.
- **PR 4 — `feat/cnn` (Bắt buộc phạm vi học máy — Level 5 theo Liu Ch. 9–11 & Ch. 15).**
  - Pipeline trong `train/` dùng Alpha-Beta độ sâu 2 để gán nhãn nước đi chuyên gia cho tensor `Gomoku.encode()` kích thước `(3, 9, 9)`. Các ván sinh dữ liệu ghép Alpha-Beta với Alpha-Beta, Heuristic hoặc Random. Nhánh value dùng kết quả ván theo góc nhìn bên sắp đi. Pipeline chia `train/validation/test` theo ván trước khi khử các trạng thái trùng và dùng validation để chọn checkpoint.
  - Huấn luyện mạng CNN bằng PyTorch, che mặt nạ các ô không hợp lệ (`legal_actions` mask) khi suy luận để đảm bảo không sinh nước đi lỗi, lưu lịch sử loss/accuracy theo epoch vào `logs/`, lưu trọng số đã train vào `checkpoints/` (< 50 MB hoặc kèm link tải), khai báo CPU/GPU và thời gian train.
  - Tạo `agents/cnn.py` + `agents/test_cnn.py`, đăng ký tên `cnn` trong `agents/registry.py` (kèm kiểm thử hợp lệ, thắng/chặn cơ bản, thắng Random).
- **Báo cáo & Học liệu phụ trách:** Viết Chương 2 (Heuristic, Minimax/Alpha-Beta, CNN), Chương 3 (biểu diễn trạng thái, thiết kế Level 2, 3, 5, quy trình sinh dữ liệu & huấn luyện) và nội dung kỹ thuật cho Poster.
- **Nghiệm thu TV1:** Có bảng số liệu + biểu đồ Ablation 1 (bật/tắt cắt tỉa, depth 2 vs. 3); checkpoint `cnn` nạp chạy lại được từ lệnh mẫu, đạt kết quả thực nghiệm thật trước `random` và `heuristic`.

### Thành viên 2 · MCTS theo thời gian, Ablation 2, Video Demo & Tùy chọn Self-play RL (Level 6)

- **PR 3 — `feat/mcts-time` (Hoàn thiện Level 4 theo Liu Ch. 8 — Bắt buộc).**
  - Trong `agents/mcts.py`: Bổ sung tùy chọn ngân sách thời gian mỗi nước (`time_limit: float | None = None`) bên cạnh `simulations`, lưu lại số mô phỏng thực tế đã chạy (`last_simulations`) để so sánh công bằng với Alpha-Beta trong chế độ `budget_mode="time"` (có thể khảo sát thêm thu hẹp nhánh mở rộng bằng `candidate_moves`).
  - Thực hiện **Ablation 2**: Khảo sát độ nhạy tỷ lệ thắng và độ trễ của MCTS theo ngân sách mô phỏng (`simulations` ∈ {100, 400, 1000, 2000}) và hằng số khám phá `c` ∈ {0.7, 1.4, 2.0}.
- **PR 4 (Tùy chọn cộng điểm) — `feat/rl` (Level 6 Self-play Policy Gradient theo Liu Ch. 13–15).**
  - Nếu mở rộng thêm Level 6, khởi tạo từ checkpoint `cnn_9x9.pt` đã huấn luyện rồi tinh chỉnh bằng **Self-play Policy Gradient** để lưu đường cong học tập tự chơi và đối chiếu với bản học có giám sát.
- **Video Demo, Báo cáo & Học liệu phụ trách:** Quay **Video Demo** hoạt động thực tế của hệ thống (trên giao diện Web 1-Click & CLI) kèm bộ ảnh chụp các thế cờ chiến thuật/lỗi điển hình của từng cấp AI; viết Chương 2 (MCTS/UCT & RL nếu có), Chương 3 (thiết kế Level 4 và demo CLI), phụ trách chính Slide thuyết trình và kịch bản trình diễn trực tiếp.
- **Nghiệm thu TV2:** Chế độ giới hạn giây/nước của MCTS hoạt động ổn định; có đủ số liệu + log cho **Ablation 2**; có video demo và slide hoàn chỉnh.

### Thành viên 3 · Giải đấu chuẩn cuối kỳ, Giao diện Web 1-Click & Deploy, Level 7 (MCTS + CNN), Notebook Phân tích & Quản trị GitHub

- **PR 2 — `feat/eval-suite` (Đã triển khai & hợp nhất).**
  - Đã merge `feat/arena` vào `main` (PR #7) và nâng cấp `arena/round_robin.py` (PR #8): hỗ trợ giải đấu **≥ 100 ván/cặp** ở cả 2 chế độ `compute` và `time`, tính `score`, khoảng tin cậy **Wilson 95%**, thời gian trung bình & **P95** tách riêng từng agent, thống kê `nodes`/`simulations`, ma trận đối đầu (`--matrix`) và thống kê lợi thế đi trước.
- **PR 3 — `feat/notebooks` (Đã triển khai cho 5 agent Level 1–5; mở rộng lên Level 7 & Ablation 2).**
  - Xây dựng [notebooks/analysis.ipynb](notebooks/analysis.ipynb) và bộ hình minh họa trong `notebooks/figures/` đọc trực tiếp từ `logs/*.jsonl` (ma trận đối đầu, `score` + CI 95%, độ trễ P95, lợi thế đi trước, đường cong huấn luyện `cnn` và Ablation 1).
- **PR 4 — `feat/web-deploy` (Giao diện đồ họa Người–Máy & Máy–Máy trên Web, Chạy 1-Click & Deploy không cần Docker — Đã triển khai & hợp nhất ở PR #11).**
  - Đảm nhận toàn bộ phần **Giao diện đồ họa tương tác Người–Máy & Máy–Máy** thông qua máy chủ [scripts/web_app.py](scripts/web_app.py) (`ThreadingHTTPServer` chuẩn Python, không thêm dependency ngoài) và giao diện lưới ô vuông [ui/web_index.html](ui/web_index.html) kèm bộ kiểm thử [scripts/test_web_app.py](scripts/test_web_app.py): chọn mọi cấp độ AI trong `registry`, chọn quân X/O, xem trực quan từng bước, thống kê trực tiếp và lưu/xem lại/tải log lịch sử trận đấu (`logs/web_matches.jsonl`).
  - Cung cấp bộ khởi chạy 1 lần nhấp chuột [run_caro.bat](run_caro.bat) (Windows) / [run_caro.sh](run_caro.sh) (macOS/Linux) tự kiểm tra `.venv` và mở trình duyệt, cùng cấu hình [render.yaml](render.yaml) để deploy Web trực tiếp lên Render không cần Docker.
- **PR 5 — `feat/mcts-cnn` (Level 7 AlphaGo/AlphaZero-inspired: Tích hợp mạng CNN Policy–Value dẫn hướng cây MCTS theo PUCT).**
  - Xây dựng tác tử `mcts_cnn` kết hợp đầu `policy` (xác suất tiên nghiệm `P(s, a)`) và đầu `value` (`V(s) ∈ [-1, 1]` thay rollout ngẫu nhiên) từ checkpoint `checkpoints/cnn_9x9.pt` vào cây tìm kiếm PUCT có kiểm tra thắng/chặn chiến thuật và hỗ trợ `time_limit`; so sánh trực tiếp `cnn` đơn thuần (`policy-only`) với `mcts_cnn` (`policy + value + MCTS`) để trả lời trọn vẹn **RQ2**.
- **Quản trị GitHub, Kiểm định tái lập & Tổng hợp hồ sơ nộp (Nhóm trưởng/Điều phối).**
  - Mở đầy đủ **GitHub Issues / Projects** gắn nhãn và phân công cho từng PR của 3 thành viên; duy trì lịch sử commit đều đặn hàng tuần và kiểm tra **GitHub Insights** (không dồn code lên sát hạn nộp).
  - Kiểm thử chạy lại toàn bộ dự án trên môi trường ảo sạch từ đầu theo đúng `README.md` (cài gói → `pytest` → sinh dữ liệu/train mẫu hoặc nạp checkpoint → chạy round-robin → mở CLI & Web 1-Click).
  - Viết Chương 1 (giới thiệu, mô hình hóa bài toán, câu hỏi nghiên cứu), Chương 2–3 (phần kiến trúc hệ thống, Arena, giao diện Web/Deploy & tích hợp Level 7 PUCT MCTS+CNN), Chương 4 (tổng hợp kết quả thực nghiệm & thảo luận), Chương 5 (kết luận & hướng phát triển); kiểm tra trích dẫn học thuật; in ấn **01 cuốn báo cáo + slide + poster** và đóng gói file ZIP nộp bài.
- **Nghiệm thu TV3:** Log thi đấu thô ≥ 100 ván/cặp ở cả 2 chế độ ngân sách khớp tuyệt đối với bảng/biểu đồ xuất từ `notebooks/`; giao diện Web 1-Click chọn được đủ các cấp AI; `mcts_cnn` vượt rõ rệt `mcts` và `cnn` đơn lẻ; toàn bộ sản phẩm trong checklist nộp bài chạy lại không lỗi.

### Danh sách thành viên và tỷ lệ đóng góp (Cập nhật trước khi nộp)

> Theo yêu cầu nộp bài của giảng viên, nhóm kê khai đầy đủ Họ tên, MSSV, nhiệm vụ, công việc thực tế và tỷ lệ đóng góp sao cho **tổng tỷ lệ đóng góp bằng đúng 100%** (lịch sử GitHub và kết quả thực hiện là căn cứ đối chiếu):

| STT | Họ và tên | MSSV | Tài khoản GitHub | Nhiệm vụ & công việc thực hiện chính | Tỷ lệ đóng góp (%) |
| :-: | --- | --- | --- | --- | --: |
| 1 | *(Điền họ tên TV1)* | *(Điền MSSV)* | *(Điền username)* | Level 2 (`heuristic`), Level 3 (`alphabeta` + đếm nút & ablation cắt tỉa), Level 5 (`cnn` + sinh dữ liệu & huấn luyện), Chương 2–3 báo cáo & nội dung Poster | 33.3% |
| 2 | *(Điền họ tên TV2)* | *(Điền MSSV)* | *(Điền username)* | Level 4 (`mcts` + giới hạn thời gian & Ablation 2 theo số mô phỏng/`c`), CLI (`play_cli`), Video demo & ảnh tình huống chiến thuật, tùy chọn Level 6 (`rl`), Chương 2–3 (MCTS/CLI) & Slide thuyết trình | 33.3% |
| 3 | *(Điền họ tên TV3 — Nhóm trưởng)* | *(Điền MSSV)* | *(Điền username)* | Engine `game/`, `arena/` (round-robin ≥ 100 ván/cặp, 2 chế độ ngân sách, `p95`/CI), Giao diện Web 1-Click & Deploy (`ui/web_index.html`, `scripts/web_app.py`, `run_caro.bat`, `render.yaml`), Level 7 (`mcts_cnn` PUCT), `notebooks/` phân tích & biểu đồ, quản lý GitHub, Chương 1–5 & hồ sơ nộp | 33.4% |
| **Tổng** | | | | **Toàn bộ các thành viên nắm rõ và giải thích được phần việc phụ trách** | **100%** |

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

Lưu ý bắt buộc theo quy định quản lý mã nguồn của giảng viên:

- Cấu hình thống nhất `git config user.name` và `git config user.email` khớp tài khoản GitHub cá nhân để lịch sử commit và **GitHub Insights** phản ánh chính xác người thực hiện, nội dung và tiến độ.
- Cập nhật thường xuyên mã nguồn, notebook (`notebooks/`) và tài liệu xuyên suốt quá trình làm đồ án; **không dồn toàn bộ mã nguồn lên GitHub vào sát ngày nộp**.
- Khai thác đầy đủ `README.md`, **Issues/Projects**, **Branch/Pull Request** và **GitHub Insights** để quản lý công việc và minh chứng đóng góp.

## Cấu trúc thư mục

| Thư mục | Nội dung |
| --- | --- |
| `game/` | Engine Gomoku và test |
| `agents/` | Giao diện Agent, registry và các bot |
| `arena/` | Chạy một ván và giải đấu vòng tròn `round-robin` |
| `scripts/` | Lệnh chạy thử và demo terminal |
| `configs/`, `utils/` | Cấu hình, seed và logger JSONL |
| `train/`, `ui/` | Huấn luyện mạng nơ-ron/RL (`train/`) và giao diện Web (`ui/web_index.html`) |
| `logs/`, `checkpoints/`, `notebooks/` | Kết quả thực nghiệm, trọng số đã train và notebook phân tích |
| `docs/` | Quy ước nhóm |

## Nộp bài cuối kỳ

### 1. Sản phẩm bắt buộc trong 01 file ZIP điện tử (chỉ nhóm trưởng nộp đại diện)

- **Quy tắc đặt tên file ZIP:** Đặt theo thông báo nộp bài trên hệ thống của giảng viên `Nhom??_TenDeTai_HoTen_MaSV.zip` (ví dụ: `Nhom03_GameAI_Caro9x9_NguyenVanA_3124123456.zip`; đối chiếu thêm mẫu trong đề cương PDF `NhomXX_TenGame_TTNTNC_HoTen_MaSV.zip` nếu cổng nộp yêu cầu).
- **Tài liệu tổng kết:** Báo cáo cuối kỳ hoàn chỉnh (đủ 5 chương theo đề cương), slide thuyết trình và poster giới thiệu đề tài.
- **Mã nguồn & cấu hình tái lập:** Toàn bộ mã nguồn Python, `configs/default.json`, `requirements.txt`, bộ kiểm thử tự động (`pytest`), cùng hướng dẫn cài đặt/train/evaluate/demo trong `README.md` đảm bảo **chạy lại được từ đầu**.
- **Dữ liệu:** Dataset sinh ván cờ (nếu dung lượng nhỏ) hoặc script sinh dữ liệu kèm đường dẫn truy cập dữ liệu.
- **Tài nguyên thực nghiệm & minh họa:** Jupyter Notebook sinh bảng/biểu đồ (`notebooks/`), trọng số mô hình đã huấn luyện (`checkpoints/`), log thi đấu thực nghiệm (`logs/`), hình ảnh minh họa, **video demo** và danh mục tài liệu tham khảo có trích dẫn rõ phần tự cài đặt/kế thừa.
- **Hồ sơ đóng góp & GitHub:** Đường dẫn GitHub Repository chính của đề tài và bảng danh sách thành viên (Họ tên, MSSV, nhiệm vụ, công việc thực hiện, tỷ lệ đóng góp `%` có **tổng bằng 100%**).

### 2. Bản cứng và yêu cầu bảo vệ

- Chuẩn bị thêm **01 cuốn báo cáo in**, slide thuyết trình và poster khi báo cáo cuối kỳ.
- Chỉ báo cáo các thí nghiệm và mô hình đã thực sự chạy (kèm cấu hình, `seed`, ngân sách tính toán và số ván). Mỗi thành viên phải nắm rõ và giải thích được phần công việc của mình; lịch sử GitHub và kết quả thực hiện là căn cứ đánh giá mức độ đóng góp cá nhân.
