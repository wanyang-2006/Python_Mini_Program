const config = {
  projectName: 'ai-quiz',
  date: '2026-11-12',
  designWidth: 375,
  deviceRatio: {
    640: 2.34 / 2,
    750: 1,
    375: 2,
    828: 1.81 / 2
  },
  sourceRoot: 'src',
  outputRoot: 'dist',
  plugins: [],
  defineConstants: {},
  copy: {
    patterns: [],
    options: {}
  },
  framework: 'react',
  // webpack5 模式，关闭 prebundle（Module Federation 在微信小程序中有异步加载兼容问题）
  compiler: {
    type: 'webpack5',
    prebundle: {
      enable: false
    }
  },
  cache: {
    enable: false
  },
  mini: {
    // zustand 是 ESM 包，让 babel-loader 处理它转为 CJS，避免 Webpack5 TDZ 循环引用
    esnextModules: ['zustand'],
    // 通过 webpackChain alias，强制 Webpack 解析 zustand 时使用 CJS 入口（index.js），
    // 避免走 package.exports 的 "import" 字段（ESM，触发 TDZ）
    // exactMatch:true 确保只替换 'zustand' 本身，不影响 'zustand/vanilla' 等子路径
    webpackChain(chain) {
      const path = require('path')
      const zustandCJS = path.resolve(__dirname, '../node_modules/zustand/index.js')
      chain.resolve.alias
        .set('zustand$', zustandCJS)
    },
    postcss: {
      pxtransform: {
        enable: true,
        config: {
          onePxTransform: false,
          unitPrecision: 5,
          propList: ['*'],
          selectorBlackList: [],
          replace: true,
          mediaQuery: false,
          minPixelValue: 0
        }
      },
      url: { enable: true, config: { limit: 10240 } },
      cssModules: { enable: false }
    }
  },
  h5: {
    publicPath: '/',
    staticDirectory: 'static',
    esnextModules: [],
    postcss: {
      autoprefixer: { enable: true, config: {} },
      cssModules: { enable: false }
    }
  }
}

module.exports = function (merge) {
  if (process.env.NODE_ENV === 'development') {
    return merge({}, config, require('./dev'))
  }
  return merge({}, config, require('./prod'))
}
