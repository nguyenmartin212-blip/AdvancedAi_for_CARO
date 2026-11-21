# Báo cáo Lab 05 · Tìm kiếm đối kháng và trò chơi

## Thiết lập thực nghiệm

Tic-Tac-Toe dùng chỉ số ô 0–8, X đi trước. Hai tác tử Random chơi 1.000 ván với seed NumPy 51000. Ở các dòng còn lại, mỗi tác tử chơi 100 ván ở vai X và 100 ván ở vai O. Đối thủ dùng cùng dãy seed theo vai, bắt đầu ở 51000 khi tác tử cầm X và 61000 khi tác tử cầm O. Các tác tử Monte Carlo dùng bộ sinh số riêng cho mô phỏng. Ngân sách N là tổng số playout cho một quyết định. Thời gian trung bình chỉ tính lời gọi chọn nước của tác tử ở cột đầu, có tính các lần tra bộ nhớ đệm nếu thuật toán dùng.

| Tác tử | Đối thủ | Số ván | Thắng | Hòa | Thua | TB (ms/nước) |
|---|---|---:|---:|---:|---:|---:|
| Random (thống kê theo X) | Random | 1000 | 584 | 113 | 303 | 0.0218 |
| AND-OR | Random | 200 | 167 | 33 | 0 | 0.1847 |
| Alpha-Beta đầy đủ | Random | 200 | 185 | 15 | 0 | 85.8551 |
| Heuristic Alpha-Beta, cutoff 2 | Random | 200 | 188 | 12 | 0 | 1.8132 |
| Heuristic Alpha-Beta, cutoff 4 | Random | 200 | 185 | 15 | 0 | 10.5966 |
| Pure Monte Carlo, N=10 | Random | 200 | 164 | 19 | 17 | 0.1129 |
| Pure Monte Carlo, N=100 | Random | 200 | 184 | 7 | 9 | 0.7828 |
| Pure Monte Carlo, N=1000 | Random | 200 | 193 | 4 | 3 | 6.8569 |
| UCB1 độ sâu 1, N=10 | Random | 200 | 153 | 13 | 34 | 0.1971 |
| UCB1 độ sâu 1, N=100 | Random | 200 | 184 | 4 | 12 | 1.2708 |

Trong 1.000 ván Random, X thắng 584 ván, O thắng 303 ván và 113 ván hòa. X có lợi thế đi trước trong mẫu này. Các notebook ghi riêng kết quả từng vai, số nút và thời gian cho từng thế kiểm thử.

## Nhận xét từ kết quả

1. **Cắt tỉa giữ giá trị chính xác.** Minimax và Alpha-Beta duyệt theo cùng thứ tự trả cùng giá trị và nước đi trên năm thế so sánh. Từ bàn trống, Minimax thăm 549.946 nút và Alpha-Beta thăm 18.297 nút. Ưu tiên giữa rồi góc giảm còn 7.275 nút ở bàn trống, nhưng tăng từ 101 lên 149 nút ở thế X phải chặn. Hiệu quả phụ thuộc vào việc thứ tự có đưa nhánh tạo cận mạnh lên sớm hay không.
2. **Cutoff giảm chi phí và có thể bỏ sót chiến thuật.** Trên bàn trống, cutoff 2 và 4 thăm lần lượt 26 và 303 nút. Ở thế chiến thuật bổ sung trong Bài 4, cutoff 2 chọn nước có giá trị hòa, còn cutoff 4 thấy nước bảo đảm thắng. Cutoff 2 thắng nhiều hơn cutoff 4 trong mẫu đấu với Random, nơi mục tiêu là tận dụng sai lầm của đối thủ cụ thể.
3. **Tăng mẫu giúp PMCS ổn định ở thế phải chặn.** Ô 7 được chọn 11/30, 22/30 và 30/30 lần với N=10, 100 và 1000. Số ván thua trước Random giảm từ 17 còn 3 khi tăng N từ 10 lên 1000, cùng với chi phí mô phỏng cao hơn.
4. **UCB1 phân bổ thích ứng.** Ở thế X thắng ngay và N=100, UCB1 dành 29 lượt cho ô thắng ngay 8, trong khi PMCS chia 20 lượt cho mỗi ô. Tăng N từ 10 lên 100 giảm số ván thua của UCB1 từ 34 còn 12. Tại N=100, cả hai cùng thắng 184 ván. PMCS có 9 ván thua và UCB1 có 12 ván thua.
5. **Bàn lớn khiến việc duyệt đến cuối ván trở nên đắt.** Với thứ tự ưu tiên và bảng lưu trạng thái, Alpha-Beta giải bàn rỗng 4×4 sau 15.926 lượt thăm nút. Ở bàn 6×7, tìm kiếm dừng tại giới hạn 250.000 nút khi chưa xác định được giá trị chính xác. Trên cùng bàn chuẩn, heuristic cutoff 4 chọn cột giữa sau 236 nút. Chi phí thấp hơn đi kèm việc đánh giá các thế còn dang dở.

