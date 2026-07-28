<script setup lang="ts">
import { Check, Info, TriangleAlert } from '@lucide/vue'
import { useToast } from '@/composables/useToast'
import type { ToastTone } from '@/types/ui'

const { items } = useToast()
const icons: Record<ToastTone, typeof Check> = { ok: Check, info: Info, error: TriangleAlert }
</script>

<template>
  <Teleport to="body">
    <div class="fixed bottom-5 right-5 z-[60] flex flex-col items-end gap-2">
      <TransitionGroup name="toast">
        <div
          v-for="t in items"
          :key="t.id"
          class="flex items-center gap-2 rounded-xl border border-border bg-paper px-4 py-2.5 text-sm font-medium shadow-float"
          :class="{
            'text-green-deep': t.tone === 'ok',
            'text-ink-2': t.tone === 'info',
            'text-danger': t.tone === 'error',
          }"
        >
          <component :is="icons[t.tone]" :size="16" />
          <span>{{ t.message }}</span>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
