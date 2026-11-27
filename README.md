# Gomoku (Caro) 9×9 – Multi-level Game AI

Đồ án cuối kỳ *Trí tuệ nhân tạo nâng cao*. Nhóm xây dựng và so sánh các agent chơi Gomoku 9×9. Bàn cờ dùng luật freestyle. Từ 5 quân liên tiếp theo hàng, cột hoặc đường chéo là thắng. Bàn đầy mà chưa có bên thắng thì hòa.

## Mô hình hóa bài toán & Câu hỏi nghiên cứu

- **Tính chất môi trường:** Gomoku 9×9 freestyle (`k = 5`, chấp nhận chuỗi ≥ 5) là trò chơi hai người chơi luân phiên (`X = +1` đi trước, `O = -1` đi sau), **quan sát đầy đủ**, **xác định**, **tổng bằng không** và **hữu hạn** (tối đa 81 nước; cận trên không gian cấu hình `3^81 ≈ 4.43 × 10^38`, hệ số rẽ nhánh đầu ván là 81).
- **Trạng thái, hành động & phần thưởng:** Trạng thái lưu bằng lưới `board[9, 9] ∈ {-1, 0, 1}` cùng người sắp đi `player ∈ {+1, -1}` (hoặc tensor bất biến lượt đi `encode()` kích thước `(3, 9, 9)`). Hành động hợp lệ `a = 9r + c ∈ [0, 80]` tại các ô trống; phần thưởng cuối ván từ góc nhìn người chơi là `+1` (thắng), `-1` (thua), `0` (hòa).
- **Câu hỏi nghiên cứu trọng tâm:**
  - **RQ1:** Trên bàn Caro 9×9, trong cùng ngân sách thời gian suy nghĩ mỗi nước (`~50–65 ms/nước`), MCTS/UCT với rollout ngẫu nhiên có vượt Minimax + Alpha-Beta dùng hàm lượng giá cửa sổ `4^n` hay không?
  - **RQ2:** Tác tử học từ dữ liệu/tự chơi (Level 5 CNN / Level 6 RL) cải thiện tỷ lệ thắng thế nào so với heuristic tĩnh hoặc khi tích hợp dẫn hướng cho cây MCTS?

## Giao diện Web

- **Windows:** Chạy [run_caro.bat](run_caro.bat) tại thư mục gốc để tự động chuẩn bị `.venv`, cài gói cần thiết và mở trình duyệt với bàn cờ Caro 9×9 (hỗ trợ cả **Người đấu AI** và **AI đấu AI**).
- **macOS / Linux:** Chạy `bash run_caro.sh` (hoặc gọi trực tiếp `.\.venv\Scripts\python.exe -X utf8 -m ui.web_app`).
- **Triển khai trực tuyến:** File [render.yaml](render.yaml) cấu hình sẵn dịch vụ Web Python trên Render (`0.0.0.0:$PORT`, endpoint `/healthz`).

## Chạy qua dòng lệnh (CLI & Kiểm thử)

