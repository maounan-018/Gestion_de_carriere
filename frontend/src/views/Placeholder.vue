<script setup lang="ts">
import { useRoute } from 'vue-router'
import { Hammer } from 'lucide-vue-next'
import EmptyState from '@/components/ui/EmptyState.vue'

const route = useRoute()
</script>

<template>
  <EmptyState
    :icon="Hammer"
    :title="(route.meta.title as string) || 'Écran'"
    text="Écran en construction — il sera implémenté dans un prochain jalon (M2–M5). La coquille (shell + design system) est déjà en place autour de lui."
  />
</template>
