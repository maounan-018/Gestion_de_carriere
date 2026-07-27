<script setup lang="ts">
import { watch, onUnmounted } from 'vue'
import { X } from 'lucide-vue-next'

const props = defineProps<{ modelValue: boolean; title?: string }>()
const emit = defineEmits<{ 'update:modelValue': [boolean] }>()

function close() {
  emit('update:modelValue', false)
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) document.addEventListener('keydown', onKey)
    else document.removeEventListener('keydown', onKey)
  },
)
onUnmounted(() => document.removeEventListener('keydown', onKey))
</script>

<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="modal-in fixed inset-0 z-50 grid place-items-center bg-ink/40 p-4 backdrop-blur-sm"
      @click.self="close"
    >
        <div
          class="w-full max-w-lg rounded-2xl border border-border bg-paper shadow-float"
          role="dialog"
          aria-modal="true"
        >
          <div
            v-if="title || $slots.header"
            class="flex items-center justify-between gap-3 border-b border-border px-5 py-4"
          >
            <slot name="header">
              <h3 class="font-display text-lg font-bold text-ink">{{ title }}</h3>
            </slot>
            <button
              class="grid h-8 w-8 place-items-center rounded-lg text-ink-3 hover:bg-panel-2 hover:text-ink"
              aria-label="Fermer"
              @click="close"
            >
              <X :size="18" />
            </button>
          </div>
          <div class="px-5 py-4"><slot /></div>
          <div
            v-if="$slots.footer"
            class="flex justify-end gap-2 border-t border-border px-5 py-4"
          >
            <slot name="footer" />
          </div>
        </div>
      </div>
  </Teleport>
</template>

<style scoped>
.modal-in {
  animation: modalIn 0.18s ease-out;
}
@keyframes modalIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@media (prefers-reduced-motion: reduce) {
  .modal-in {
    animation: none;
  }
}
</style>
