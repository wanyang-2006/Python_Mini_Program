import { useState, useEffect } from 'react'
import { View, Text, Textarea } from '@tarojs/components'
import Taro, { useDidShow } from '@tarojs/taro'
import { useQuizStore, Question } from '../../store/quiz'
import './index.css'

const QUICK_TAGS = ['Python 基础', '唐朝历史', '光合作用', 'JavaScript', '消化系统', '二战历史']
const TOPIC_MAP: Record<string, string> = {
  'Python 基础': 'Python 基础语法',
  '唐朝历史': '唐朝历史',
  '光合作用': '光合作用原理',
  'JavaScript': 'JavaScript 基础',
  '消化系统': '人体消化系统',
  '二战历史': '二战历史'
}

interface Stats { count: number; avgPct: number; topics: number }

export default function IndexPage() {
  const [topic, setTopic] = useState('')
  const [selectedTag, setSelectedTag] = useState('')
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<Stats>({ count: 0, avgPct: 0, topics: 0 })
  const { setTopic: setStoreTopic, initSession } = useQuizStore()

  const loadStats = () => {
    try {
      const history: any[] = Taro.getStorageSync('quiz_history') || []
      if (history.length > 0) {
        const avgPct = Math.round(history.reduce((s, h) => s + h.pct, 0) / history.length)
        const topicCount = new Set(history.map((h) => h.topic)).size
        setStats({ count: history.length, avgPct, topics: topicCount })
      }
    } catch {}
  }

  useEffect(() => { loadStats() }, [])
  useDidShow(() => { loadStats() })

  const handleTagClick = (tag: string) => {
    setTopic(TOPIC_MAP[tag] || tag)
    setSelectedTag(tag)
  }

  const handleStart = async () => {
    const t = topic.trim()
    if (!t) {
      Taro.showToast({ title: '请输入学习主题', icon: 'none' })
      return
    }

    setLoading(true)
    Taro.showLoading({ title: 'AI 生成题目中...' })

    try {
      const res: any = await new Promise((resolve, reject) => {
        Taro.request({
          url: 'http://localhost:8000/api/quiz/generate',
          method: 'POST',
          data: { topic: t, question_count: 5 },
          header: { 'Content-Type': 'application/json' },
          success: (r: any) => r.statusCode < 300 ? resolve(r.data) : reject(new Error(r.data?.detail || 'Error')),
          fail: (err: any) => reject(new Error(err.errMsg)),
        })
      })

      setStoreTopic(t)

      // 将 API 返回格式映射为前端 Question 结构
      // API 返回的 questions 包含 id(str), type, stem, options[{key,text}], answer[], explanation, knowledge_point
      // 但不包含 DB 的 question id；需要通过 session 再查，这里直接用后续答题时用 seq 在后端查
      // 解决方案：前端用 seq（index+1）定位题目，后端 answer 接口接受 session_id + seq
      const questions: Question[] = (res.questions as any[]).map((q: any, idx: number) => ({
        id: idx + 1,       // 用 seq（1-based）作为前端 id，答题时传 seq
        apiId: q.id,
        content: q.stem,
        options: q.options.map((o: any) => `${o.key}. ${o.text}`),
        optionKeys: q.options.map((o: any) => o.key),
        correctAnswer: q.answer[0] || 'A',   // 仅用于多选/判断展示（后端会校验）
        explanation: q.explanation,
        tags: [q.knowledge_point],
      }))

      initSession(res.session_id, questions)

      Taro.hideLoading()
      Taro.navigateTo({ url: `/pages/quiz/index` })
    } catch (err: any) {
      Taro.hideLoading()
      Taro.showToast({ title: `出题失败：${err.message || '请检查网络'}`, icon: 'none', duration: 3000 })
    } finally {
      setLoading(false)
    }
  }

  return (
    <View className="index-page">
      {/* Hero */}
      <View className="hero">
        <View className="hero-icon"><Text>🧠</Text></View>
        <Text className="hero-title">输入主题，生成题目闯关</Text>
        <Text className="hero-sub">5 道题测试你的掌握程度，答完立即获得知识总结</Text>
      </View>

      {/* Input card */}
      <View className="card">
        <Text className="input-label">学习主题</Text>
        <Textarea
          className="topic-input"
          value={topic}
          onInput={(e: any) => setTopic(e.detail.value)}
          placeholder="Python 基础语法、唐朝历史..."
          maxlength={100}
        />
        <Text className="char-hint">{topic.length} / 100</Text>
      </View>

      {/* Quick tags */}
      <Text className="tags-label">热门主题</Text>
      <View className="tags-wrap">
        {QUICK_TAGS.map((tag) => (
          <View
            key={tag}
            className={`tag${selectedTag === tag ? ' on' : ''}`}
            onClick={() => handleTagClick(tag)}
          >
            <Text>{tag}</Text>
          </View>
        ))}
      </View>

      {/* Start button */}
      <View className={`btn-primary${loading ? ' btn-loading' : ''}`} onClick={loading ? undefined : handleStart}>
        <Text className="btn-primary-text">{loading ? '生成中...' : '开始闯关 →'}</Text>
      </View>

      {/* Stats row */}
      <View className="stats-row">
        {[
          { num: stats.count || 0, desc: '闯关次数' },
          { num: stats.count > 0 ? `${stats.avgPct}%` : '—', desc: '平均正确率' },
          { num: stats.topics || 0, desc: '掌握主题' }
        ].map((s) => (
          <View key={s.desc} className="stat-card">
            <Text className="stat-num">{s.num}</Text>
            <Text className="stat-desc">{s.desc}</Text>
          </View>
        ))}
      </View>
    </View>
  )
}
