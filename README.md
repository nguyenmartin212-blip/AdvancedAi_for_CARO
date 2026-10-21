# Gomoku (Caro) 9×9 – Multi-level Game AI

Đồ án cuối kì *Trí tuệ nhân tạo nâng cao*. Xây dựng và đánh giá nhiều cấp độ AI cho Gomoku 9×9,
5 quân liên tiếp thắng (freestyle: ≥5 đều thắng, không có luật cấm).

## Cấp độ agent

| Level | Agent | Trạng thái |
|---|---|---|
| 1 | Random | ✅ xong |
| 2 | Heuristic / Rule-based | ⏳ |
| 3 | Minimax + Alpha-Beta | ⏳ |
| 4 | MCTS / UCT | ⏳ |
| 5 | CNN policy (+value), học có giám sát | ⏳ |
| 6 | Reinforcement Learning (self-play) | ⏳ |
| 7 | AlphaGo-*inspired* (khuyến khích) | ⏳ |
| 8 | AlphaZero-*inspired* (khuyến khích) | ⏳ |

Level 7–8 là bản *inspired* rút gọn, không phải tái hiện đầy đủ AlphaGo/AlphaZero.

## Cài đặt

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
Cần Python ≥ 3.10. `torch` chỉ cần từ Level 5 trở đi; GPU không bắt buộc.

## Chạy thử

```bash
python -m pytest -q                              # chạy toàn bộ test
python -m scripts.quick_match random random -n 20   # trận thử giữa 2 agent đã đăng ký
```

Các lệnh dưới đây sẽ có khi các phần tương ứng hoàn thành:

```bash
python -m train.<...>          # huấn luyện (Level 5/6/8)
python -m arena.round_robin    # giải round-robin, ghi log vào logs/
python -m ui.app               # demo chơi với AI (Pygame)
```

## Cấu trúc thư mục

```
game/      engine Gomoku + test engine
agents/    base.py (giao diện Agent), registry.py (đăng ký agent), mỗi level một file
arena/     play.py (chạy 1 ván), round-robin, thống kê
train/     huấn luyện mô hình (supervised / RL / AlphaZero-inspired)
ui/        giao diện Pygame
utils/     seed, logger JSONL, đọc config
configs/   default.json (cỡ bàn, seed, ngân sách, tham số agent)
scripts/   công cụ dòng lệnh nhỏ
logs/      log thí nghiệm (.jsonl)
checkpoints/  trọng số mô hình đã huấn luyện
notebooks/ phân tích kết quả, vẽ biểu đồ
docs/      quy ước nhóm
```

## Quy ước chung (xem thêm `docs/CONVENTIONS.md`)

- Bàn cờ `board[r, c]`: `1` = đi trước, `-1` = đi sau; `action = r*9 + c`.
- Mọi agent kế thừa `Agent` và cài `select_action(game) -> int`, **không sửa** `game` (dùng `game.clone()`).
- Agent mới phải đăng ký trong `agents/registry.py` bằng `@register("ten")`.
- Log thí nghiệm dùng `utils.logger.JsonlLogger`, một dòng JSON mỗi bản ghi.
- Seed cố định qua `utils.seed.set_seed`; tham số lấy từ `configs/`.

## Thêm một agent mới

```python
# agents/my_agent.py
from agents.base import Agent
from agents.registry import register

class MyAgent(Agent):
    name = "my_agent"
    def __init__(self, seed=None): ...
    def select_action(self, game): ...

@register("my_agent")
def _make(seed=None, **params):
    return MyAgent(seed=seed, **params)
```
Sau đó import module trong `agents/__init__.py` để việc đăng ký có hiệu lực, và thêm test `agents/test_my_agent.py`.

## Nộp bài

Đóng gói `NhomXX_TenGame_TTNTNC_HoTen_MaSV.zip` gồm: code, README, log, checkpoint, báo cáo, slide, poster.
Chỉ báo cáo các thí nghiệm đã thực sự chạy.
