<script setup lang="ts">
defineProps<{ title?: string }>()
</script>

<template>
  <div class="rounded-2xl border border-border bg-paper p-5 shadow-card">
    <div
      v-if="title || $slots.header || $slots.actions"
      class="mb-4 flex items-center justify-between gap-3"
    >
      <slot name="header">
        <h3 class="font-display text-base font-bold text-ink">{{ title }}</h3>
      </slot>
      <div v-if="$slots.actions" class="shrink-0"><slot name="actions" /></div>
    </div>
    <slot />
  </div>
</template>
