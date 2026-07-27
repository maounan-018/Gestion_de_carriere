<script setup lang="ts">
defineProps<{ tone?: 'role' | 'gold' | 'mut' }>()
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-bold"
    :class="{
      'bg-green text-white': !tone || tone === 'role',
      'bg-gold-soft text-gold': tone === 'gold',
      'bg-panel-2 text-ink-3': tone === 'mut',
    }"
  >
    <slot />
  </span>
</template>
