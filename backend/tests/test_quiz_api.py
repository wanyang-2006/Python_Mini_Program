"""后端接口测试（使用真实 DeepSeek API + MySQL）"""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def get_client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.anyio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.anyio
async def test_generate_and_answer_and_report():
    """端到端：出题 → 全部答题 → 生成报告"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. 出题
        gen_resp = await client.post("/api/quiz/generate", json={
            "topic": "Python 变量和数据类型",
            "question_count": 5,
        })
        assert gen_resp.status_code == 200, gen_resp.text
        gen_data = gen_resp.json()
        session_id = gen_data["session_id"]
        questions = gen_data["questions"]
        assert len(questions) == 5
        print(f"\n[generate] session_id={session_id}, 题数={len(questions)}")
        print(f"  第一题：{questions[0]['stem'][:40]}...")

        # 2. 验证数据已写入 DB
        from app.core.database import SessionLocal
        from app.models.quiz import Question as QModel
        db = SessionLocal()
        db_questions = db.query(QModel).filter(QModel.session_id == session_id).order_by(QModel.seq).all()
        db.close()
        assert len(db_questions) == 5
        print(f"  DB questions: {len(db_questions)} rows")

        # 3. 答题：每题答第一个选项（按 seq 传递）
        for idx, q_schema in enumerate(questions):
            first_key = q_schema["options"][0]["key"]
            ans_resp = await client.post("/api/quiz/answer", json={
                "session_id": session_id,
                "seq": idx + 1,
                "user_answer": [first_key],
            })
            assert ans_resp.status_code == 200, ans_resp.text
            ans_data = ans_resp.json()
            print(f"  seq{idx+1} answer:{first_key} correct:{ans_data['is_correct']}")

        # 4. 生成报告
        rpt_resp = await client.post("/api/quiz/report", json={"session_id": session_id})
        assert rpt_resp.status_code == 200, rpt_resp.text
        rpt = rpt_resp.json()
        assert rpt["session_id"] == session_id
        assert rpt["correct_rate"] is not None
        assert len(rpt["summary"]) > 10
        print(f"\n[report] 正确率={rpt['correct_rate']}%")
        print(f"  总结前50字：{rpt['summary'][:50]}...")
        print(f"  建议前50字：{rpt['suggestions'][:50]}...")

    print("\nOK end-to-end test passed")
