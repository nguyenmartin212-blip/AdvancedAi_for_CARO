# MCTS/UCT, ngân sách thời gian và cách kiểm chứng

## Giá trị tại nút

Mỗi nút lưu tổng kết quả từ góc nhìn bên sắp đi tại nút đó. Một kết quả thắng cho bên này có giá trị +1, thua là -1 và hòa là 0. Khi chọn con bằng UCT, cha dùng giá trị trung bình của con với dấu âm. Khi cập nhật ngược, kết quả đổi dấu sau mỗi cạnh. Cách quy ước này giữ việc chọn nước nhất quán cho cả X lẫn O.

Bot thực hiện bốn bước: chọn nút theo UCT, mở rộng một hành động chưa thử, rollout ngẫu nhiên tới trạng thái kết thúc, rồi cập nhật số lượt thăm và tổng kết quả. Nước đi cuối cùng ưu tiên con có nhiều lượt thăm; nếu bằng nhau thì so giá trị trung bình từ góc nhìn gốc. Cây được tạo mới ở mỗi lượt. Các nước mô phỏng đều chạy trên bản sao của môi trường.

Trước khi xây cây, bot tìm nước thắng ngay của mình, rồi mới tìm nước chặn thắng ngay của đối thủ. Quy tắc ở gốc không thay đổi chính sách rollout ngẫu nhiên. Nếu đối thủ có nhiều ô thắng độc lập, chặn một ô không bảo đảm tránh được thất bại.

## Hai giới hạn tính toán

Khi `time_limit=None`, bot chạy đủ `simulations` rollout, trừ khi trả thẳng nước chiến thuật. Cùng seed, cấu hình và chuỗi lời gọi cho cùng hành động. Ở chế độ có thời gian, kết quả còn phụ thuộc tốc độ máy và tải hệ thống; cùng seed không bảo đảm cùng số rollout hoặc cùng nước đi.

Đồng hồ `perf_counter()` bắt đầu ở đầu `select_action()`. Kiểm tra deadline đặt trước mỗi rollout. Rollout đã bắt đầu được chạy đến hết để tránh đưa giá trị của một ván chưa kết thúc vào bước cập nhật ngược. Vì vậy ngân sách thời gian là giới hạn mềm: chi phí kiểm tra thắng/chặn và rollout đang chạy có thể làm vượt thời gian yêu cầu. Nếu kiểm tra chiến thuật đã dùng hết thời gian mà không tìm được nước bắt buộc, bot chọn một ô hợp lệ bằng RNG của agent.

Khi dùng cả hai tham số, bot dừng ở giới hạn chạm trước. Có thể đặt `simulations` đủ lớn khi muốn so theo thời gian. Bộ đếm `last_simulations` được đặt về 0 ở đầu mỗi lần chọn nước; nó tăng sau mỗi rollout hoàn tất. Nước chiến thuật và fallback trước rollout có giá trị 0. Arena dùng bộ đếm này để ghi lượng tìm kiếm thực tế.

## Kiểm thử

Bộ test cũ tiếp tục kiểm tra UCT, đổi dấu khi backup, nước thắng/chặn, đầu vào không bị sửa và khả năng thắng Random. Test mới dùng đồng hồ giả để kiểm tra dừng đúng ở ranh giới giữa hai rollout, ngân sách quá nhỏ, giới hạn số mô phỏng khi vẫn còn thời gian và việc đặt lại bộ đếm. Test Arena kiểm tra truyền deadline trực tiếp và tính cả ván có 0 rollout trong trung bình.

Ablation 2 tái dùng runner của Arena. Mỗi cặp đổi bên có cùng seed và hai nước khai cuộc; mọi cấu hình nhận cùng bộ seed. Log thô được giữ lại để tổng hợp lại kết quả. Kiểm thử tích hợp đối chiếu thắng/thua, khai cuộc, số ván và tính lặp lại của kết quả ở chế độ cố định số mô phỏng.

## Nội dung trình bày

Phần Chương 2 có thể dùng quy ước giá trị và bốn bước UCT ở trên. Phần Chương 3 mô tả vòng đời `select_action()`, hai giới hạn tính toán, cách truyền tham số qua registry/CLI/Arena và bộ đếm rollout. Kết quả thực nghiệm, cấu hình chạy và giới hạn suy luận nằm trong `MCTS_ABLATION.md`.

Khi trình bày, nên chỉ rõ MCTS ở đây dùng rollout ngẫu nhiên, chưa dùng policy/value network. Số rollout cao hơn tăng lượng tìm kiếm nhưng không thay thế được chất lượng chính sách mô phỏng trong các thế cờ cần chiến thuật sâu.
