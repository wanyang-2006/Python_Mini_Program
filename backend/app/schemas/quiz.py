"""Pydantic 请求/响应 Schema"""
from pydantic import BaseModel, Field


class Option(BaseModel):
    key: str = Field(..., description="选项标识 A/B/C/D 或 对/错")
    text: str = Field(..., description="选项内容")


class QuestionItem(BaseModel):
    """AI 返回的单道题结构（与 LangChain with_structured_output 配合）"""
    id: str = Field(..., description="题号 q1, q2...")
    type: str = Field(..., description="single | multiple | judge")
    stem: str = Field(..., description="题干")
    options: list[Option]
    answer: list[str] = Field(..., description="正确答案，单选/判断一个元素，多选多个")
    explanation: str
    knowledge_point: str
    difficulty: str = Field(..., description="easy | medium | hard")


class QuizBundle(BaseModel):
    """AI 返回的整组题结构"""
    title: str = Field(..., description="学习主题")
    summary: str = Field(..., description="本次题库的主题摘要")
    questions: list[QuestionItem]


# ---------- 出题接口 ----------
class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200, description="学习主题")
    question_count: int = Field(default=5, ge=1, le=10)


class GenerateResponse(BaseModel):
    session_id: int
    title: str
    summary: str
    questions: list[QuestionItem]


# ---------- 答题接口 ----------
class AnswerRequest(BaseModel):
    session_id: int
    seq: int = Field(..., description="题目序号 1-N", ge=1)
    user_answer: list[str]


class AnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: list[str]
    explanation: str


# ---------- 报告接口 ----------
class ReportRequest(BaseModel):
    session_id: int


class ReportResponse(BaseModel):
    session_id: int
    topic: str
    title: str
    summary: str
    suggestions: str
    weak_points: list[str]
    correct_rate: int
    total_questions: int
    correct_count: int


# ---------- 历史会话接口 ----------
class SessionBrief(BaseModel):
    id: int
    topic: str
    status: str
    correct_rate: int | None
    total_questions: int
    created_at: str


class SessionDetail(BaseModel):
    id: int
    topic: str
    title: str
    summary: str
    correct_rate: int | None
    total_questions: int
    created_at: str
    questions: list[QuestionItem]
    user_answers: dict[int, list[str]] | None = None