Cần Python 3.10 trở lên; khuyến nghị Python 3.13 khi chạy CNN/MCTS-CNN với PyTorch CPU. Mở PowerShell tại thư mục gốc của repo rồi chạy:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install numpy pytest
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.quick_match random random -n 20
.\.venv\Scripts\python.exe -m scripts.quick_match alphabeta heuristic -n 20 --seed 0
.\.venv\Scripts\python.exe -m arena.round_robin --agents random heuristic alphabeta mcts --seed 0
```

Trên Linux hoặc macOS, dùng `python3 -m venv .venv` và thay đường dẫn Python bằng `.venv/bin/python`. Khi chạy phần mạng CNN/MCTS-CNN hoặc xuất biểu đồ, cài thêm các gói trong [requirements.txt](requirements.txt). GPU là tùy chọn.

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

Factory nhận `seed`, `simulations` (số nguyên dương) và `c` (hữu hạn, không âm). Mặc định của lớp là 100 mô phỏng; cấu hình chung hiện tại dùng 400. CLI cho phép ghi đè để chạy demo nhanh. Ở chế độ cố định số mô phỏng, cùng seed, cấu hình và chuỗi lời gọi cho cùng nước đi; chế độ thời gian còn phụ thuộc tốc độ máy. Rollout dùng nước ngẫu nhiên, chưa có đánh giá học máy; ngân sách mô phỏng thấp có thể bỏ sót chiến thuật sâu. MCTS hiện hỗ trợ thêm `time_limit` và bộ đếm `last_simulations`; hướng dẫn ở phần bên dưới.

Kiểm tra thực tế trên nhánh này (15/11/2026, Python 3.15.1, NumPy 2.5.4):

- `pytest -q`: **48 test đạt**, gồm chiến thuật thắng/chặn, cùng seed, giữ nguyên đầu vào, góc nhìn UCT/cập nhật ngược, ván hòa và các trường hợp nhập terminal.
- Lệnh `quick_match` ở trên: **MCTS thắng 12, thua 0, hòa 0** trước Random; 400 mô phỏng/nước, `c=1.4`, seed gốc 0, đổi bên từng ván và 2 nước khai cuộc ngẫu nhiên theo runner hiện có. Đây là mẫu kiểm tra nhỏ, chưa phải đánh giá sức mạnh tổng quát.
- Chạy `scripts.play_cli random --seed 0` qua đầu vào terminal đã chuẩn bị: kết thúc sau 9 nước, người chơi X thắng; đã thử sai định dạng, tọa độ âm/ngoài bàn và ô đã có quân.

## MCTS theo thời gian và Ablation 2 (Thành viên 2)

MCTS nhận thêm `time_limit` (giây/nước, mặc định `None`). Khi đặt cả `simulations` và `time_limit`, bot dừng khi chạm một trong hai giới hạn. Thời gian được tính từ đầu `select_action()`; bot vẫn hoàn thành kiểm tra thắng/chặn ở gốc và mô phỏng đã bắt đầu. Đây là giới hạn mềm, có thể vượt ngân sách bởi chi phí kiểm tra chiến thuật và một rollout. Nếu chưa kịp bắt đầu rollout nào, bot trả một nước hợp lệ bằng RNG đã nhận seed.

`last_simulations` được đặt lại sau mỗi lời gọi và chỉ đếm rollout đã hoàn thành. Nước thắng/chặn trực tiếp có giá trị 0. Arena tự truyền `time_limit` ở chế độ `time`, đồng thời ghi số mô phỏng thực tế thay vì ngân sách khai báo. Kết quả giải đấu 2.000 ván bên dưới là thí nghiệm trước thay đổi này, dùng hiệu chuẩn số mô phỏng; cần tạo run mới khi đánh giá MCTS theo thời gian trực tiếp.

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.play_cli mcts --side o --seed 0 --simulations 2000 --time-limit 0.05
.\.venv\Scripts\python.exe -X utf8 -m arena.round_robin --agents mcts heuristic -n 100 --budget-mode time --seconds-per-move 0.05 --simulations 100000 --seed 0 --run rr_mcts_native_time_100
.\.venv\Scripts\python.exe -X utf8 -m scripts.ablation_mcts -n 40 --seed 0 --run mcts_sensitivity_40
```

Ablation 2 khảo sát đủ `simulations ∈ {100, 400, 1000, 2000}` và `c ∈ {0.7, 1.4, 2.0}`, đối đầu Random và Heuristic. Mỗi cấu hình chạy 40 ván/đối thủ, đổi X/O theo cặp với cùng khai cuộc và seed giữa các cấu hình. Tổng cộng 24 cấu hình đối đầu, 960 ván. Có thể thêm `--opponents random heuristic alphabeta` hoặc tăng `-n` để mở rộng.

Log thô nằm ở `logs/<run>_s<simulations>_c<c>_vs_<opponent>.jsonl`; `logs/<run>.jsonl` chứa thông tin môi trường và bảng tổng hợp điểm, CI Wilson 95%, thời gian trung bình, P95 và số mô phỏng thực tế. Runner từ chối tên run đã tồn tại để tránh gộp nhầm thí nghiệm. Dùng `python -X utf8 -m scripts.summarize_mcts logs/mcts_sensitivity_40.jsonl` để đối chiếu log thô và xuất CSV cho notebook. Xem [docs/MCTS_ABLATION.md](docs/MCTS_ABLATION.md) cho kết quả và cách đọc số liệu.

