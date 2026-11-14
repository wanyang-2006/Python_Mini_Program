"""Quiz 相关路由"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.quiz import QuizSession, Question, Report
from app.schemas.quiz import (
    GenerateRequest, GenerateResponse,
    AnswerRequest, AnswerResponse,
    ReportRequest, ReportResponse,
    SessionBrief, QuestionItem, Option,
)
from app.services.quiz_service import generate_quiz, generate_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/quiz", tags=["quiz"])


def _question_to_schema(q: Question) -> QuestionItem:
    opts_raw = q.options  # list of dicts
    return QuestionItem(
        id=q.question_id,
        type=q.q_type,
        stem=q.stem,
        options=[Option(key=o["key"], text=o["text"]) for o in opts_raw],
        answer=q.answer,
        explanation=q.explanation,
        knowledge_point=q.knowledge_point,
        difficulty=q.difficulty,
    )


# ----------------------------------------------------------------
# POST /api/quiz/generate  — 生成题库
# ----------------------------------------------------------------
@router.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest, db: Session = Depends(get_db)):
    try:
        bundle = generate_quiz(req.topic, req.question_count)
    except Exception as e:
        logger.error("Quiz generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"题库生成失败：{e}")

    # 保存 session
    session = QuizSession(
        topic=req.topic,
        total_questions=len(bundle.questions),
        status="ongoing",
    )
    db.add(session)
    db.flush()  # 获取 session.id

    # 保存题目
    for idx, q in enumerate(bundle.questions, start=1):
        question = Question(
            session_id=session.id,
            seq=idx,
            question_id=q.id,
            q_type=q.type,
            stem=q.stem,
            options_json=json.dumps([o.model_dump() for o in q.options], ensure_ascii=False),
            answer_json=json.dumps(q.answer, ensure_ascii=False),
            explanation=q.explanation,
            knowledge_point=q.knowledge_point,
            difficulty=q.difficulty,
        )
        db.add(question)

    db.commit()
    db.refresh(session)

    return GenerateResponse(
        session_id=session.id,
        title=bundle.title,
        summary=bundle.summary,
        questions=bundle.questions,
    )


# ----------------------------------------------------------------
# POST /api/quiz/answer  — 提交单题答案（按 seq 定位题目）
# ----------------------------------------------------------------
@router.post("/answer", response_model=AnswerResponse)
def answer(req: AnswerRequest, db: Session = Depends(get_db)):
    q = (
        db.query(Question)
        .filter(Question.session_id == req.session_id, Question.seq == req.seq)
        .first()
    )
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    correct_ans = sorted(q.answer)
    user_ans = sorted(req.user_answer)
    is_correct = user_ans == correct_ans

    q.user_answer_json = json.dumps(req.user_answer, ensure_ascii=False)
    q.is_correct = is_correct
    db.commit()

    return AnswerResponse(
        is_correct=is_correct,
        correct_answer=q.answer,
        explanation=q.explanation,
    )


# ----------------------------------------------------------------
# POST /api/quiz/report  — 生成报告
# ----------------------------------------------------------------
@router.post("/report", response_model=ReportResponse)
def report(req: ReportRequest, db: Session = Depends(get_db)):
    session = db.get(QuizSession, req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    questions = session.questions
    total = len(questions)
    correct_count = sum(1 for q in questions if q.is_correct)
    correct_rate = round(correct_count / total * 100) if total > 0 else 0

    # 薄弱知识点
    weak_set: set[str] = set()
    wrong_items: list[str] = []
    for q in questions:
        if not q.is_correct:
            weak_set.add(q.knowledge_point)
            ua = json.loads(q.user_answer_json) if q.user_answer_json else []
            wrong_items.append(
                f"题目：{q.stem[:50]}…  正确答案：{q.answer}  你的答案：{ua}"
            )

    # 检查是否已有报告
    if session.report:
        rpt = session.report
    else:
        try:
            ai_rpt = generate_report(
                topic=session.topic,
                total=total,
                correct=correct_count,
                weak_points=list(weak_set),
                wrong_items=wrong_items,
            )
        except Exception as e:
            logger.error("Report generation failed: %s", e)
            raise HTTPException(status_code=500, detail=f"报告生成失败：{e}")

        rpt = Report(
            session_id=session.id,
            summary=ai_rpt.summary,
            suggestions=ai_rpt.suggestions,
            weak_points=json.dumps(list(weak_set), ensure_ascii=False),
            correct_rate=correct_rate,
        )
        db.add(rpt)
        session.status = "done"
        session.score = correct_count
        db.commit()
        db.refresh(rpt)

    return ReportResponse(
        session_id=session.id,
        topic=session.topic,
        title=session.topic,
        summary=rpt.summary,
        suggestions=rpt.suggestions,
        weak_points=json.loads(rpt.weak_points),
        correct_rate=rpt.correct_rate,
        total_questions=total,
        correct_count=correct_count,
    )


# ----------------------------------------------------------------
# GET /api/quiz/sessions  — 历史会话列表
# ----------------------------------------------------------------
@router.get("/sessions", response_model=list[SessionBrief])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(QuizSession).order_by(QuizSession.created_at.desc()).limit(50).all()
    result = []
    for s in sessions:
        rpt = s.report
        result.append(SessionBrief(
            id=s.id,
            topic=s.topic,
            status=s.status,
            correct_rate=rpt.correct_rate if rpt else None,
            total_questions=s.total_questions,
            created_at=s.created_at.strftime("%Y-%m-%d %H:%M"),
        ))
    return result
