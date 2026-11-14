import { useEffect, useState, useMemo } from 'react'
import { View, Text } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useQuizStore } from '../../store/quiz'
import './index.css'

export default function ReportPage() {
  const { topic, questions, answers, sessionId, reset } = useQuizStore()
  const [aiSummary, setAiSummary] = useState('')
  const [aiSuggestions, setAiSuggestions] = useState('')
  const [loadingReport, setLoadingReport] = useState(true)

  const correctCount = answers.filter((a) => a.isCorrect).length
  const total = questions.length || 5
  const pct = total > 0 ? Math.round((correctCount / total) * 100) : 0
  const progressDeg = pct * 3.6

  const evaluation =
    pct >= 80 ? '太棒了！掌握情况优秀'
    : pct >= 60 ? '不错，继续努力'
    : '还需加强，多练习'

  const weakTags = useMemo(() => {
    const set = new Set<string>()
    answers.forEach((a, i) => {
      if (!a.isCorrect && questions[i]) {
        questions[i].tags.forEach((t) => set.add(t))
      }
    })
    return [...set]
  }, [answers, questions])

  // 获取 AI 报告 + 保存历史
  useEffect(() => {
    const sid = sessionId || 0
    if (sid && answers.length > 0) {
      Taro.request({
        url: 'http://localhost:8000/api/quiz/report',
        method: 'POST',
        data: { session_id: sid },
        header: { 'Content-Type': 'application/json' },
        success: (r: any) => {
          if (r.statusCode < 300 && r.data) {
            setAiSummary(r.data.summary || '')
            setAiSuggestions(r.data.suggestions || '')
          }
          setLoadingReport(false)
        },
        fail: () => setLoadingReport(false),
      })
    } else {
      setLoadingReport(false)
    }

    // 保存本地历史
    if (!topic || answers.length === 0) return
    try {
      const hist: any[] = Taro.getStorageSync('quiz_history') || []
      hist.unshift({
        topic, pct, correct: correctCount, total,
        date: new Date().toLocaleString('zh-CN', {
          month: '2-digit', day: '2-digit',
          hour: '2-digit', minute: '2-digit'
        })
      })
      Taro.setStorageSync('quiz_history', hist.slice(0, 20))
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleRestart = () => {
    reset()
    Taro.switchTab({ url: '/pages/index/index' })
  }

  const displaySummary = aiSummary ||
    (`围绕「${topic || '知识主题'}」共作答 ${total} 题，正确率 ${pct}%。` +
    (correctCount === total ? '表现完美，所有知识点掌握扎实！'
    : correctCount >= Math.ceil(total / 2) ? '大部分知识点已掌握，建议复习标注的薄弱环节。'
    : '仍有较多知识点需要加强，建议系统复习相关内容。'))

  return (
    <View className="report-page">
      {/* Score banner */}
      <View className="report-top">
        <Text className="report-topic">主题：{topic || '—'}</Text>
        <View className="big-ring" style={{ background: `conic-gradient(#4A9EDE ${progressDeg}deg, #e8f4fd 0deg)` }}>
          <View className="big-ring-hole">
            <Text className="big-pct">{pct}%</Text>
            <Text className="big-pct-label">正确率</Text>
          </View>
        </View>
        <Text className="evaluation">{evaluation}</Text>
        <Text className="score-detail">答对 {correctCount} / {total} 题</Text>
      </View>

      <View className="report-body">
        {/* Summary */}
        <View className="card">
          <Text className="section-label">知识总结</Text>
          <Text className="summary-text">
            {loadingReport ? 'AI 正在生成总结...' : displaySummary}
          </Text>
          {aiSuggestions ? (
            <>
              <Text className="section-label" style={{ marginTop: '14px' }}>学习建议</Text>
              <Text className="summary-text">{aiSuggestions}</Text>
            </>
          ) : null}
          <Text className="section-label" style={{ marginTop: '14px' }}>薄弱知识点</Text>
          {weakTags.length === 0
            ? <Text className="weak-empty">全部掌握，无薄弱知识点</Text>
            : <View className="weak-tags">
                {weakTags.map((t) => <View key={t} className="weak-tag"><Text>{t}</Text></View>)}
              </View>
          }
        </View>

        {/* Detail list */}
        <View className="card">
          <Text className="section-label">答题明细</Text>
          {answers.map((a, i) => {
            const q = questions[i]
            if (!q) return null
            return (
              <View key={a.questionId} className="detail-item">
                <View className={`detail-no ${a.isCorrect ? 'ok' : 'fail'}`}><Text>{i + 1}</Text></View>
                <View className="detail-text">
                  <Text>{q.content.length > 28 ? q.content.slice(0, 28) + '...' : q.content}</Text>
                  <Text className="detail-ans">你：{a.userAnswer} ｜ 答：{a.correctAnswer}</Text>
                </View>
                <Text style={{ fontSize: '16px' }}>{a.isCorrect ? 'O' : 'X'}</Text>
              </View>
            )
          })}
        </View>

        <View className="btn-restart" onClick={handleRestart}>
          <Text className="btn-restart-text">再来一关 →</Text>
        </View>
      </View>
    </View>
  )
}
