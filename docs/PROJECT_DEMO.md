# Thuyết trình và demo toàn dự án

Học liệu này bao quát sáu agent đã triển khai: `random`, `heuristic`, `alphabeta`, `mcts`, `cnn` và `mcts_cnn`, cùng engine, CLI, Web, Arena, CNN đã huấn luyện và hai thí nghiệm ablation. Level 6 self-play RL và Level 8 AlphaZero là hướng mở rộng, chưa được tính là tính năng đã hoàn thành.

## Tệp trình bày

- [Slide toàn dự án](demo/project/CARO_Project.pptx): 18 trang, bảng và biểu đồ chỉnh sửa được, có nguồn và lời dẫn trong speaker notes.
- [Video Web và CLI](demo/project/project_demo_vi.mp4): dài 6 phút 24 giây, 1280×720, 10 fps, khoảng 48 MB; phụ đề tiếng Việt, không có lời thu âm.
- [33 ảnh tình huống](demo/project/screenshots), [phụ đề](demo/project/captions_vi.srt) và [lời dẫn video](demo/project/narration_vi.txt).
- [Cấu hình, nguồn số liệu và kiểm tra checkpoint](demo/project/project_evidence.json); [lịch sử nước đi khi quay](demo/project/demo_manifest.json).

Bản sáu slide và video MCTS ban đầu vẫn nằm trong `docs/demo/`; đó là học liệu phần MCTS, không thay cho bộ toàn dự án này.

Bản ghi ngày 27/11/2026 đã đối chiếu đủ 18 quyết định (ba thế cho mỗi agent), phát lại lịch sử bằng engine và khớp SHA-256 checkpoint. Slide có bảy ảnh nhúng, năm bảng và ba biểu đồ chỉnh sửa được; đã kiểm tra 18 trang render và cấu trúc PPTX. Các kiểm tra này không thay cho việc nhóm mở lại trên máy trình chiếu trước khi bảo vệ.

## Kịch bản thuyết trình

Dành khoảng 12–15 phút cho slide; video có thể mở riêng hoặc dùng các đoạn ngắn khi giải thích chiến thuật.

| Trang | Nội dung | Người giải thích gợi ý |
| --- | --- | --- |
| 1–4 | Bài toán, RQ1/RQ2, kiến trúc và sáu agent | Cả nhóm, TV3 giới thiệu kiến trúc |
| 5–6 | Random, Heuristic, Alpha-Beta và Ablation 1 | TV1 |
| 7 | MCTS, góc nhìn giá trị và deadline mềm | TV2 |
| 8–9 | Sinh dữ liệu, tách tập, CNN và lỗi chiến thuật quan sát được | TV1 |
| 10 | Policy–Value và PUCT | TV3 |
| 11–13 | Thiết kế giải đấu, điểm số và chi phí | TV3 |
| 14–15 | Ablation 2 và các thế kiểm thử chung | TV2 |
| 16–18 | Demo, kết luận, hạn chế và nguồn | TV2 điều phối, cả nhóm trả lời |

Phân chia trên là gợi ý khi bảo vệ; cả nhóm cần hiểu luồng hoạt động và phần việc của mình. Điền họ tên, MSSV thật trong hồ sơ nộp theo README.

## Trình diễn trực tiếp

1. Chạy `run_caro.bat` trên Windows hoặc `python -m ui.web_app`. Máy cần cài PyTorch và có checkpoint `checkpoints/cnn_9x9.pt` để hiện đủ sáu agent.
2. Chọn Người đấu AI, cố định seed 0, chọn quân X rồi đánh vài nước. Thử hoàn tác và đổi sang quân O.
3. Chọn lần lượt các agent trong Máy–Máy, dùng nút đi từng bước để giải thích quyết định. Nêu cấu hình mặc định: Alpha-Beta sâu 3; MCTS 400 mô phỏng, `c=1.4`; MCTS-CNN 56 mô phỏng, `c_puct=1.5`.
4. Mở ảnh và video cho các thế kiểm thử có nhãn bên dưới. Dùng lịch sử lưu trong manifest để đối chiếu, không coi các thế dựng là kết quả giải đấu ngẫu nhiên.
5. Chạy CLI, thử nhập sai, một ô hợp lệ và thoát bằng `q`:

   ```powershell
   python -X utf8 -m scripts.play_cli cnn --seed 0
   python -X utf8 -m scripts.play_cli mcts --side o --seed 0 --simulations 2000 --time-limit 0.05
   ```

