import { useState } from 'react'
import { View, Text } from '@tarojs/components'
import Taro, { useDidShow } from '@tarojs/taro'
import './index.css'

interface HistItem {
  topic: string
  pct: number
  correct: number
  total: number
  date: string
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistItem[]>([])

  const loadHistory = () => {
    try {
      const list: HistItem[] = Taro.getStorageSync('quiz_history') || []
      setHistory(list)
    } catch {
      setHistory([])
    }
  }

  useDidShow(() => { loadHistory() })

  const handleItemClick = (item: HistItem) => {
    Taro.showToast({
      title: `${item.topic} · ${item.pct}%`,
      icon: 'none'
    })
  }

  return (
    <View className="history-page">
      {history.length === 0 ? (
        <View className="empty-state">
          <Text className="empty-icon">📭</Text>
          <Text className="empty-title">还没有答题记录</Text>
          <Text className="empty-sub">去首页开始第一次闯关吧</Text>
        </View>
      ) : (
        history.map((item, idx) => (
          <View
            key={idx}
            className="history-item"
            onClick={() => handleItemClick(item)}
          >
            <View className="history-icon"><Text>📚</Text></View>
            <View className="history-info">
              <Text className="history-topic">{item.topic}</Text>
              <Text className="history-meta">
                {item.date} · {item.correct}/{item.total} 题答对
              </Text>
            </View>
            <View className="history-score">
              <Text className={`history-pct${item.pct < 60 ? ' low' : ''}`}>
                {item.pct}%
              </Text>
              <Text className="history-pct-lbl">正确率</Text>
            </View>
          </View>
        ))
      )}
    </View>
  )
}
