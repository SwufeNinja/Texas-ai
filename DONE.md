# 已完成的功能记录

## 核心引擎与规则
- 建立基础数据模型（玩家、房间、阶段、状态），支持盲注、下注回合与阶段推进。对应文件：`app/models.py`
- 实现核心状态机：发牌、行动处理、下注轮结算、阶段切换（含全员 All-in 直接补牌到河牌）。对应文件：`app/game_engine.py`
- 增加牌力评估与胜负结算（无边池）：支持常见牌型比较并在摊牌时分配底池。对应文件：`app/hand_eval.py`、`app/game_engine.py`

## 控制台验证工具
- 增加控制台演示脚本，可通过 `scripted/random/interactive` 模式运行以压力测试状态机。对应文件：`app/console_runner.py`
- 补充运行说明与示例命令。对应文件：`RUNNING.md`

## 最小网络版（FastAPI + WebSocket）
- 新增 WebSocket 连接管理与广播能力。对应文件：`app/connection_mgr.py`
- 新增 FastAPI 服务入口，支持 join、action、game_update、error 的最小协议流程。对应文件：`app/main.py`
