<script setup lang="ts">
import { ChevronRight } from 'lucide-vue-next'
import type { CrumbItem } from '@/types/ui'

defineProps<{ items: CrumbItem[] }>()
</script>

<template>
  <nav class="mb-4 flex flex-wrap items-center gap-1.5 text-xs text-ink-3" aria-label="Fil d'ariane">
    <template v-for="(it, i) in items" :key="i">
      <ChevronRight v-if="i" :size="13" class="opacity-60" />
      <router-link
        v-if="it.to && i < items.length - 1"
        :to="it.to"
        class="font-medium hover:text-green-deep"
      >
        {{ it.label }}
      </router-link>
      <span v-else class="font-semibold text-ink-2" aria-current="page">{{ it.label }}</span>
    </template>
  </nav>
</template>
