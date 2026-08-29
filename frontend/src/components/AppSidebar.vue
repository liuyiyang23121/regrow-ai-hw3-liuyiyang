<template>
  <aside class="sidebar">
    <div class="brand">
      <img src="/regrow-mark.png" alt="" class="brand-mark" />
      <span>ReGrow</span>
    </div>

    <nav class="sidebar-nav" aria-label="主导航">
      <button
        v-for="item in items"
        :key="item.id"
        type="button"
        :class="['nav-item', { active: activeSection === item.id }]"
        @click="$emit('navigate', item.id)"
      >
        <component :is="item.icon" :size="20" weight="regular" />
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <div class="sidebar-user">
      <div class="avatar">张</div>
      <div>
        <strong>CRM 运营</strong>
        <span>运营团队</span>
      </div>
      <CaretDown :size="14" />
    </div>
  </aside>
</template>

<script setup>
import { markRaw } from 'vue';
import {
  PhCaretDown as CaretDown,
  PhFlask as Flask,
  PhFolderSimple as FolderSimple,
  PhNotebook as Notebook,
} from '@phosphor-icons/vue';

defineProps({ activeSection: { type: String, required: true } });
defineEmits(['navigate']);

const items = [
  { id: 'tasks', label: '任务', icon: markRaw(FolderSimple) },
  { id: 'knowledge', label: '知识库', icon: markRaw(Notebook) },
  { id: 'tests', label: '测试', icon: markRaw(Flask) },
];
</script>
