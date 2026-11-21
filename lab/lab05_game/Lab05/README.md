# Lab 05 · Tìm kiếm đối kháng và trò chơi

Gói này gồm bảy notebook Tic-Tac-Toe và bài mở rộng Connect 4. Mỗi notebook có kết quả đã chạy và nhận xét sau các thí nghiệm. [Báo cáo tổng hợp](Bao-cao-Lab05.md) có bảng đấu với Random và phần trả lời câu hỏi thảo luận.

## Chạy lại

Giải nén và giữ các notebook cùng thư mục với các tệp `.py`. Trong thư mục vừa giải nén, chạy bằng Python 3.10 trở lên.

```powershell
python -m pip install jupyterlab numpy
python -m jupyterlab
```

Chọn kernel Python đã cài các gói trên rồi dùng **Restart Kernel and Run All Cells**. Cài thêm `matplotlib` nếu muốn `show_board()` vẽ bàn Tic-Tac-Toe bằng đồ họa. Bản kết quả đi kèm dùng hiển thị văn bản. Thời gian đo có thể thay đổi theo máy và tiến trình đang chạy.

## Thứ tự notebook

| Bài | Notebook |
|---|---|
| 1 · Định nghĩa trò chơi | [tictactoe_definitions.ipynb](tictactoe_definitions.ipynb) |
| 2 · AND-OR Search | [tictactoe_and_or_tree_search.ipynb](tictactoe_and_or_tree_search.ipynb) |
| 3 · Minimax và Alpha-Beta | [tictactoe_alpha_beta_tree_search.ipynb](tictactoe_alpha_beta_tree_search.ipynb) |
| 4 · Alpha-Beta có heuristic | [tictactoe_heuristic_alpha_beta_tree_search.ipynb](tictactoe_heuristic_alpha_beta_tree_search.ipynb) |
| 5 · Pure Monte Carlo Search | [tictactoe_pure_monte_carlo_search.ipynb](tictactoe_pure_monte_carlo_search.ipynb) |
| 6 · UCB1 ở gốc | [tictactoe_monte_carlo_tree_search_restricted.ipynb](tictactoe_monte_carlo_tree_search_restricted.ipynb) |
| 7 · Chơi tương tác | [tictactoe_interactive.ipynb](tictactoe_interactive.ipynb) |
| 8 · Connect 4 | [assignment_connect4.ipynb](assignment_connect4.ipynb) |

Bài 7 có hai ván dùng đầu vào định sẵn qua cùng hàm kiểm tra nước đi. Để chơi trực tiếp, đặt `PLAY_AS = "x"` hoặc `"o"` ở ô cuối và chạy ô đó.

Bài 8 có bản HTML để đọc kết quả mà không cần mở Jupyter. Trong Bài 8, ngân sách PMCS được tính theo số playout trên mỗi cột hợp lệ. [Xem Connect 4 đã chạy](assignment_connect4.html)
