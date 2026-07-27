<script setup lang="ts">
import { TriangleAlert } from 'lucide-vue-next'

defineProps<{ title?: string; message: string }>()
</script>

<template>
  <div
    class="flex flex-col items-center justify-center rounded-2xl border border-danger/30 bg-danger-soft/50 px-6 py-10 text-center"
    role="alert"
  >
    <div class="mb-3 grid h-12 w-12 place-items-center rounded-full bg-danger-soft text-danger">
      <TriangleAlert :size="22" />
    </div>
    <h4 class="font-display text-base font-bold text-ink">{{ title || 'Une erreur est survenue' }}</h4>
    <p class="mt-1 max-w-sm text-sm text-ink-2">{{ message }}</p>
    <div v-if="$slots.action" class="mt-4"><slot name="action" /></div>
  </div>
</template>
