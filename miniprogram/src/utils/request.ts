/**
 * 统一请求封装
 * 开发时 BASE_URL 指向本地后端，微信开发者工具需勾选"不校验合法域名"
 */
const BASE_URL = 'http://localhost:8000'

interface ApiResponse<T = unknown> {
  data: T
  status: number
}

export function request<T = unknown>(
  url: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  data?: unknown
): Promise<T> {
  return new Promise((resolve, reject) => {
    // @ts-ignore — Taro.request 在小程序环境下可用
    wx.request({
      url: BASE_URL + url,
      method,
      data,
      header: { 'Content-Type': 'application/json' },
      success: (res: any) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${JSON.stringify(res.data)}`))
        }
      },
      fail: (err: any) => reject(new Error(err.errMsg || 'Network error')),
    })
  })
}

export const api = {
  generateQuiz: (topic: string, questionCount = 5) =>
    request('/api/quiz/generate', 'POST', { topic, question_count: questionCount }),

  submitAnswer: (sessionId: number, questionId: number, userAnswer: string[]) =>
    request('/api/quiz/answer', 'POST', {
      session_id: sessionId,
      question_id: questionId,
      user_answer: userAnswer,
    }),

  getReport: (sessionId: number) =>
    request('/api/quiz/report', 'POST', { session_id: sessionId }),

  getSessions: () =>
    request('/api/quiz/sessions', 'GET'),
}
