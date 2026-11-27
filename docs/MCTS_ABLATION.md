# Ablation 2: số mô phỏng và hằng số UCT của MCTS

## Cấu hình

Run `mcts_sensitivity_40` chạy ngày 27/11/2026, gồm 12 tổ hợp số mô phỏng `{100, 400, 1000, 2000}` và `c ∈ {0.7, 1.4, 2.0}`. Mỗi tổ hợp gặp Random và Heuristic trong 40 ván/đối thủ, tổng cộng 960 ván. Bàn 9×9 freestyle, hai nước khai cuộc ngẫu nhiên, seed gốc 0; mỗi cặp đổi X/O dùng cùng khai cuộc. Các cấu hình dùng cùng bộ 20 seed khai cuộc.

Môi trường: Python 3.15.1, NumPy 2.5.4, Windows 10 build 19042, CPU Intel64 Family 6 Model 61 Stepping 4. Lưới chạy trên CPU trong khoảng 71 phút. Mã MCTS, Arena và engine đã được đối chiếu với commit `a3e4cbb`. Thời gian đo bằng `perf_counter()`, gồm kiểm tra chiến thuật và tìm kiếm.

Điểm tính bằng `(thắng + 0.5 × hòa) / số ván`; khoảng tin cậy dùng Wilson 95% theo Arena hiện có. Rollout TB là số rollout hoàn tất trung bình trên mỗi nước, gồm cả giá trị 0 khi trả thẳng nước thắng/chặn.

## Kết quả trước Random

| Mô phỏng | c | Thắng–Hòa–Thua | Điểm | CI 95% | TB (ms/nước) | P95 (ms) | Rollout TB |
| ---: | ---: | :---: | ---: | :---: | ---: | ---: | ---: |
| 100 | 0.7 | 40–0–0 | 1.000 | [0.912, 1.000] | 89.24 | 169.39 | 91.2 |
| 100 | 1.4 | 40–0–0 | 1.000 | [0.912, 1.000] | 89.91 | 153.68 | 91.3 |
| 100 | 2 | 40–0–0 | 1.000 | [0.912, 1.000] | 85.13 | 151.84 | 91.4 |
| 400 | 0.7 | 40–0–0 | 1.000 | [0.912, 1.000] | 435.43 | 782.61 | 362.9 |
| 400 | 1.4 | 40–0–0 | 1.000 | [0.912, 1.000] | 350.54 | 546.52 | 360.2 |
| 400 | 2 | 40–0–0 | 1.000 | [0.912, 1.000] | 365.95 | 566.52 | 363.9 |
| 1000 | 0.7 | 40–0–0 | 1.000 | [0.912, 1.000] | 991.61 | 1601.68 | 867.3 |
| 1000 | 1.4 | 40–0–0 | 1.000 | [0.912, 1.000] | 896.17 | 1516.35 | 877.4 |
| 1000 | 2 | 40–0–0 | 1.000 | [0.912, 1.000] | 691.19 | 909.81 | 882.8 |
| 2000 | 0.7 | 40–0–0 | 1.000 | [0.912, 1.000] | 1417.03 | 1879.98 | 1698.1 |
| 2000 | 1.4 | 40–0–0 | 1.000 | [0.912, 1.000] | 1399.36 | 1841.07 | 1732.4 |
| 2000 | 2 | 40–0–0 | 1.000 | [0.912, 1.000] | 1395.54 | 1814.89 | 1760.0 |

## Kết quả trước Heuristic

| Mô phỏng | c | Thắng–Hòa–Thua | Điểm | CI 95% | TB (ms/nước) | P95 (ms) | Rollout TB |
| ---: | ---: | :---: | ---: | :---: | ---: | ---: | ---: |
| 100 | 0.7 | 0–0–40 | 0.000 | [0.000, 0.088] | 76.86 | 140.30 | 70.4 |
| 100 | 1.4 | 0–0–40 | 0.000 | [0.000, 0.088] | 146.00 | 304.81 | 70.4 |
| 100 | 2 | 0–0–40 | 0.000 | [0.000, 0.088] | 86.78 | 187.88 | 70.4 |
| 400 | 0.7 | 1–0–39 | 0.025 | [0.004, 0.129] | 305.59 | 532.00 | 288.8 |
| 400 | 1.4 | 0–0–40 | 0.000 | [0.000, 0.088] | 300.21 | 483.36 | 290.3 |
| 400 | 2 | 0–0–40 | 0.000 | [0.000, 0.088] | 342.97 | 647.20 | 284.5 |
| 1000 | 0.7 | 1–0–39 | 0.025 | [0.004, 0.129] | 784.28 | 1316.47 | 721.9 |
| 1000 | 1.4 | 1–0–39 | 0.025 | [0.004, 0.129] | 597.78 | 925.51 | 714.3 |
| 1000 | 2 | 1–0–39 | 0.025 | [0.004, 0.129] | 592.35 | 907.23 | 708.8 |
| 2000 | 0.7 | 3–0–37 | 0.075 | [0.026, 0.199] | 1196.93 | 1846.94 | 1436.4 |
| 2000 | 1.4 | 1–0–39 | 0.025 | [0.004, 0.129] | 1168.79 | 1842.83 | 1410.7 |
| 2000 | 2 | 1–0–39 | 0.025 | [0.004, 0.129] | 1216.46 | 1843.53 | 1451.8 |

