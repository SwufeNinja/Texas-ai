# 简易多人 AI 德州扑克设计文档 (SimpleHoldem-AI)

## 1. 愿景
构建一个轻量级、易于部署的多人在线德州扑克游戏。
- **核心功能**：人类玩家与 LLM (大语言模型) 驱动的 AI 玩家同台竞技。
- **架构理念**：单体应用 + 内存状态管理。优先考虑开发速度和代码可读性，非常适合独立开发者的 MVP (最小可行产品)。

## 2. 技术栈 (Python 全栈)
- **后端框架**: `FastAPI` (HTTP + WebSocket, 默认异步)。
- **网络协议**: `WebSocket` (实时游戏通信)。
- **存储**:
  - **热数据**: Python **内存** (全局 `Dict`) 存储房间和游戏状态；最快，无外部依赖。
  - **持久化 (可选)**: `SQLite` 仅用于基本配置或用户凭证 (MVP 阶段可跳过)。
- **AI 集成**: `OpenAI SDK` (或兼容 API，如 DeepSeek/Claude) + `AsyncIO`。
- **前端**: HTML5 + Vue.js/React (基于 CDN，无需构建工具)。

## 3. 系统架构

### 3.1 模块 (文件夹结构)
后端是一个单一的 Python 项目，以避免微服务的复杂性。

```text
/app
  |-- main.py            # 入口：启动 FastAPI，注册路由
  |-- models.py          # 数据结构：Player, Room, GameState 等
  |-- game_engine.py     # 核心逻辑：洗牌/发牌, 牌型评估, 底池计算, 状态机
  |-- connection_mgr.py  # 网络层：WebSocket 连接和广播
  `-- ai_agent.py        # AI 层：Prompt 构建和 API 调用
```

### 3.2 运行时图 (Mermaid)

```mermaid
graph TD
    ClientA[人类玩家 A] <-->|WebSocket| API[FastAPI 网关]
    ClientB[人类玩家 B] <-->|WebSocket| API

    subgraph "后端服务器 (单进程)"
        API --> Manager[连接管理器]
        API --> Engine[游戏状态机 (内存中)]

        Engine -- AI 回合 --> AI_Mod[AI 模块]
        AI_Mod -- HTTP --> LLM_Cloud[LLM API]
    end

    Manager -- 广播 JSON --> ClientA
    Manager -- 广播 JSON --> ClientB
```

## 4. 核心数据模型 (内存对象)
这些对象仅驻留在内存中；服务器重启将重置所有内容。

### 4.1 房间 (Room)
```python
class Room:
    id: str
    players: List[Player]      # 人类 + AI
    deck: List[str]            # 牌堆 (例如 ['Ah', 'Td'])
    community_cards: List[str] # 公共牌
    pot: int                   # 当前底池
    current_actor_index: int   # 轮到谁行动 (座位索引)
    stage: str                 # PREFLOP, FLOP, TURN, RIVER, SHOWDOWN
```

### 4.2 玩家 (Player)
```python
class Player:
    id: str
    is_ai: bool           # 关键标志：AI 还是人类
    chips: int            # 剩余筹码
    hand: List[str]       # 手牌 ['Ah', 'Kd']
    status: str           # WAITING, PLAYING, FOLDED, ALLIN
    websocket: WebSocket  # 仅人类有此连接；AI 为 None
