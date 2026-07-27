<script setup lang="ts">
import type { Component } from 'vue'
import { Inbox } from 'lucide-vue-next'

defineProps<{ icon?: Component; title: string; text?: string }>()
</script>

<template>
  <div
    class="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border-strong bg-panel px-6 py-12 text-center"
  >
    <div class="mb-3 grid h-12 w-12 place-items-center rounded-full bg-green-soft text-green-deep">
      <component :is="icon || Inbox" :size="22" />
    </div>
    <h4 class="font-display text-base font-bold text-ink">{{ title }}</h4>
    <p v-if="text" class="mt-1 max-w-sm text-sm text-ink-3">{{ text }}</p>
    <div v-if="$slots.action" class="mt-4"><slot name="action" /></div>
  </div>
</template>