## Kiểm tra ngân sách thời gian

Run `rr_mcts_native_time_100` gồm 100 ván MCTS–Heuristic, seed gốc 0, hai nước khai cuộc và đổi bên X/O. MCTS dùng `time_limit=0.05`, `simulations=100000`, `c=1.4`, kết quả 0 thắng, 0 hòa, 100 thua.

Trên 447 nước của MCTS, thời gian trung bình là 36.13 ms, P95 50.99 ms, cao nhất 51.70 ms; số rollout hoàn tất trung bình 45.8/nước. Các nước thắng/chặn trực tiếp có thể trả sớm và được tính 0 rollout. Deadline là giới hạn mềm, nên việc hoàn thành rollout đang chạy và tải hệ thống có thể làm vượt 50 ms. Log ở [rr_mcts_native_time_100.jsonl](../logs/rr_mcts_native_time_100.jsonl).

## Nhận xét

MCTS thắng 40/40 ván trước Random ở mọi cấu hình. Với đối thủ này, tỷ lệ thắng đã chạm trần nên tăng ngân sách không tạo thêm khác biệt về điểm trong mẫu đo.

Trước Heuristic, cấu hình 2.000 mô phỏng, c=0.7 đạt 3 thắng và 37 thua; các cấu hình còn lại đạt tối đa 1 thắng/40 ván. Kết quả cho thấy rollout ngẫu nhiên vẫn yếu trước heuristic chiến thuật trên bàn 9×9. Chi phí tăng theo số mô phỏng, trong khi mức tăng điểm nhỏ và không đều giữa các giá trị c.

Mỗi cấu hình chỉ có 20 cặp khai cuộc đổi bên. Các CI của những cấu hình có ít chiến thắng còn rộng, nên số liệu chưa đủ để chọn một c tối ưu ổn định. Độ trễ còn phụ thuộc tải máy và độ dài ván; khi đối chiếu với các run trước cần xét riêng môi trường và ngân sách.

## Tái lập và sử dụng số liệu

Chạy từ thư mục gốc với môi trường Python đã cài các gói của dự án:

```powershell
python -X utf8 -m scripts.ablation_mcts -n 40 --seed 0 --run mcts_sensitivity_40_repeat
python -X utf8 -m scripts.summarize_mcts logs/mcts_sensitivity_40.jsonl
python -X utf8 -m arena.round_robin --agents mcts heuristic -n 100 --budget-mode time --seconds-per-move 0.05 --simulations 100000 --seed 0 --run rr_mcts_native_time_100_repeat
```

Log tổng hợp và thông tin môi trường ở [mcts_sensitivity_40.jsonl](../logs/mcts_sensitivity_40.jsonl); bảng cho notebook ở [mcts_sensitivity_40.csv](../logs/mcts_sensitivity_40.csv). Mỗi cấu hình có log ván riêng theo tên `mcts_sensitivity_40_s<S>_c<C>_vs_<opponent>.jsonl`. Runner từ chối tên run đã tồn tại để tránh gộp thêm ván vào kết quả cũ.

Kiểm thử toàn bộ dự án đạt 127 test trên Python 3.13.2, NumPy 2.3.3 và PyTorch 2.13.0+cpu, bao gồm đầy đủ các module CNN và MCTS-CNN. Thiết kế thuật toán và giới hạn mềm của deadline được mô tả trong [MCTS_DESIGN.md](MCTS_DESIGN.md).

Toàn bộ 1.060 ván đã được phát lại thành công để đối chiếu trạng thái kết thúc. Số ván, kết quả và 480 cặp khai cuộc đổi bên của Ablation 2 khớp với log.
