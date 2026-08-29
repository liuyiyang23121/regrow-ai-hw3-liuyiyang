<template>
  <header class="topbar">
    <p>AI 高价值用户智能召回实验室</p>
    <div class="topbar-actions">
      <span class="topbar-date"><CalendarBlank :size="17" /> 2026-08-24</span>
      <button type="button" aria-label="帮助文档"><Question :size="18" /> <span>帮助文档</span></button>
      <button type="button" aria-label="通知"><Bell :size="18" /></button>
      <button type="button" class="topbar-account" aria-label="账户菜单">张 <CaretDown :size="13" /></button>
    </div>
  </header>
</template>

<script setup>
import {
  PhBell as Bell,
  PhCalendarBlank as CalendarBlank,
  PhCaretDown as CaretDown,
  PhQuestion as Question,
} from '@phosphor-icons/vue';
</script>
