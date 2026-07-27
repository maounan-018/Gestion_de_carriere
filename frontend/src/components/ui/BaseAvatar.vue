<script setup lang="ts">
defineProps<{ initials: string; size?: 'sm' | 'md' | 'xl'; photo?: string }>()
</script>

<template>
  <div
    class="grid shrink-0 place-items-center overflow-hidden rounded-full bg-green-soft bg-cover bg-center font-bold text-green-deep shadow-card ring-2 ring-white"
    :class="{
      'h-8 w-8 text-xs': !size || size === 'sm',
      'h-11 w-11 text-sm': size === 'md',
      'h-16 w-16 text-lg': size === 'xl',
    }"
    :style="photo ? { backgroundImage: `url(${photo})`, color: 'transparent' } : undefined"
  >
    {{ initials }}
  </div>
</template>