## Câu hỏi thảo luận

1. **Minimax và AND-OR mô hình hóa đối thủ thế nào?** Minimax cho nút Min chọn phản hồi làm giá trị của Max nhỏ nhất. AND-OR gộp các phản hồi thành các kết quả có thể xảy ra của một hành động. Nút AND cần kế hoạch tiếp nối đạt mục tiêu cho mọi kết quả. Mục tiêu thắng và mục tiêu không thua tương ứng với hai ngưỡng khác nhau của utility.
2. **Alpha-Beta có thay đổi nước tối ưu không?** Nó giữ giá trị Minimax khi tìm tới lá kết thúc. Khi α ≥ β, bên ở nút tổ tiên đã có lựa chọn đủ tốt để loại các nhánh còn lại. Nếu nhiều nước cùng tối ưu, đổi thứ tự duyệt có thể đổi nước được trả về trong nhóm đó.
3. **Khi nào cần heuristic và cutoff?** Khi độ sâu và số nước khả dĩ khiến tìm kiếm đến trạng thái kết thúc vượt ngân sách thời gian. Hàm đánh giá thay utility ở lá chưa kết thúc. Tìm sâu hơn có thể phát hiện chiến thuật sau nhiều lượt, đổi lại phải duyệt thêm nút.
4. **Ưu điểm và hạn chế của PMCS là gì?** PMCS dùng các ván mô phỏng nên chỉ cần luật chuyển trạng thái, điều kiện kết thúc và chính sách mô phỏng. Ít mẫu làm ước lượng nhiễu. Ngay cả với nhiều mẫu, chính sách đi ngẫu nhiên có thể đánh giá cao một nước dễ bị đối thủ mạnh phản bác.
5. **UCB1 cải thiện cách cấp playout ra sao?** Nó ưu tiên điểm trung bình cao và cộng khoản thăm dò lớn hơn cho nhánh ít lượt. Sau lần thử ban đầu ở từng nhánh, ngân sách dịch về các nước đang có triển vọng, trong khi các nước ít mẫu vẫn có cơ hội được kiểm tra lại.
6. **Điều gì làm không gian tìm kiếm tăng nhanh trong Connect 4 và Dots and Boxes?** Connect 4 có thể mở tới bảy nhánh theo cột và sâu tới 42 nước trên bàn chuẩn. Nhiều thứ tự đánh có thể dẫn đến cùng thế, làm cây lớn hơn số trạng thái phân biệt. Dots and Boxes có $E = r(c+1)+c(r+1)$ cạnh trên bàn $r$ hàng, $c$ cột ô vuông. Ban đầu có tới $E$ nước và số thứ tự đặt cạnh có thể lên tới $E!$. Quyền đi thêm khi hoàn thành ô và chủ sở hữu các ô cũng ảnh hưởng đến trạng thái trò chơi.
