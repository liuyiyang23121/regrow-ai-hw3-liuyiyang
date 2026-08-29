<template>
  <main class="section-page knowledge-page">
    <header class="section-page-header">
      <div>
        <div class="section-eyebrow"><Books :size="16" /> 当前任务使用</div>
        <h1>营销知识库</h1>
        <p>这里是各个 Agent 共用的数据表、指标定义和安全规则。修改后，后续任务会读取新版本。</p>
      </div>
      <div class="knowledge-health"><CheckCircle :size="19" weight="fill" /><div><strong>当前版本可用</strong><span>{{ totalEntries }} 条规则已加载</span></div></div>
    </header>

    <section class="section-stat-grid" aria-label="知识库摘要">
      <article><Database :size="22" /><div><span>可查询数据表</span><strong>3</strong></div><small>3 张表可用于取数</small></article>
      <article><Target :size="22" /><div><span>指标定义</span><strong>3</strong></div><small>当前任务读取 3 项</small></article>
      <article><ShieldCheck :size="22" /><div><span>安全规则</span><strong>6</strong></div><small>任务前后都会检查</small></article>
      <article><ClockCounterClockwise :size="22" /><div><span>知识版本</span><strong>v1.4</strong></div><small>2026-08-24 更新</small></article>
    </section>

    <section class="knowledge-shell">
      <aside class="knowledge-nav" aria-label="知识分类">
        <div class="knowledge-search"><MagnifyingGlass :size="16" /><input v-model="query" aria-label="搜索知识" placeholder="搜索表、字段或规则" /></div>
        <button v-for="category in categories" :key="category.id" type="button" :class="{ active: activeCategory === category.id }" @click="activeCategory = category.id">
          <span>{{ category.name }}</span><small>{{ category.entries.length }}</small>
        </button>
      </aside>

      <div class="knowledge-content">
        <header>
          <div><h2>{{ selectedCategory?.name || '知识条目' }}</h2><p>{{ selectedCategory?.description }}</p></div>
          <span class="source-label"><LinkSimple :size="14" /> SQL Agent 正在使用</span>
        </header>
        <div class="knowledge-table" role="table">
          <div class="knowledge-row knowledge-head" role="row"><span>知识条目</span><span>内容</span><span>状态</span></div>
          <div v-for="entry in filteredEntries" :key="entry.title" class="knowledge-row" role="row">
            <div><strong>{{ entry.title }}</strong><small>{{ entry.type }}</small></div>
            <p>{{ entry.summary }}</p>
            <span class="knowledge-status"><Check :size="14" /> {{ entry.status }}</span>
          </div>
          <div v-if="!filteredEntries.length" class="knowledge-empty">没有匹配的知识条目</div>
        </div>
        <footer class="knowledge-footnote"><Info :size="15" /> 当前任务读取了数据字典、30 天复购率定义、只读 SQL 规则和 50,000 人审核阈值。</footer>
      </div>
    </section>
  </main>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import {
  PhBooks as Books, PhCheck as Check, PhCheckCircle as CheckCircle, PhClockCounterClockwise as ClockCounterClockwise,
  PhDatabase as Database, PhInfo as Info, PhLinkSimple as LinkSimple, PhMagnifyingGlass as MagnifyingGlass,
  PhShieldCheck as ShieldCheck, PhTarget as Target,
} from '@phosphor-icons/vue';

const props = defineProps({ categories: { type: Array, default: () => [] } });
const activeCategory = ref('schema');
const query = ref('');
const totalEntries = computed(() => props.categories.reduce((sum, item) => sum + item.entries.length, 0));
const selectedCategory = computed(() => props.categories.find((item) => item.id === activeCategory.value) || props.categories[0]);
const filteredEntries = computed(() => {
  const entries = selectedCategory.value?.entries || [];
  const keyword = query.value.trim().toLowerCase();
  if (!keyword) return entries;
  return entries.filter((entry) => `${entry.title} ${entry.type} ${entry.summary}`.toLowerCase().includes(keyword));
});
watch(() => props.categories, (value) => { if (value.length && !value.some((item) => item.id === activeCategory.value)) activeCategory.value = value[0].id; }, { immediate: true });
</script>
