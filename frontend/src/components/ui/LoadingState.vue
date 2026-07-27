<script setup lang="ts">
defineProps<{ label?: string }>()
</script>

<template>
  <div
    class="flex flex-col items-center justify-center gap-3 py-12 text-ink-3"
    role="status"
    aria-live="polite"
  >
    <span
      class="h-8 w-8 animate-spin rounded-full border-[3px] border-green-line border-t-green"
      aria-hidden="true"
    />
    <span class="text-sm">{{ label || 'Chargement…' }}</span>
  </div>
</template>
