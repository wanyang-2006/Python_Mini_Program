import { create } from 'zustand'

export interface Question {
  id: number         // 后端数据库的 Question.id（答题接口需要）
  apiId: string      // AI 给出的 id（q1, q2...）
  content: string
  options: string[]        // ['A. xxx', 'B. yyy', ...]
  optionKeys: string[]     // ['A', 'B', 'C', 'D']
  correctAnswer: string    // 客户端不再存正确答案（由后端校验）
  explanation: string
  tags: string[]
}

export interface AnswerRecord {
  questionId: number       // DB id
  userAnswer: string
  correctAnswer: string    // 后端返回
  isCorrect: boolean
  explanation: string
}

interface QuizState {
  topic: string
  sessionId: number | null   // 后端返回的 session id
  questions: Question[]
  currentIndex: number
  answers: AnswerRecord[]
  // actions
  setTopic: (topic: string) => void
  initSession: (sessionId: number, questions: Question[]) => void
  submitAnswer: (record: AnswerRecord) => void
  nextQuestion: () => void
  reset: () => void
}

export const useQuizStore = create<QuizState>((set) => ({
  topic: '',
  sessionId: null,
  questions: [],
  currentIndex: 0,
  answers: [],

  setTopic: (topic) => set({ topic }),

  initSession: (sessionId, questions) =>
    set({ sessionId, questions, currentIndex: 0, answers: [] }),

  submitAnswer: (record) =>
    set((s) => ({ answers: [...s.answers, record] })),

  nextQuestion: () =>
    set((s) => ({ currentIndex: s.currentIndex + 1 })),

  reset: () =>
    set({ topic: '', sessionId: null, questions: [], currentIndex: 0, answers: [] })
}))

// ---- Mock 题库（Phase 5 前端联调期保留，正式环境由 API 替代） ----
export const MOCK_QUESTIONS: Question[] = [
  {
    id: 1,
    apiId: 'q1',
    content: '以下哪个是 Python 合法的变量名？',
    options: ['A. _my_var', 'B. 1abc', 'C. my-var', 'D. class'],
    optionKeys: ['A', 'B', 'C', 'D'],
    correctAnswer: 'A',
    explanation: 'Python 变量名须以字母或下划线开头，不能用数字开头，不能含连字符，也不能是保留字。_my_var 完全合法。',
    tags: ['变量命名']
  },
  {
    id: 2,
    apiId: 'q2',
    content: 'Python 中用来输出内容到控制台的内置函数是？',
    options: ['A. echo()', 'B. console.log()', 'C. print()', 'D. log()'],
    optionKeys: ['A', 'B', 'C', 'D'],
    correctAnswer: 'C',
    explanation: 'Python 使用内置函数 print() 输出内容。echo 是 PHP/Bash 语法，console.log 是 JavaScript 语法。',
    tags: ['内置函数']
  },
  {
    id: 3,
    apiId: 'q3',
    content: '下列哪种数据类型在 Python 中是不可变的？',
    options: ['A. list', 'B. dict', 'C. set', 'D. tuple'],
    optionKeys: ['A', 'B', 'C', 'D'],
    correctAnswer: 'D',
    explanation: 'tuple（元组）创建后不能修改元素，是不可变序列。list、dict、set 都是可变的。',
    tags: ['数据类型', '不可变']
  },
  {
    id: 4,
    apiId: 'q4',
    content: 'Python 中 // 运算符的作用是什么？',
    options: ['A. 普通除法', 'B. 整除（向下取整）', 'C. 注释', 'D. 幂运算'],
    optionKeys: ['A', 'B', 'C', 'D'],
    correctAnswer: 'B',
    explanation: '// 是整除运算符，结果向下取整。/ 是普通除法，** 是幂运算，# 是注释。',
    tags: ['运算符']
  },
  {
    id: 5,
    apiId: 'q5',
    content: 'Python 中用于定义函数的关键字是？',
    options: ['A. func', 'B. function', 'C. def', 'D. define'],
    optionKeys: ['A', 'B', 'C', 'D'],
    correctAnswer: 'C',
    explanation: 'Python 使用 def 关键字定义函数。func 和 function 是其他语言的用法，define 不是 Python 关键字。',
    tags: ['函数定义']
  }
]