6. Mở bảng thực nghiệm. Phân biệt giải 2.000 ván, run PUCT 200 ván và Ablation 2 960 ván; chúng có cấu hình, môi trường và cỡ mẫu khác nhau.

## Thế chiến thuật chung

Mỗi lịch sử được dựng bằng engine thật, action = hàng × 9 + cột. Agent nhận seed 0 qua API Web; engine cộng độ dài lịch sử khi tạo RNG như mã nguồn hiện tại.

| Tình huống | Lịch sử trước lượt X | Điều cần quan sát |
| --- | --- | --- |
| Có nước thắng | `[36, 9, 37, 10, 38, 11, 39, 12]` | Ô `(4,4)` giúp X thắng ngay |
| Chặn bắt buộc | `[40, 0, 49, 1, 41, 2, 50, 3]` | Ô `(0,4)` chặn chuỗi O trên hàng 0 |
| Hai đầu đe dọa | `[40, 2, 49, 3, 60, 4, 70, 5]` | O có hai ô thắng `(0,1)` và `(0,6)`; X không thể chặn cả hai |

Trong kiểm tra trước khi quay, Random chọn `(3,6)` ở cả hai thế đầu. Heuristic, Alpha-Beta, MCTS và MCTS-CNN thắng ở `(4,4)` và chặn ở `(0,4)`. CNN chọn `(1,4)` thay vì nước thắng, nhưng chặn đúng ở thế thứ hai. Đây là một lỗi cụ thể của checkpoint; không suy ra tỷ lệ thắng từ riêng tình huống đó.

Thế hai đầu là trạng thái đã bất lợi không thể cứu bằng một nước. Ảnh thua của từng agent trong thế này không được dùng để kết luận agent mắc lỗi hay yếu hơn đối thủ. Các ảnh `<agent>_win.png`, `<agent>_block.png`, `<agent>_double_threat.png` lưu phản hồi thật cho từng agent; ảnh `common_*_before.png` lưu trạng thái đầu vào.

## Nguồn và giới hạn của số liệu

- Giải 2.000 ván: lấy từ output đã lưu trong `notebooks/analysis.ipynb`. Raw log của giải này không có trong checkout dùng chuẩn bị học liệu, nên không ghi là đã phát lại 2.000 ván.
- CNN: thông số tập dữ liệu, test metrics và epoch tốt nhất đọc trực tiếp từ `summary` trong checkpoint; SHA-256 được lưu để đối chiếu. Không huấn luyện lại khi làm video.
- Đường cong học và hình Ablation 1 gốc của nhóm nằm ở [cnn_learning_and_ablation1.png](../notebooks/figures/cnn_learning_and_ablation1.png); mở thêm hình này khi giải thích cách chọn epoch bằng validation. Các điểm theo từng epoch không có trong checkpoint, nên không suy diễn lại dữ liệu từ ảnh.
- Ablation 1 và PUCT 200 ván: trích số liệu nhóm đã báo cáo trong README. PUCT có 20 ván/cặp, khác giải 100 ván/cặp của năm agent.
- Ablation 2: CSV và raw log 960 ván có trong repo, được đối chiếu bằng `scripts.summarize_mcts`. Kiểm tra deadline 100 ván là một run riêng.
- Chế độ `time` của giải cũ hiệu chuẩn số rollout; khác `time_limit` trực tiếp của MCTS hiện tại. Không mô tả đó là hard deadline hoặc trộn độ trễ giữa các môi trường.

Số liệu trong slide dùng để trả lời hai câu hỏi nghiên cứu trong phạm vi các cấu hình đã đo. MCTS-CNN hiện dùng học có giám sát và PUCT; chưa triển khai vòng lặp self-play MCTS, nhiễu Dirichlet và đấu loại cập nhật checkpoint của AlphaZero đầy đủ.
