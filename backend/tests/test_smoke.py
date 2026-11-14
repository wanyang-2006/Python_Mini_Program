"""
冒烟测试 + 灰度测试 + 异常路径测试
- 不调用真实 DeepSeek（避免费用/耗时），仅测试路由可达性与数据流
- 用 monkeypatch 替换 quiz_service 的 LLM 调用为 mock 数据
"""
import json
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.schemas.quiz import QuizBundle, QuestionItem, Option


# ---- mock LLM 返回 ----
MOCK_BUNDLE = QuizBundle(
    title="Python 基础语法",
    summary="测试用摘要",
    questions=[
        QuestionItem(
            id="q1", type="single",
            stem="以下哪个是 Python 合法变量名？",
            options=[Option(key="A", text="_my_var"), Option(key="B", text="1abc")],
            answer=["A"],
            explanation="变量名须以下划线或字母开头",
            knowledge_point="变量命名",
            difficulty="easy",
        ),
        QuestionItem(
            id="q2", type="judge",
            stem="Python 是编译型语言。",
            options=[Option(key="对", text="对"), Option(key="错", text="错")],
            answer=["错"],
            explanation="Python 是解释型语言。",
            knowledge_point="语言特性",
            difficulty="medium",
        ),
    ],
)

MOCK_REPORT = type("R", (), {"summary": "测试总结：基础掌握尚可", "suggestions": "建议：多练变量命名"})()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def patch_llm(monkeypatch):
    """替换 LLM 调用为 mock 数据（patch 使用点，不是定义点）"""
    monkeypatch.setattr("app.api.quiz.generate_quiz", lambda *a, **k: MOCK_BUNDLE)
    monkeypatch.setattr("app.api.quiz.generate_report", lambda *a, **k: MOCK_REPORT)


async def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ============================================================
# 1. 冒烟测试：每个接口路由可达
# ============================================================
@pytest.mark.anyio
async def test_smoke_health():
    """健康检查"""
    async with await client() as c:
        r = await c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.anyio
async def test_smoke_generate():
    """出题接口可达，返回结构正确"""
    async with await client() as c:
        r = await c.post("/api/quiz/generate", json={"topic": "Python 基础", "question_count": 5})
    assert r.status_code == 200, r.text
    d = r.json()
    assert "session_id" in d and isinstance(d["session_id"], int)
    assert "title" in d and "summary" in d
    assert isinstance(d["questions"], list) and len(d["questions"]) >= 2
    # 验证题目字段完整
    q0 = d["questions"][0]
    for k in ["id", "type", "stem", "options", "answer", "explanation", "knowledge_point", "difficulty"]:
        assert k in q0, f"缺失字段 {k}"


@pytest.mark.anyio
async def test_smoke_sessions_list():
    """历史会话列表可达"""
    async with await client() as c:
        r = await c.get("/api/quiz/sessions")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ============================================================
# 2. 答题接口：全对 / 全错 / 边界
# ============================================================
async def _setup_session():
    """创建一个会话，返回 (client, session_id, questions)"""
    c = await client()
    ctx = await c.__aenter__()
    r = await ctx.post("/api/quiz/generate", json={"topic": "测试主题", "question_count": 5})
    return ctx, r.json()["session_id"], r.json()["questions"]


@pytest.mark.anyio
async def test_answer_all_correct():
    """全对：每题答正确答案"""
    async with await client() as c:
        r = await c.post("/api/quiz/generate", json={"topic": "T", "question_count": 5})
        sid = r.json()["session_id"]
        qs = r.json()["questions"]
        for idx, q in enumerate(qs):
            ar = await c.post("/api/quiz/answer", json={
                "session_id": sid, "seq": idx + 1, "user_answer": q["answer"],
            })
            assert ar.status_code == 200
            assert ar.json()["is_correct"] is True
        # 生成报告
        rr = await c.post("/api/quiz/report", json={"session_id": sid})
        assert rr.status_code == 200
        assert rr.json()["correct_rate"] == 100