Run `mcts_sensitivity_40` đã hoàn tất 960 ván: MCTS thắng 40/40 trước Random ở mọi cấu hình; kết quả tốt nhất trước Heuristic là 3–0–37 tại 2.000 mô phỏng, `c=0.7`. Kiểm tra riêng 100 ván với deadline 50 ms có P95 50,99 ms.

Kiểm thử toàn bộ dự án đạt 128 test trên Python 3.13.2, NumPy 2.3.3 và PyTorch 2.13.0+cpu, bao gồm CNN và MCTS-CNN. Chạy lại bằng `python -m pytest -q` trong môi trường đã cài PyTorch.

Thiết kế chi tiết ở [MCTS_DESIGN.md](docs/MCTS_DESIGN.md); kịch bản quay và nội dung trình bày ở [MCTS_DEMO.md](docs/MCTS_DEMO.md).

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

## Tác tử Level 7: PUCT kết hợp MCTS + CNN (`mcts_cnn` — Thành viên 3)

Module [agents/mcts_cnn.py](agents/mcts_cnn.py) tái sử dụng trực tiếp checkpoint hai đầu [checkpoints/cnn_9x9.pt](checkpoints/cnn_9x9.pt) để dẫn hướng cây tìm kiếm theo công thức **PUCT** (`simulations=56`, `c_puct=1.5`, `max_children=12`, hỗ trợ gốc `time_limit` và `last_simulations`):

- **Thành phần đã hiện thực:** (1) Đầu `policy` cung cấp xác suất tiên nghiệm `P(s, a)` thu hẹp tập ứng viên cục bộ `candidate_moves(2)`; (2) Đầu `value` `V(s) ∈ [-1, 1]` thay thế hoàn toàn rollout ngẫu nhiên tại nút lá; (3) Phát hiện chính xác thắng 1 nước và thế tứ mở không thể cản (`≥ 2` điểm thắng) ngay khi mở rộng nút.
- **Thành phần chưa hiện thực so với AlphaZero đầy đủ:** Chưa chạy vòng lặp tự chơi sinh cây MCTS nhiều thế hệ kèm nhiễu Dirichlet ở gốc và đấu loại cập nhật checkpoint (mạng vẫn dùng trọng số học có giám sát từ `train_cnn.py`).
- **Thực nghiệm kiểm chứng RQ2 (`--agents heuristic alphabeta mcts cnn mcts_cnn -n 20 --seed 0`, 200 ván):** Ở cùng ngân sách thời gian mỗi nước với `mcts` và `alphabeta` (`55,6 ms/nước`, P95 `83,5 ms`, trung bình `49,9` mô phỏng/nước), `mcts_cnn` đạt `score = 0.731` (`47-23-10`): thắng tuyệt đối `mcts` (`20-0-0`), áp đảo `heuristic` (`17-2-1`, `score = 0.90`), **bất bại trước `cnn` đơn thuần (`9-11-0`, `score = 0.725`)**, và nâng điểm đối đầu trước `alphabeta` độ sâu 3 gấp 4 lần so với `cnn` đơn lẻ (từ `0.075` lên **`0.300`**, `1 thắng – 10 hòa – 9 thua`).

## Tiến độ các level

| Level | Agent | Trạng thái |
| --- | --- | --- |
| 1 | Random | Đã có, tên registry là `random` |
| 2 | Heuristic / Rule-based | Đã có, tên registry là `heuristic` |
| 3 | Minimax + Alpha-Beta | Đã có, tên registry là `alphabeta` |
| 4 | MCTS / UCT | Đã có, tên registry là `mcts` |
| 5 | CNN policy (+value), học có giám sát | Đã có, tên registry là `cnn` (`checkpoints/cnn_9x9.pt`) |
| 6 | Reinforcement Learning (self-play) | Tùy chọn mở rộng (`feat/rl` — Thành viên 2) |
| 7 | AlphaGo-inspired (PUCT MCTS + CNN) | Đã có, tên registry là `mcts_cnn` (`agents/mcts_cnn.py`) |
| 8 | AlphaZero-inspired | Khuyến khích (+điểm cộng nếu có vòng lặp tự chơi MCTS) |

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

