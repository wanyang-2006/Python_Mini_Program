import { useState, useEffect } from 'react'
import { View, Text } from '@tarojs/components'
import Taro, { useLoad } from '@tarojs/taro'
import { useQuizStore, MOCK_QUESTIONS } from '../../store/quiz'
import './index.css'

export default function QuizPage() {
  const {
    topic, questions, currentIndex, sessionId,
    initSession, submitAnswer, nextQuestion
  } = useQuizStore()

  const [selectedOption, setSelectedOption] = useState('')
  const [hasAnswered, setHasAnswered] = useState(false)
  const [isCorrect, setIsCorrect] = useState(false)
  const [correctAnswer, setCorrectAnswer] = useState('')
  const [explanation, setExplanation] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // 切题时重置状态
  useEffect(() => {
    setSelectedOption('')
    setHasAnswered(false)
    setIsCorrect(false)
    setCorrectAnswer('')
    setExplanation('')
  }, [currentIndex])

  useLoad(() => {
    // 冷启动保护：store 为空时用 mock
    if (useQuizStore.getState().questions.length === 0) {
      useQuizStore.getState().initSession(0, MOCK_QUESTIONS)
    }
    const t = useQuizStore.getState().topic
    if (t) {
      Taro.setNavigationBarTitle({ title: t.length > 10 ? t.slice(0, 10) + '...' : t })
    }
  })

  const q = questions[currentIndex]
  if (!q) {
    return (
      <View className="quiz-page">
        <View className="quiz-body">
          <Text style={{ fontSize: '14px', color: '#8fa9be' }}>加载中...</Text>
        </View>
      </View>
    )
  }

  const progressDeg = ((currentIndex + 1) / 5) * 360

  const handleSelect = async (key: string) => {
    if (hasAnswered || submitting) return
    setSelectedOption(key)
    setSubmitting(true)

    try {
      const sid = sessionId || 0
      const result: any = await new Promise((resolve, reject) => {
        Taro.request({
          url: 'http://localhost:8000/api/quiz/answer',
          method: 'POST',
          data: { session_id: sid, seq: currentIndex + 1, user_answer: [key] },
          header: { 'Content-Type': 'application/json' },
          success: (r: any) => r.statusCode < 300 ? resolve(r.data) : reject(new Error(r.data?.detail || 'Error')),
          fail: (err: any) => reject(new Error(err.errMsg)),
        })
      })

      setIsCorrect(result.is_correct)
      setCorrectAnswer(result.correct_answer[0] || key)
      setExplanation(result.explanation)
      setHasAnswered(true)

      submitAnswer({
        questionId: q.id,
        userAnswer: key,
        correctAnswer: result.correct_answer[0] || key,
        isCorrect: result.is_correct,
        explanation: result.explanation,
      })
    } catch {
      // 网络失败时回退到本地判断
      const localCorrect = key === q.correctAnswer
      setIsCorrect(localCorrect)
      setCorrectAnswer(q.correctAnswer)
      setExplanation(q.explanation)
      setHasAnswered(true)
      submitAnswer({
        questionId: q.id,
        userAnswer: key,
        correctAnswer: q.correctAnswer,
        isCorrect: localCorrect,
        explanation: q.explanation,
      })
    } finally {
      setSubmitting(false)
    }
  }

  const getOptClass = (key: string): string => {
    if (!hasAnswered) return selectedOption === key ? 'option-btn selected' : 'option-btn'
    if (key === correctAnswer) return 'option-btn correct'
    if (key === selectedOption && !isCorrect) return 'option-btn wrong'
    return 'option-btn'
  }

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      nextQuestion()
    } else {
      Taro.navigateTo({ url: '/pages/report/index' })
    }
  }

  return (
    <View className="quiz-page">
      {/* Progress header */}
      <View className="quiz-top">
        <View
          className="ring"
          style={{ background: `conic-gradient(#4A9EDE ${progressDeg}deg, #e8eff6 0deg)` }}
        >
          <View className="ring-hole">
            <Text className="ring-no">{currentIndex + 1}</Text>
            <Text className="ring-of">/ {questions.length}</Text>
          </View>
        </View>
        <View className="quiz-meta">
          <Text className="quiz-topic">{topic || '答题闯关'}</Text>
          <Text className="quiz-difficulty">第 {currentIndex + 1} 题 · 共 {questions.length} 题</Text>
        </View>
      </View>

      {/* Question card */}
      <View className="quiz-body">
        <View className="card">
          <View className="type-badge"><Text>单选题</Text></View>
          <Text className="q-content">{q.content}</Text>

          <View className="options-wrap">
            {q.optionKeys.map((key, i) => (
              <View
                key={key}
                className={getOptClass(key)}
                onClick={() => handleSelect(key)}
              >
                <View className="opt-key"><Text>{key}</Text></View>
                <Text className="opt-text">{q.options[i].substring(3)}</Text>
              </View>
            ))}
          </View>

          {hasAnswered && (
            <View className={`result-panel ${isCorrect ? 'correct' : 'wrong'}`}>
              <Text className={`result-title ${isCorrect ? 'c' : 'w'}`}>
                {isCorrect ? '回答正确' : `正确答案：${correctAnswer}`}
              </Text>
              <Text className="result-explain">{explanation}</Text>
            </View>
          )}

          {hasAnswered && (
            <View className="btn-next" onClick={handleNext}>
              <Text className="btn-next-text">
                {currentIndex < questions.length - 1 ? '下一题 →' : '查看报告'}
              </Text>
            </View>
          )}
        </View>
      </View>
    </View>
  )
}