@pytest.mark.anyio
async def test_answer_all_wrong():
    """全错：答错答案"""
    async with await client() as c:
        r = await c.post("/api/quiz/generate", json={"topic": "T", "question_count": 5})
        sid = r.json()["session_id"]
        qs = r.json()["questions"]
        for idx, q in enumerate(qs):
            wrong = ["Z"]  # 必然错误
            ar = await c.post("/api/quiz/answer", json={
                "session_id": sid, "seq": idx + 1, "user_answer": wrong,
            })
            assert ar.json()["is_correct"] is False
        rr = await c.post("/api/quiz/report", json={"session_id": sid})
        assert rr.json()["correct_rate"] == 0


@pytest.mark.anyio
async def test_answer_partial():
    """部分正确"""
    async with await client() as c:
        r = await c.post("/api/quiz/generate", json={"topic": "T", "question_count": 5})
        sid = r.json()["session_id"]
        qs = r.json()["questions"]
        # 第1题对，第2题错
        await c.post("/api/quiz/answer", json={"session_id": sid, "seq": 1, "user_answer": qs[0]["answer"]})
        await c.post("/api/quiz/answer", json={"session_id": sid, "seq": 2, "user_answer": ["Z"]})
        rr = await c.post("/api/quiz/report", json={"session_id": sid})
        assert rr.json()["correct_rate"] == 50


# ============================================================
# 3. 异常路径测试
# ============================================================
@pytest.mark.anyio
async def test_generate_empty_topic():
    """空主题"""
    async with await client() as c:
        r = await c.post("/api/quiz/generate", json={"topic": "", "question_count": 5})
    assert r.status_code == 422  # Pydantic 校验失败


@pytest.mark.anyio
async def test_generate_too_many_questions():
    """题数超限（>10）"""
    async with await client() as c:
        r = await c.post("/api/quiz/generate", json={"topic": "T", "question_count": 99})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_answer_nonexistent_session():
    """答题：不存在的 session"""
    async with await client() as c:
        r = await c.post("/api/quiz/answer", json={
            "session_id": 999999, "seq": 1, "user_answer": ["A"],
        })
    assert r.status_code == 404


@pytest.mark.anyio
async def test_answer_invalid_seq():
    """答题：seq 越界"""
    async with await client() as c:
        r = await c.post("/api/quiz/generate", json={"topic": "T", "question_count": 5})
        sid = r.json()["session_id"]
        r2 = await c.post("/api/quiz/answer", json={
            "session_id": sid, "seq": 999, "user_answer": ["A"],
        })
    assert r2.status_code == 404


@pytest.mark.anyio
async def test_answer_missing_field():
    """答题：缺字段"""
    async with await client() as c:
        r = await c.post("/api/quiz/answer", json={"session_id": 1})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_report_nonexistent_session():
    """报告：不存在的 session"""
    async with await client() as c:
        r = await c.post("/api/quiz/report", json={"session_id": 999999})
    assert r.status_code == 404


@pytest.mark.anyio
async def test_report_idempotent():
    """报告幂等：重复调用不会重复生成"""
    async with await client() as c:
        r = await c.post("/api/quiz/generate", json={"topic": "T", "question_count": 5})
        sid = r.json()["session_id"]
        await c.post("/api/quiz/answer", json={"session_id": sid, "seq": 1, "user_answer": r.json()["questions"][0]["answer"]})
        await c.post("/api/quiz/answer", json={"session_id": sid, "seq": 2, "user_answer": ["Z"]})
        r1 = await c.post("/api/quiz/report", json={"session_id": sid})
        r2 = await c.post("/api/quiz/report", json={"session_id": sid})
        # 第二次应返回相同的报告内容（不会重新调 LLM）
        assert r1.json()["summary"] == r2.json()["summary"]
