<script setup lang="ts">
defineProps<{ tone?: 'new' | 'hot' | 'warn' | 'mut' | 'ai' | 'ok' }>()
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-bold"
    :class="{
      'bg-green-soft text-green-deep': !tone || tone === 'new' || tone === 'ok',
      'bg-danger-soft text-danger': tone === 'hot',
      'bg-warning-soft text-warning': tone === 'warn',
      'bg-panel-2 text-ink-3': tone === 'mut',
      'border border-green-line bg-green-ghost text-green-deep': tone === 'ai',
    }"
  >
    <slot />
  </span>
</template>
