<script setup lang="ts">
defineProps<{ width?: string; height?: string; rounded?: string }>()
</script>

<template>
  <span
    class="shimmer relative block overflow-hidden bg-panel-2"
    :class="rounded || 'rounded-lg'"
    :style="{ width: width || '100%', height: height || '1rem' }"
    aria-hidden="true"
  />
</template>

<style scoped>
.shimmer::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgb(255 255 255 / 0.65), transparent);
  transform: translateX(-100%);
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}
@media (prefers-reduced-motion: reduce) {
  .shimmer::after {
    animation: none;
  }
}
</style>