## Phân công & Tiến độ giai đoạn hoàn thiện cuối kỳ (3 thành viên)

Đối chiếu trạng thái nhánh `main` hiện tại (`127 passed`) với đề cương `TTNTNC_De_tai_cuoi_ky_Game_AI.pdf`, sách *AlphaGo Simplified* (Mark Liu) và quy định nộp bài của giảng viên:

1. **Bài toán & Câu hỏi nghiên cứu (Đã hoàn thành):** Đã phát biểu rõ **RQ1** và **RQ2** kèm phân tích không gian trạng thái Caro 9×9.
2. **Tác tử học được & Nâng cao (Đã hoàn thành):** Đã hoàn thiện cả **Level 5 (`cnn`)** và **Level 7 (`mcts_cnn` PUCT)** dùng checkpoint đã huấn luyện [checkpoints/cnn_9x9.pt](checkpoints/cnn_9x9.pt) cùng đường cong học tập trong `notebooks/figures/`.
3. **Đánh giá công bằng & 02 Ablation (Đã hoàn thành):** Đã hoàn tất giải đấu **2.000 ván** (`100` ván/cặp ở cả 2 chế độ `compute` và `time`), **Ablation 1** cho Minimax/Alpha-Beta (`scripts/ablation_search.py`) và **Ablation 2** 960 ván cho MCTS ([docs/MCTS_ABLATION.md](docs/MCTS_ABLATION.md)).
4. **Giao diện đồ họa & Học liệu nộp cuối kỳ (Đang hoàn thiện học liệu):** Giao diện Web (`ui/web_app.py`, `ui/web_index.html`) và notebook biểu đồ (`notebooks/analysis.ipynb`) đã hoàn tất; video, bộ ảnh và slide toàn dự án của TV2 nằm ở [docs/PROJECT_DEMO.md](docs/PROJECT_DEMO.md). Nhóm tiếp tục rà soát học liệu, hoàn thiện **Báo cáo cuối kỳ 5 chương (TV1)** và **Poster + Hồ sơ ZIP nộp bài (TV3)**.

### Thành viên 1 · Tối ưu/Ablation Tìm kiếm, Tác tử CNN (Level 5) & Viết Báo cáo cuối kỳ

