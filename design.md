# 简易版多人 AI 德州扑克设计文档 (SimpleHoldem-AI)

## 1. 项目愿景
构建一个轻量级、无需复杂部署的多人在线德州扑克游戏。
- **核心特色**：真人玩家与 LLM (大模型) 驱动的 AI 玩家同台竞技。
- **架构哲学**：单体应用 (Monolith) + 内存状态管理。优先保证开发效率和代码可读性，适合个人开发者快速构建 MVP。

## 2. 技术栈选型 (Python 全栈)
- **后端框架**: `FastAPI` (处理 HTTP 和 WebSocket，原生支持异步)。
- **网络协议**: `WebSocket` (实时对局通信)。
- **数据存储**:
    - **热数据**: Python **内存** (全局字典 `Dict`) —— *存储房间、对局状态，速度最快，无外部依赖。*
    - **持久化 (可选)**: `SQLite` —— *仅用于存储基础配置或用户凭证（MVP阶段可省略）。*
- **AI 交互**: `OpenAI SDK` (或兼容接口，如 DeepSeek/Claude) + `AsyncIO`。
- **前端**: HTML5 + Vue.js/React (推荐 CDN 引入方式，无需构建工具)。

## 3. 系统架构设计

### 3.1 模块划分 (目录结构)
整个后端为一个单一的 Python 项目，避免微服务带来的复杂性。

```text
/app
  ├── main.py            # 入口：启动 FastAPI，挂载路由
  ├── models.py          # 数据结构：定义 Player, Room, GameState 等类
  ├── game_engine.py     # 核心逻辑：洗牌、发牌、比牌、底池计算、状态机
  ├── connection_mgr.py  # 网络层：管理 WebSocket 连接，处理广播
  └── ai_agent.py        # AI 层：封装 LLM 的 Prompt 和 API 调用
```

### 3.2 运行时架构图 (Mermaid)

graph TD
    ClientA[真人玩家 A] <-->|WebSocket| API[FastAPI 网关]
    ClientB[真人玩家 B] <-->|WebSocket| API
    
    subgraph "后端服务器 (单进程)"
        API --> Manager[连接管理器]
        API --> Engine[游戏状态机 (内存)]
        
        Engine -- 轮到AI --> AI_Mod[AI 模块]
        AI_Mod -- HTTP请求 --> LLM_Cloud[大模型 API]
    end
    
    Manager -- 广播 JSON --> ClientA
    Manager -- 广播 JSON --> ClientB

## 4. 核心数据模型 (内存对象)
这些对象直接存在内存中，服务器重启即重置，极大简化开发。

### 4.1 房间 (Room)
```python
class Room:
    id: str
    players: List[Player]      # 包含真人与AI
    deck: List[str]            # 牌堆 (e.g., ['Ah', 'Td'])
    community_cards: List[str] # 公共牌
    pot: int                   # 当前底池
    current_actor_index: int   # 当前轮到谁行动 (Seat Index)
    stage: str                 # PREFLOP, FLOP, TURN, RIVER, SHOWDOWN
```

### 4.2 玩家 (Player)
```python
class Player:
    id: str
    is_ai: bool           # 关键标记：是否为 AI
    chips: int            # 剩余筹码
    hand: List[str]       # 手牌 ['Ah', 'Kd']
    status: str           # WAITING, PLAYING, FOLDED, ALLIN
    websocket: WebSocket  # 仅真人有此连接对象，AI 为 None
```

## 5. 核心逻辑流程
### 5.1 游戏主循环 (State Machine)
这是整个游戏的心脏，位于 game_engine.py。

1. WaitForAction: 服务器等待当前玩家操作。

2. ActionReceived:

 - 真人: 通过 WebSocket 收到 JSON `{"action": "raise", "amount": 100}`。

 - AI: 内部触发，调用 LLM 获取 JSON。

3. Validate: 检查操作合法性（钱够不够？是不是轮到你？）。

4. UpdateState: 更新底池、玩家筹码、下注轮次。

5. CheckStageEnd: 检查本轮下注是否结束？

 - 是: 发公共牌 -> 进入下一阶段 (如 FLOP -> TURN)。

 - 否: 移动`current_actor_index`到下一位玩家。

6. Broadcast: 将最新的`GameState`推送给所有客户端。

### 5.2 AI 决策流程 (关键路径)
当`current_actor_index`指向一个`is_ai=True`的玩家时：

1. 暂停等待: 不再等待 WebSocket 消息。

2. 构建 Prompt: 收集场上信息（公共牌、底池、AI手牌、前序动作）。

3. 异步调用:`await llm_client.chat.completions.create(...)`。

4. 解析执行: 拿到结果后，直接调用`engine.process_action()`，假装是真人点的按钮。

5. 延迟模拟: 为了真实感，可以在 AI 思考前加`await asyncio.sleep(1)`。

## 6. 接口协议设计
### 6.1 WebSocket 消息格式
客户端 -> 服务端:

```JSON
{
  "type": "action",
  "data": {
    "action": "call",  // fold, check, call, raise, allin
    "amount": 0
  }
}
```

服务端 -> 客户端 (广播):

```JSON
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

## 7. MVP 开发路线图 (建议顺序)
阶段一：单机控制台版 (The Core)

- 目标：不写网络，只写 Python 类。

- 工作：实现发牌、洗牌、胜负判定（建议用 treys 库）、简单的 AI（随机乱出牌）。

- 测试：在 Terminal 里跑通一局游戏，确保钱算得对。

阶段二：接入大脑 (The Brain)

- 目标：让 AI 变聪明。

- 工作：编写 Prompt，接入 OpenAI API。

- 测试：在 Terminal 里跟 AI 对打，看它会不会诈你。

阶段三：服务器化 (The Server)

- 目标：多人连接。

- 工作：引入 FastAPI 和 WebSocket，把阶段一的逻辑包装起来。

- 测试：用 Postman 或简单的 HTML 页面连接 WS，能看到 JSON 数据在跳动。

阶段四：图形界面 (The Face)

- 目标：能玩。

- 工作：画一个简单的 Web 页面（显示公共牌、自己的牌、操作按钮）。

## 8. 避坑指南 (针对个人项目)
1. 不做 Side Pot (边池)：如果多人 All-in 且筹码不同，计算极其复杂。MVP 规则：多余的筹码退回给大筹码玩家，只比主池。

2. 不做断线重连：掉线就当 Fold（弃牌）。

3. 不做复杂的鉴权：进房间只要输入一个名字即可，不需要注册登录发邮件验证码。

4. AI 超时处理：设置 API 调用超时为 5 秒，如果 AI 没反应，代码自动替它选`Check`或`Fold`。