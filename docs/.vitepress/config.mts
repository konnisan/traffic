import { defineConfig } from 'vitepress'
import markdownItTaskCheckbox from 'markdown-it-task-checkbox'

export default defineConfig({
  lang: 'zh-CN',
  title: 'Yuxi-Know',
  description: '语析',
  base: '/Yuxi-Know/',
  srcDir: './',
  ignoreDeadLinks: [/localhost/],
  markdown: {
    config: (md) => {
      md.use(markdownItTaskCheckbox)
    }
  },
  themeConfig: {
    logo: '/favicon.svg',
    nav: [
      {
        text: 'Version',
        items: [
          { text: 'Latest (开发版)', link: '/latest/intro/quick-start' },
          { text: 'v0.4.0 (稳定版)', link: '/v0.4.0/intro/quick-start' }
        ]
      }
    ],
    sidebar: {
      '/latest/': [
        {
          text: '简介',
          items: [
            { text: '什么是 Yuxi-Know？', link: '/latest/intro/project-overview' },
            { text: '快速开始', link: '/latest/intro/quick-start' },
            { text: '模型配置', link: '/latest/intro/model-config' },
            { text: '知识库与知识图谱', link: '/latest/intro/knowledge-base' },
            { text: 'RAG 分层与视觉检索', link: '/latest/intro/rag-graph-visual-rag' },
            { text: '知识库评估', link: '/latest/intro/evaluation' }
          ]
        },
        {
          text: '智能体开发',
          items: [
            { text: '智能体配置', link: '/latest/agents/agents-config' },
            { text: '上下文配置', link: '/latest/agents/context-config' },
            { text: '工具系统', link: '/latest/agents/tools-system' },
            { text: '交通稽核智能体', link: '/latest/agents/traffic-audit' },
            { text: '中间件', link: '/latest/agents/middleware' },
            { text: 'MCP 集成', link: '/latest/agents/mcp-integration' },
            { text: 'Skills 管理', link: '/latest/agents/skills-management' }
          ]
        },
        {
          text: '交通稽核轻量化方案',
          items: [
            { text: '总体架构设计', link: '/latest/traffic-audit/architecture' },
            { text: '业务闭环设计', link: '/latest/traffic-audit/business-loop' },
            { text: '轻量组件工作流核心', link: '/latest/traffic-audit/lightweight-workflow-core' },
            { text: 'Dify 工作流接入', link: '/latest/traffic-audit/dify-workflow' },
            { text: 'Dify 工作流模板', link: '/latest/traffic-audit/dify-workflows' },
            { text: 'RAG 与知识边界', link: '/latest/traffic-audit/rag-boundary' }
          ]
        },
        {
          text: '高级配置',
          items: [
            { text: '配置系统详解', link: '/latest/advanced/configuration' },
            { text: '文档解析', link: '/latest/advanced/document-processing' },
            { text: '品牌自定义', link: '/latest/advanced/branding' },
            { text: '其他配置', link: '/latest/advanced/misc' },
            { text: '生产部署', link: '/latest/advanced/deployment' }
          ]
        },
        {
          text: '更新日志',
          items: [
            { text: '路线图', link: '/latest/changelog/roadmap' },
            { text: '参与贡献', link: '/latest/changelog/contributing' },
            { text: '常见问题', link: '/latest/changelog/faq' },
            { text: '迁移至 v0.5', link: '/latest/changelog/migrate_to_v0-5' }
          ]
        }
      ],
      '/v0.4.0/': [
        {
          text: '简介',
          items: [
            { text: '什么是 Yuxi-Know？', link: '/v0.4.0/intro/project-overview' },
            { text: '快速开始', link: '/v0.4.0/intro/quick-start' },
            { text: '模型配置', link: '/v0.4.0/intro/model-config' },
            { text: '知识库与知识图谱', link: '/v0.4.0/intro/knowledge-base' },
            { text: '知识库评估', link: '/v0.4.0/intro/evaluation' }
          ]
        },
        {
          text: '高级配置',
          items: [
            { text: '配置系统详解', link: '/v0.4.0/advanced/configuration' },
            { text: '文档解析', link: '/v0.4.0/advanced/document-processing' },
            { text: '智能体', link: '/v0.4.0/advanced/agents-config' },
            { text: '品牌自定义', link: '/v0.4.0/advanced/branding' },
            { text: '其他配置', link: '/v0.4.0/advanced/misc' },
            { text: '生产部署', link: '/v0.4.0/advanced/deployment' }
          ]
        }
      ]
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/xerrors/Yuxi-Know' }
    ],
    footer: {
      message: '本项目基于 MIT License 开源，欢迎使用和贡献。',
      copyright: 'Copyright © 2025-present Yuxi'
    },
    editLink: {
      pattern: 'https://github.com/xerrors/Yuxi-Know/edit/main/docs/:path',
      text: '在 GitHub 上编辑此页'
    },
    lastUpdated: {
      text: '最后更新时间',
      formatOptions: {
        dateStyle: 'full',
        timeStyle: 'medium'
      }
    },
    search: {
      provider: 'local'
    },
    docFooter: {
      prev: '上一页',
      next: '下一页'
    }
  }
})
