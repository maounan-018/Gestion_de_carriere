<script setup lang="ts">
defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [boolean] }>()
</script>

<template>
  <button
    type="button"
    role="switch"
    :aria-checked="modelValue"
    class="relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green/60 focus-visible:ring-offset-2 focus-visible:ring-offset-paper"
    :class="modelValue ? 'bg-green' : 'border border-border bg-panel-2'"
    @click="emit('update:modelValue', !modelValue)"
  >
    <span
      class="inline-block h-[18px] w-[18px] rounded-full bg-white shadow transition"
      :class="modelValue ? 'translate-x-[23px]' : 'translate-x-[3px]'"
    />
  </button>
</template>
