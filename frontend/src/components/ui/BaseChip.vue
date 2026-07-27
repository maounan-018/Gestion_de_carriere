<script setup lang="ts">
defineProps<{ tone?: 'default' | 'green' | 'gap' | 'add' }>()
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-semibold"
    :class="{
      'border border-border bg-panel-2 text-ink-2': !tone || tone === 'default',
      'border border-green-line bg-green-soft text-green-deep': tone === 'green',
      'bg-danger-soft text-danger': tone === 'gap',
      'cursor-pointer border border-dashed border-green-line text-green-deep hover:bg-green-ghost':
        tone === 'add',
    }"
  >
    <slot />
  </span>
</template>
