# Phase 5 开发说明 — 核心功能开发（MVP）

> 版本：v1.0 | 日期：2026-11-14 | 阶段：Phase 5（后端接口 + 前端联调）

## 一、阶段目标

跑通 MVP 核心业务闭环：**首页输入主题 → AI 出题 → 逐题答题 + 讲解 → 通关报告 → 历史记录**。

- 后端：FastAPI + LangChain + DeepSeek + MySQL
- 前端：Taro 4.x + Zustand，替换 mock 为真实 API 调用

---

## 二、后端架构

### 目录结构

```
backend/
├── .env.example             # 环境变量示例
├── .gitignore
├── requirements.txt
├── pytest.ini
├── alembic.ini
├── alembic/
│   ├── env.py               # 已改写：自动从 app.core.config 读取连接串
│   └── versions/241e0670c9a8_init_quiz_tables.py
└── app/
    ├── __init__.py
    ├── main.py               # FastAPI 入口 + CORS + 路由注册
    ├── core/
    │   ├── config.py          # pydantic-settings，读取根目录 .env
    │   └── database.py        # SQLAlchemy engine + Base + get_db 依赖
    ├── models/quiz.py         # ORM 模型：QuizSession / Question / Report
    ├── schemas/quiz.py        # Pydantic 请求/响应模型
    ├── services/quiz_service.py  # LangChain 出题/报告 Chain
    └── api/quiz.py            # 4 个 API 路由
```

### 数据库表

| 表 | 字段 | 说明 |
|----|------|------|
| quiz_sessions | id, topic, status, score, total_questions, created_at | 答题会话 |
| questions | id, session_id(FK), seq, question_id, q_type, stem, options_json, answer_json, explanation, knowledge_point, difficulty, user_answer_json, is_correct | 题目（含作答结果）|
| reports | id, session_id(FK), summary, suggestions, weak_points, correct_rate, generated_at | AI 报告 |

### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/quiz/generate` | 出题：输入 topic → 返回 session_id + 5 道结构化题目 |
| POST | `/api/quiz/answer` | 答题：按 session_id + seq 定位题目，返回 is_correct + explanation |
| POST | `/api/quiz/report` | 生成 AI 报告：调用 DeepSeek 生成个性化总结 |
| GET | `/api/quiz/sessions` | 历史会话列表（按 created_at 降序） |
| GET | `/health` | 健康检查 |

### LangChain 出题 Prompt 结构（黄金组合）

- **角色**：专业的 AI 学习教练
- **约束**：5 题，含单选 + 判断 + 多选
- **格式**：每题含 id/type/stem/options/answer/explanation/knowledge_point/difficulty
- **范例**：JSON 结构示例
- **变量**：`{topic}` + `{question_count}`

`with_structured_output(QuizBundle)` 用 Pydantic 模型约束 JSON 输出，避免 DeepSeek 返回格式错误（DeepSeek 不支持 `response_format` 参数）。

---

## 三、前端改动点

| 文件 | 改动 |
|------|------|
| `src/utils/request.ts` | 新增：统一请求封装 + `api` 对象 |
| `src/store/quiz.ts` | `sessionId` 改为 `number`；`Question` 加 `apiId`；`AnswerRecord` 加 `explanation` |
| `src/pages/index/index.tsx` | 替换 mock：真实调用 `/api/quiz/generate` + loading 状态 |
| `src/pages/quiz/index.tsx` | 替换本地判断：调用 `/api/quiz/answer`，按 seq 提交 |
| `src/pages/report/index.tsx` | 新增：调用 `/api/quiz/report` 获取 AI 总结 + 学习建议 |
| `src/pages/history/index.tsx` | 不变（仍用本地存储；Phase 6 迁服务端）|

### 请求基础地址

`http://localhost:8000`（开发时微信开发者工具需勾选"不校验合法域名"）

### 答题定位策略

前端不知道数据库 question.id，通过 `session_id + seq`（题序 1-N）定位题目。后端 `/api/quiz/answer` 已适配此方式。

---

## 四、启动方式

### 后端

```bash
cd backend
.venv/Scripts/activate      # Windows
python -m app.main
# 访问 http://localhost:8000/docs 查看 Swagger
```

### 前端（微信开发者工具）

```bash
cd miniprogram
npm run dev:weapp
# 用微信开发者工具导入 miniprogram/dist/
```

### 测试

```bash
cd backend
.venv/Scripts/pytest tests/ -v -s
# 会真实调用 DeepSeek，约 30-60 秒
```

---

## 五、已知问题与 Phase 6 待办

| 问题 | 处理 |
|------|------|
| 历史记录仅本地存储 | Phase 6 迁移服务端（需用户登录）|
| 多选题/判断题前端展示统一为单选样式 | Phase 5 已支持后端，前端可后续优化 |
| AI 响应时间约 5-15 秒 | 前端已加 loading 状态 + 超时容错 |
| DeepSeek 偶发返回 JSON 不完整 | LangChain `with_structured_output` 自动重试 |

---

## 六、版本与依赖

### Python 3.14 兼容性处理

| 包 | 版本 | 说明 |
|----|------|------|
| pydantic | 2.14.3 | 必须用此版本，2.10.x 的 pydantic-core 无 Py3.14 wheel |
| sqlalchemy | 2.1.8 | 必须升级，2.0.x 与 Py3.14 的 Optional 类型注解不兼容 |
| alembic | 1.14.0 | 标准版 |
| langchain | 0.3.9 | 含 langchain-openai 0.2.10 |
| fastapi | 0.115.5 | 标准版 |

### alembic 中文路径处理

`alembic` CLI 在中文路径下找不到 `alembic.ini`，已改为通过 Python 脚本调用 `Config` + `command.upgrade`。详见 `backend/alembic/env.py`。
