<script setup>
import { useRouter } from 'vue-router'
import { Bot, Database, FileSearch, GitBranch, LogIn, ShieldCheck } from 'lucide-vue-next'

import UserInfoComponent from '@/components/UserInfoComponent.vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

function enterAudit() {
  if (!userStore.isLoggedIn) {
    sessionStorage.setItem('redirect', '/audit')
    router.push('/login')
    return
  }
  router.push('/audit')
}
</script>

<template>
  <main class="audit-home">
    <header class="home-header">
      <div class="brand">
        <FileSearch :size="24" />
        <span>交通稽核智能体</span>
      </div>
      <UserInfoComponent :show-button="true" />
    </header>

    <section class="hero-card">
      <a-tag color="blue">一期演示版</a-tag>
      <h1>交通稽核工作台</h1>
      <p>
        面向收费稽核场景，保留问答、知识库和知识图谱能力，同时提供样例数据导入、路径还原、案例分析、异常证据和报告草稿生成。
        业务事实由确定性规则计算，知识能力负责依据检索和辅助解释。
      </p>
      <div class="actions">
        <a-button type="primary" size="large" @click="enterAudit">
          <FileSearch :size="18" />
          进入交通稽核
        </a-button>
        <a-button v-if="!userStore.isLoggedIn" size="large" @click="router.push('/login')">
          <LogIn :size="18" />
          登录
        </a-button>
        <a-button v-else size="large" @click="router.push('/agent')">
          <Bot :size="18" />
          问答
        </a-button>
      </div>
    </section>

    <section class="feature-grid">
      <a-card>
        <template #title>路径还原</template>
        <p>按入口、门架、出口事件生成时间线和示意地图，保留源文件、行号和记录 ID。</p>
      </a-card>
      <a-card>
        <template #title>案例分析</template>
        <p>汇总通行特征、风险类型和相似案例摘要，辅助稽核人员快速判断。</p>
      </a-card>
      <a-card>
        <template #title>报告草稿</template>
        <p>根据结构化证据生成 Markdown 草稿，未经人工确认不得作为正式结论。</p>
      </a-card>
      <a-card>
        <template #title>
          <span class="card-title"><Database :size="18" /> 知识库</span>
        </template>
        <p>用于管理政策制度、稽核规则和历史案例，为报告依据和问答提供来源。</p>
      </a-card>
      <a-card>
        <template #title>
          <span class="card-title"><GitBranch :size="18" /> 知识图谱</span>
        </template>
        <p>保留规则、异常类型、证据项和案例之间的结构关系，不处理原始业务流水。</p>
      </a-card>
      <a-card>
        <template #title>
          <span class="card-title"><Bot :size="18" /> 问答</span>
        </template>
        <p>面向稽核人员的政策解释、案例追问和报告说明入口，不自动生成正式结论。</p>
      </a-card>
    </section>

    <section class="boundary-card">
      <ShieldCheck :size="20" />
      <span>业务流水不进入 RAG 或图谱；Dify/LLM 仅用于草稿和解释，不自动定案。</span>
    </section>
  </main>
</template>

<style lang="less" scoped>
.audit-home {
  min-height: 100vh;
  padding: 28px 36px 48px;
  color: var(--gray-900);
  background: linear-gradient(135deg, var(--main-30), var(--gray-10));
}

.home-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1080px;
  margin: 0 auto 48px;
}

.brand {
  display: flex;
  gap: 10px;
  align-items: center;
  color: var(--main-700);
  font-size: 18px;
  font-weight: 700;
}

.hero-card {
  max-width: 1080px;
  padding: 44px;
  margin: 0 auto 22px;
  border: 1px solid var(--gray-200);
  border-radius: 16px;
  background: var(--main-0);
}

.hero-card h1 {
  margin: 16px 0 12px;
  font-size: 36px;
}

.hero-card p {
  max-width: 760px;
  margin: 0;
  color: var(--gray-600);
  font-size: 16px;
  line-height: 1.8;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 28px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  max-width: 1080px;
  margin: 0 auto 18px;
}

.feature-grid p {
  margin: 0;
  color: var(--gray-600);
  line-height: 1.7;
}

.card-title {
  display: inline-flex;
  gap: 8px;
  align-items: center;
}

.boundary-card {
  display: flex;
  gap: 10px;
  align-items: center;
  max-width: 1080px;
  padding: 16px 18px;
  margin: 0 auto;
  border: 1px solid var(--main-100);
  border-radius: 10px;
  background: var(--main-10);
  color: var(--main-800);
}

@media (max-width: 820px) {
  .audit-home {
    padding: 20px;
  }

  .hero-card {
    padding: 28px;
  }

  .hero-card h1 {
    font-size: 28px;
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }
}
</style>
