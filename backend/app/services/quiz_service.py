"""LangChain + DeepSeek 出题 / 报告服务"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from app.schemas.quiz import QuizBundle, Option, QuestionItem


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.7,
        max_tokens=4096,
    )


# ================================================================
# 出题 Chain
# ================================================================
QUIZ_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "你是一名专业的 AI 学习教练，请根据用户提供的学习内容生成一组用于小程序闯关答题的题目。\n\n"
        "要求：\n"
        "1. 题目总数为 {question_count} 题。\n"
        "2. 题型分布：{question_count} 题中包含至少 2 道单选题（single）、"
        "至少 1 道判断题（judge）、剩余为单选题。若题数 ≥ 5，则包含 1 道多选题（multiple）。\n"
        "3. 每道题必须包含：题号(id)、题型(type)、题干(stem)、选项(options)、"
        "正确答案(answer)、详细讲解(explanation)、知识点标签(knowledge_point)、难度(difficulty)。\n"
        "4. 单选题答案格式：[\"A\"]；多选题：[\"A\",\"B\"]；判断题选项为 对/错，答案为 [\"对\"] 或 [\"错\"]。\n"
        "5. 讲解必须适合初学者，避免过度学术化。\n"
        "6. 输入内容过短时，可基于常识补充，但不要偏离主题。\n"
        "7. 同时输出 title（主题标题）和 summary（本次题库摘要）。"
    )),
    ("human", "学习主题：{topic}"),
])


def generate_quiz(topic: str, question_count: int = 5) -> QuizBundle:
    """调用 DeepSeek 生成题库，返回 QuizBundle（含结构化题目）"""
    llm = _get_llm()
    structured_llm = llm.with_structured_output(QuizBundle)
    chain = QUIZ_PROMPT | structured_llm
    result: QuizBundle = chain.invoke({
        "topic": topic,
        "question_count": question_count,
    })
    return result


# ================================================================
# 报告生成 Chain
# ================================================================
REPORT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "你是一名专业的 AI 学习教练，根据学生的答题情况生成个性化学习报告。\n\n"
        "要求：\n"
        "1. 生成一段精炼的知识总结（summary），100-200字，围绕学习主题展开。\n"
        "2. 生成针对学生薄弱点的学习建议（suggestions），100-150字，具体可操作。\n"
        "3. 语气亲切鼓励，适合中学生或初学者阅读。\n"
        "4. 仅输出 summary 和 suggestions 两个字段的 JSON，不要其他内容。"
    )),
    ("human", (
        "学习主题：{topic}\n"
        "答题情况：共 {total} 题，答对 {correct} 题（正确率 {rate}%）\n"
        "薄弱知识点：{weak_points}\n"
        "答错题目：\n{wrong_items}"
    )),
])


class ReportContent:
    summary: str
    suggestions: str

    def __init__(self, summary: str, suggestions: str):
        self.summary = summary
        self.suggestions = suggestions


from pydantic import BaseModel


class ReportOutput(BaseModel):
    summary: str
    suggestions: str


def generate_report(
    topic: str,
    total: int,
    correct: int,
    weak_points: list[str],
    wrong_items: list[str],
) -> ReportOutput:
    """根据答题情况生成 AI 报告"""
    llm = _get_llm()
    structured_llm = llm.with_structured_output(ReportOutput)
    chain = REPORT_PROMPT | structured_llm
    rate = round(correct / total * 100) if total > 0 else 0
    weak_str = "、".join(weak_points) if weak_points else "无"
    wrong_str = "\n".join(wrong_items) if wrong_items else "无"
    result: ReportOutput = chain.invoke({
        "topic": topic,
        "total": total,
        "correct": correct,
        "rate": rate,
        "weak_points": weak_str,
        "wrong_items": wrong_str,
    })
    return result