- **PR 3 — `feat/ablation-search` (Đã triển khai & hợp nhất ở PR #9).**
  - Hoàn thiện `agents/heuristic.py`, bổ sung bộ đếm `last_nodes` và cờ `use_pruning`, `use_ordering` trong `agents/alphabeta.py`; thực hiện **Ablation 1** (`scripts/ablation_search.py`: cắt tỉa giảm `58,2%` số nút giữ nguyên 20/20 nước chọn, khảo sát `depth=2` vs. `depth=3`).
- **PR 4 — `feat/cnn` (Đã triển khai & hợp nhất ở PR #10, nâng cấp ở PR #12).**
  - Xây dựng pipeline `train/train_cnn.py`, tác tử `agents/cnn.py` + `tests/test_cnn.py` và checkpoint `checkpoints/cnn_9x9.pt` tách nghiêm ngặt `train/val/test` theo ván, che mặt nạ nước bất hợp lệ và lưu log theo epoch.
- **Nhiệm vụ trọng tâm còn lại — Viết Báo cáo cuối kỳ hoàn chỉnh (5 chương):**
  - **Chủ trì biên soạn toàn bộ Báo cáo cuối kỳ 5 chương** theo đúng cấu trúc đề cương: Chương 1 (giới thiệu, mô hình hóa Caro 9×9, RQ1 & RQ2), Chương 2 (cơ sở lý thuyết Heuristic, Minimax/Alpha-Beta, MCTS/UCT, CNN & PUCT), Chương 3 (kiến trúc hệ thống, thiết kế Level 1–7, Arena & giao diện Web), Chương 4 (tổng hợp thực nghiệm 2.000 ván, Ablation 1, Ablation 2 từ [docs/MCTS_ABLATION.md](docs/MCTS_ABLATION.md), kết quả Level 7 & thảo luận), Chương 5 (kết luận, hạn chế & hướng phát triển), kèm danh mục tài liệu tham khảo chuẩn học thuật (bản mềm + file in **01 cuốn báo cáo cứng**). *(TV2 và TV3 rà soát lại phần thuật toán mình phụ trách để cả nhóm nắm vững khi bảo vệ).*
- **Nghiệm thu TV1:** Có đủ số liệu Ablation 1 và checkpoint `cnn`; hoàn thành trọn vẹn cuốn Báo cáo cuối kỳ 5 chương khớp 100% với số liệu thực nghiệm trong repo.

### Thành viên 2 · MCTS theo thời gian, Ablation 2, Video Demo & Slide thuyết trình

- **PR 3 — `feat/mcts-time` (Đã triển khai & hợp nhất ở PR #16).**
  - Bổ sung `time_limit` và `last_simulations` trong `agents/mcts.py`, tích hợp CLI & Arena; thực hiện **Ablation 2** (`scripts/ablation_mcts.py`, `scripts/summarize_mcts.py`, 960 ván trên lưới `simulations` ∈ `{100, 400, 1000, 2000}` × `c` ∈ `{0.7, 1.4, 2.0}`) cùng tài liệu [docs/MCTS_DESIGN.md](docs/MCTS_DESIGN.md) và [docs/MCTS_ABLATION.md](docs/MCTS_ABLATION.md).
- **PR 4 (Tùy chọn cộng điểm) — `feat/rl` (Level 6 Self-play Policy Gradient theo Liu Ch. 13–15).**
  - Tùy chọn không bắt buộc (nhóm đã có Level 5 `cnn` và Level 7 `mcts_cnn`).
- **Video demo, ảnh tình huống và slide thuyết trình:**
  - Học liệu toàn dự án tại [docs/PROJECT_DEMO.md](docs/PROJECT_DEMO.md): video Web và CLI, bộ ảnh cho sáu agent đã triển khai, 18 slide có lời dẫn và nguồn đối chiếu, cùng kịch bản trình diễn trực tiếp. Các thế kiểm thử được ghi nhãn; kết quả đối kháng trích riêng từ notebook, README và log của từng run.
- **Nghiệm thu TV2:** `time_limit` và **Ablation 2** đã xanh `pytest`; đã bổ sung video, ảnh chiến thuật và slide toàn dự án để nhóm rà soát trước khi bảo vệ.

### Thành viên 3 · Giải đấu chuẩn, Giao diện Web, Level 7 (`mcts_cnn`), Poster & Hồ sơ nộp

- **PR 2 — `feat/eval-suite` (Đã triển khai & hợp nhất ở PR #7, #8, #12).**
  - Xây dựng `arena/round_robin.py` hỗ trợ 2 chế độ ngân sách (`compute` & `time`), Wilson 95% CI, độ trễ P95, ma trận đối đầu và chạy giải đấu chuẩn 2.000 ván.
- **PR 3 — `feat/notebooks` (Đã triển khai & hợp nhất ở PR #8, #12).**
  - Xây dựng [notebooks/analysis.ipynb](notebooks/analysis.ipynb) và xuất 4 bộ biểu đồ PNG trong `notebooks/figures/` từ log JSONL.
- **PR 4 — `feat/web-deploy` (Đã triển khai & hợp nhất ở PR #11, #13).**
  - Xây dựng giao diện Web Người–Máy & Máy–Máy ([ui/web_app.py](ui/web_app.py), [ui/web_index.html](ui/web_index.html), [tests/test_web_app.py](tests/test_web_app.py)), script khởi chạy [run_caro.bat](run_caro.bat) / [run_caro.sh](run_caro.sh) và cấu hình [render.yaml](render.yaml).
- **PR 5 — `feat/mcts-cnn` (Đã triển khai & hợp nhất ở PR #13).**
  - Xây dựng tác tử Level 7 [agents/mcts_cnn.py](agents/mcts_cnn.py) (PUCT + Policy–Value CNN) và chuẩn hóa cấu trúc thư mục `tests/`.
- **Nhiệm vụ trọng tâm còn lại — Poster, Quản trị GitHub & Đóng gói nộp bài (Nhóm trưởng):**
  - Thiết kế **Poster** giới thiệu đề tài; rà soát **GitHub Issues / Insights**; kiểm thử chạy lại toàn bộ dự án từ đầu; tổng hợp đủ sản phẩm từ TV1 (Báo cáo 5 chương) & TV2 (Video + Slide), điền bảng thông tin thành viên, in ấn học liệu bảo vệ và đóng gói **01 file ZIP nộp bài** đại diện nhóm.
- **Nghiệm thu TV3:** Toàn bộ mã nguồn, thực nghiệm, giao diện Web, Level 7 và biểu đồ đã xanh `127 passed`; hoàn thiện Poster và gói ZIP nộp cuối kỳ đúng chuẩn.

### Danh sách thành viên và tỷ lệ đóng góp (Cập nhật trước khi nộp)

> Theo yêu cầu nộp bài của giảng viên, nhóm kê khai đầy đủ Họ tên, MSSV, nhiệm vụ, công việc thực tế và tỷ lệ đóng góp sao cho **tổng tỷ lệ đóng góp bằng đúng 100%** (lịch sử GitHub và kết quả thực hiện là căn cứ đối chiếu):

| STT | Họ và tên | MSSV | Tài khoản GitHub | Nhiệm vụ & công việc thực hiện chính | Tỷ lệ đóng góp (%) |
| :-: | --- | --- | --- | --- | --: |
| 1 | *(Điền họ tên TV1)* | *(Điền MSSV)* | `nguyenmartin212-blip` | Level 2 (`heuristic`), Level 3 (`alphabeta` + đếm nút & Ablation 1), Level 5 (`cnn` + sinh dữ liệu & huấn luyện), **viết trọn bộ Báo cáo cuối kỳ 5 chương** | 33.3% |
| 2 | *(Điền họ tên TV2)* | *(Điền MSSV)* | `3rAxis` | Level 4 (`mcts` + giới hạn thời gian & Ablation 2 960 ván), CLI (`play_cli`), **quay Video demo, chụp ảnh tình huống chiến thuật & làm Slide thuyết trình** | 33.3% |
| 3 | *(Điền họ tên TV3 — Nhóm trưởng)* | *(Điền MSSV)* | `tuankiet248` | Engine `game/`, `arena/` (2.000 ván, 2 chế độ ngân sách, `p95`/CI), Giao diện Web (`ui/`), Level 7 (`mcts_cnn` PUCT), `notebooks/` & biểu đồ, **thiết kế Poster, quản lý GitHub & đóng gói hồ sơ nộp** | 33.4% |
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
git add agents/heuristic.py tests/test_heuristic.py agents/__init__.py
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
| `game/` | Luật cờ và engine Gomoku 9×9 (`engine.py`) |
| `agents/` | Giao diện Agent, registry và các cấp AI từ Level 1 đến Level 7 |
| `arena/` | Đấu một ván (`play.py`) và giải đấu vòng tròn thống kê (`round_robin.py`) |
| `train/` | Sinh dữ liệu chuyên gia và huấn luyện mạng CNN (`train_cnn.py`) |
| `ui/` | Máy chủ và giao diện đồ họa Web (`web_app.py`, `web_index.html`) |
| `scripts/` | Công cụ dòng lệnh CLI & Ablation (`play_cli.py`, `quick_match.py`, `ablation_search.py`, `ablation_mcts.py`, `summarize_mcts.py`) |
| `tests/` | Toàn bộ 127 bài kiểm thử tự động `pytest` cho engine, agent, arena, CLI và Web |
| `configs/`, `utils/` | Cấu hình trung tâm, quản lý `seed` và logger JSONL |
| `logs/`, `checkpoints/`, `notebooks/` | Nhật ký thực nghiệm, trọng số đã train và notebook xuất biểu đồ |
| `docs/`, `lab/` | Quy ước nhóm (`CONVENTIONS.md`), thiết kế & kết quả MCTS (`MCTS_*.md`), tài liệu tham khảo và bài Lab |

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
