<script setup lang="ts">
// Auto-entretien annuel du RH : moteur co-pilote partagé (persona = session).
import GuidedInterview from '@/components/shared/GuidedInterview.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'

const crumbs = [
  { label: 'Mon espace', to: { name: 'rh.espace' } },
  { label: 'Mon entretien annuel' },
]
</script>

<template>
  <div>
    <BaseBreadcrumb :items="crumbs" />
    <GuidedInterview />
  </div>
</template>
