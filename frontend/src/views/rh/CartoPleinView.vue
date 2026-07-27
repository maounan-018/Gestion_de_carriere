<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiService } from '@/services/apiService'
import type { CartoPole } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import Heatmap from '@/components/shared/Heatmap.vue'

const router = useRouter()
const carto = ref<CartoPole[]>([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    carto.value = await apiService.getCarto()
  } catch {
    error.value = 'Impossible de charger la cartographie.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

function goPole(name: string) {
  router.push({ name: 'rh.cartoDetail', params: { pole: name } })
}
</script>

<template>
  <div>
    <BaseBreadcrumb
      :items="[{ label: 'Cartographie', to: { name: 'rh.cartographie' } }, { label: 'Vue plein écran' }]"
    />
    <BaseCard title="Cartographie · vue plein écran">
      <template #actions>
        <RouterLink :to="{ name: 'rh.cartographie' }">
          <BaseButton size="sm" variant="secondary">Vue synthétique</BaseButton>
        </RouterLink>
      </template>
      <LoadingState v-if="loading" label="Chargement…" />
      <ErrorState v-else-if="error" :message="error">
        <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
      </ErrorState>
      <Heatmap v-else :poles="carto" big @pole="goPole" />
    </BaseCard>
  </div>
</template>
