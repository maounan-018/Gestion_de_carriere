<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { LayoutGrid } from 'lucide-vue-next'
import { apiService } from '@/services/apiService'
import type { CartoPole } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
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

const legend: [string, string][] = [
  ['Aucune donnée', 'bg-heat-0'],
  ['Émergent (1·2)', 'bg-heat-1'],
  ['Avancé (3)', 'bg-heat-2'],
  ['Confirmé (4)', 'bg-heat-3'],
  ['Expert (5)', 'bg-heat-4'],
]
</script>

<template>
  <BaseCard title="Cartographie des compétences par pôle">
    <template #actions>
      <RouterLink :to="{ name: 'rh.cartoPlein' }">
        <BaseButton size="sm" variant="secondary"><LayoutGrid :size="15" /> Voir en grand</BaseButton>
      </RouterLink>
    </template>

    <LoadingState v-if="loading" label="Chargement de la cartographie…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <template v-else>
      <p class="mb-3 text-xs text-ink-3">
        Lignes = pôles · colonnes = familles de compétences · le chiffre indique le niveau moyen
        (1→5). Cliquez un pôle pour son analyse détaillée.
      </p>
      <Heatmap :poles="carto" @pole="goPole" />
      <div class="mt-4 flex flex-wrap gap-3">
        <span
          v-for="[label, cl] in legend"
          :key="label"
          class="inline-flex items-center gap-1.5 text-[11px] text-ink-3"
        >
          <i class="h-3.5 w-3.5 rounded" :class="cl" /> {{ label }}
        </span>
      </div>
    </template>
  </BaseCard>
</template>
