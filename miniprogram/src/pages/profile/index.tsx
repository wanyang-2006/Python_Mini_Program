import { View, Text } from '@tarojs/components'
import Taro from '@tarojs/taro'
import './index.css'

export default function ProfilePage() {
  const handleLogin = () => {
    Taro.showToast({ title: 'Phase 6 功能，敬请期待', icon: 'none' })
  }

  return (
    <View className="profile-page">
      {/* 登录卡片：全部竖排居中 */}
      <View className="profile-hero">
        {/* 头像：居中，大号 */}
        <View className="profile-avatar-wrap">
          <Text className="profile-avatar">👤</Text>
        </View>
        {/* 标题：单独一行居中 */}
        <Text className="profile-title">登录后查看个人信息</Text>
        {/* 描述：每句单独一行居中 */}
        <Text className="profile-desc-line">登录后可保存答题记录</Text>
        <Text className="profile-desc-line">跨设备同步历史成绩</Text>
        {/* 登录按钮 */}
        <View className="profile-login-btn" onClick={handleLogin}>
          <Text className="profile-login-text">微信一键登录</Text>
        </View>
      </View>

      {/* 统计占位（灰显） */}
      <View className="profile-placeholder">
        <Text className="profile-stats-label">我的统计</Text>
        <View className="p-stats-row">
          {[
            { num: '—', desc: '闯关次数' },
            { num: '—', desc: '平均正确率' },
            { num: '—', desc: '掌握主题' }
          ].map((s) => (
            <View key={s.desc} className="p-stat-card">
              <Text className="p-stat-num">{s.num}</Text>
              <Text className="p-stat-desc">{s.desc}</Text>
            </View>
          ))}
        </View>
      </View>

      <Text className="profile-note">登录功能将在 Phase 6 上线</Text>
    </View>
  )
}