```

## 5. 核心逻辑流程
### 5.1 游戏循环 (状态机)
这是游戏的核心，位于 `game_engine.py` 中。

1. WaitForAction: 服务器等待当前玩家的行动。
2. ActionReceived:
   - 人类: 通过 WebSocket 接收 JSON `{"action": "raise", "amount": 100}`。
   - AI: 内部触发，调用 LLM 获取 JSON。
3. Validate: 检查合法性 (筹码够吗？轮到你了吗？)。
4. UpdateState: 更新底池、玩家筹码、下注轮次状态。
5. CheckStageEnd: 确定下注轮次是否结束。
   - 是: 发公共牌 -> 进入下一阶段 (例如 FLOP -> TURN)。
   - 否: 将 `current_actor_index` 移动到下一个玩家。
6. Broadcast: 将最新的 `GameState` 推送给所有客户端。

### 5.2 AI 决策流程 (关键路径)
当 `current_actor_index` 指向 `is_ai=True` 的玩家时：

1. 暂停等待: 不等待 WebSocket。
2. 构建 Prompt: 收集牌桌信息 (公共牌、底池、AI 手牌、行动历史)。
3. 异步调用: `await llm_client.chat.completions.create(...)`。
4. 解析与执行: 调用 `engine.process_action()`，就像人类点击了按钮一样。
5. 延迟模拟: 添加 `await asyncio.sleep(1)` 来模拟思考时间。

### 5.3 下注规则和轮次边界 (MVP 细节)
保持规则明确，以避免多人下注中的边缘情况 bug。

- **盲注和按钮**:
  - 每手牌都有 `dealer_index` (庄家), `small_blind_index` (小盲), `big_blind_index` (大盲)。
  - 翻牌前行动从大盲左侧的玩家开始；翻牌后行动从小盲开始。
  - 每手牌将庄家移动到下一个活跃座位。
- **每轮状态**:
  - 跟踪每位玩家的 `current_bet` (本轮最高下注), `last_raise_size` (最后加注额), 和 `has_acted` (是否已行动)。
  - 如果玩家未弃牌且有筹码或已 All-in，则为 **活跃 (active)**。
- **合法行动**:
  - `fold` (弃牌): 总是允许。
  - `check` (过牌): 仅当玩家的下注等于 `current_bet` 时允许。
  - `call` (跟注): 如果玩家的下注 < `current_bet` 则允许；跟注金额 = `current_bet - player.bet`。
  - `raise` (加注): 如果玩家可以将下注增加至少 `min_raise` 则允许。
  - `allin` (全押): 如果筹码 > 0 则允许；根据金额算作跟注或加注。
- **最小加注**:
  - 本轮 `min_raise = max(big_blind, last_raise_size)`。
  - 如果 `raise_amount < min_raise`，拒绝为无效。
  - 如果 `allin` 未达到 `min_raise`，则视为跟注，且不会重新开启行动 (does not reopen action)。
- **轮次结束条件**:
  - 当所有活跃的非 All-in 玩家都 `has_acted = true` 且他们的下注等于 `current_bet` 时，下注轮结束。
  - 如果只剩下一名玩家未弃牌，该手牌立即结束。
- **阶段转换**:
  - PREFLOP -> FLOP: 发 3 张公共牌，重置每轮下注和 `has_acted`。
  - FLOP -> TURN 和 TURN -> RIVER: 各发 1 张牌，重置每轮下注和 `has_acted`。
  - RIVER -> SHOWDOWN: 评估手牌，分配底池。
- **摊牌 (MVP 无边池)**:
  - 如果多名玩家 All-in，目前仅比较主底池。
  - 在平局赢家之间平均分配底池 (多余部分按自家规则处理，例如给第一个座位的)。

## 6. API/协议设计
### 6.1 WebSocket 消息格式
客户端 -> 服务器:

```json
{
  "type": "action",
  "data": {
    "action": "call",  // fold, check, call, raise, allin
    "amount": 0
  }
}
```

服务器 -> 客户端 (广播):

```json
{
  "type": "game_update",
  "data": {
    "stage": "FLOP",
    "pot": 200,
    "community_cards": ["As", "Kd", "2c"],
    "current_player_id": "player_3",
    "seats": [
      {"id": "player_1", "name": "Human", "chips": 900, "bet": 100, "is_active": true},
      {"id": "player_2", "name": "GPT-4", "chips": 1500, "bet": 100, "is_active": true}
    ]
  }
}
```

### 6.2 协议版本控制、排序和错误
添加轻量级元数据以允许演进和调试。

**信封字段** (推荐):
- `schema_version`: 整数 (例如 1)，破坏性更改时增加。
- `room_id`: 字符串，明确路由和调试。
- `msg_id`: 发送者的字符串 UUID。
- `seq`: 用于排序的服务器序列号。
- `ts`: 服务器时间戳 (自纪元以来的毫秒数)，用于客户端协调。

**错误消息** (服务器 -> 客户端):
```json
{
  "type": "error",
  "schema_version": 1,
  "room_id": "room_123",
  "msg_id": "srv-9f5c",
  "seq": 42,
  "ts": 1730000000000,
  "data": {
    "code": "INVALID_ACTION",
    "message": "raise below minimum",
    "details": {"min_raise": 50, "current_bet": 100, "player_bet": 100}
  }
}
```

**系统消息** (服务器 -> 客户端):
```json
{
  "type": "system",
  "schema_version": 1,
  "room_id": "room_123",
  "msg_id": "srv-9f5d",
  "seq": 43,
  "ts": 1730000000100,
  "data": {
    "event": "player_timeout",
    "player_id": "player_3",
    "auto_action": "fold"
  }
}
```

## 7. MVP 路线图 (建议顺序)
阶段 1: 单人控制台 (核心)
- 目标: 无网络，纯 Python 类。
- 工作: 实现洗牌/发牌，手牌评估 (建议使用 `treys`)，简单 AI (随机行动)。
- 测试: 在终端运行完整游戏并验证筹码数学。

阶段 2: 添加大脑 (大脑)
- 目标: 让 AI 更聪明。
- 工作: 编写提示词 (prompt)，集成 OpenAI API。
- 测试: 在终端与 AI 对战；看它是否会诈唬。

阶段 3: 服务器模式 (服务器)
- 目标: 支持多连接。
- 工作: 添加 FastAPI + WebSocket，封装阶段 1 的核心逻辑。
- 测试: 使用 Postman 或简单 HTML 页面连接 WebSocket，查看跳动的 JSON 更新。

阶段 4: UI (门面)
- 目标: 可玩的 UI。
- 工作: 构建一个简单的网页 (公共牌，底牌，动作按钮)。

## 8. 需避免的陷阱 (个人项目)
1. 无边池 (Side pots): 多人 All-in 很复杂。MVP 规则: 将多余筹码退还给大筹码玩家；仅比较主池。
2. 无重连: 断开连接 = Fold (弃牌)。
3. 无复杂验证: 进入房间只需一个名字；无需注册/登录/电子邮件验证。
4. AI 超时处理: 设置 API 超时为 5 秒；如果 AI 超时，自动选择 `Check` 或 `Fold`。
