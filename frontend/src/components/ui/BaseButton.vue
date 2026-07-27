<script setup lang="ts">
import type { ButtonVariant, ButtonSize } from '@/types/ui'

withDefaults(
  defineProps<{
    variant?: ButtonVariant
    size?: ButtonSize
    block?: boolean
    disabled?: boolean
    type?: 'button' | 'submit'
  }>(),
  { variant: 'primary', size: 'md', block: false, disabled: false, type: 'button' },
)
</script>

<template>
  <button
    :type="type"
    :disabled="disabled"
    class="inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green/60 focus-visible:ring-offset-2 focus-visible:ring-offset-paper disabled:cursor-not-allowed disabled:opacity-50"
    :class="[
      size === 'sm' ? 'px-3 py-1.5 text-xs' : 'px-4 py-2.5 text-sm',
      block && 'w-full',
      variant === 'primary' && 'bg-green text-white shadow-green hover:brightness-105 active:brightness-95',
      variant === 'secondary' && 'border border-border-strong bg-paper text-ink-2 hover:border-ink-3 hover:text-ink',
      variant === 'ghost' && 'text-ink-2 hover:bg-green-ghost hover:text-ink',
      variant === 'ai' && 'border border-green-line bg-green-soft text-green-deep hover:bg-green-wash',
      variant === 'danger' && 'bg-danger-soft text-danger hover:brightness-105',
    ]"
  >
    <slot />
  </button>
</template>
