"""SQLAlchemy 数据模型"""
from datetime import datetime
from typing import Optional
import json
from sqlalchemy import String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(200), nullable=False, comment="学习主题")
    status: Mapped[str] = mapped_column(String(20), default="ongoing", comment="ongoing|done")
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="得分")
    total_questions: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # Phase 6 加 user_id FK

    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="session", cascade="all, delete-orphan"
    )
    report: Mapped[Optional["Report"]] = relationship(
        "Report", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("quiz_sessions.id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False, comment="题序 1-5")
    question_id: Mapped[str] = mapped_column(String(20), nullable=False, comment="AI给出的id")
    q_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="single|multiple|judge")
    stem: Mapped[str] = mapped_column(Text, nullable=False, comment="题干")
    # options JSON: [{"key":"A","text":"..."}]
    options_json: Mapped[str] = mapped_column(Text, nullable=False, comment="选项 JSON")
    # answer JSON: ["A"] 或 ["A","B"] 或 ["对"]
    answer_json: Mapped[str] = mapped_column(String(100), nullable=False, comment="正确答案 JSON")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, comment="知识讲解")
    knowledge_point: Mapped[str] = mapped_column(String(200), nullable=False, comment="知识点标签")
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, comment="easy|medium|hard")
    # 用户作答
    user_answer_json: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    session: Mapped["QuizSession"] = relationship("QuizSession", back_populates="questions")

    @property
    def options(self) -> list:
        return json.loads(self.options_json)

    @property
    def answer(self) -> list:
        return json.loads(self.answer_json)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_sessions.id"), nullable=False, unique=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False, comment="AI知识总结")
    suggestions: Mapped[str] = mapped_column(Text, nullable=False, comment="学习建议")
    weak_points: Mapped[str] = mapped_column(Text, default="[]", comment="薄弱知识点 JSON")
    correct_rate: Mapped[int] = mapped_column(Integer, nullable=False, comment="正确率 0-100")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["QuizSession"] = relationship("QuizSession", back_populates="report")
