<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { LayoutGrid } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import type { CartoMatrix, FamilleTension } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import Heatmap from '@/components/shared/Heatmap.vue'

const router = useRouter()
const carto = ref<CartoMatrix>({ familles: [], lignes: [] })
const familles = ref<FamilleTension[]>([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    carto.value = await apiService.getCarto()
    // Tensions par famille : best-effort (n'empêche pas l'affichage de la heatmap).
    apiService.getFamilles().then((f) => { familles.value = f }).catch(() => { familles.value = [] })
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

// Échelle commune des barres (max des couvertures et demandes).
const famMax = computed(() =>
  Math.max(1, ...familles.value.flatMap((f) => [f.profilsCouverts, f.demande])),
)
const pct = (v: number) => Math.round((v / famMax.value) * 100)
const tone = (t: FamilleTension['tension']) =>
  t === 'forte' ? 'hot' : t === 'moyenne' ? 'warn' : 'ok'
</script>

<template>
  <div class="space-y-5">
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
        <Heatmap :familles="carto.familles" :lignes="carto.lignes" @pole="goPole" />
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

    <!-- Panneau complémentaire : tensions par famille (offre interne vs demande). -->
    <BaseCard v-if="!loading && !error && familles.length" title="Tensions par famille de compétences">
      <p class="mb-3.5 text-xs text-ink-3">
        Offre interne <b class="text-ink-2">détenue</b> (collaborateurs qui possèdent la famille) vs
        <b class="text-ink-2">demande</b> des offres ouvertes. La tension monte quand la demande dépasse
        la couverture interne.
      </p>
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="f in familles" :key="f.famille" class="rounded-xl border border-border bg-panel p-3.5">
          <div class="mb-3 flex items-center justify-between gap-2">
            <span class="text-sm font-bold text-ink">{{ f.famille }}</span>
            <BasePill :tone="tone(f.tension)">tension {{ f.tension }}</BasePill>
          </div>
          <div class="mb-2 flex items-center gap-2">
            <span class="w-16 shrink-0 text-[11px] text-ink-3">détenu</span>
            <div class="h-2 flex-1 overflow-hidden rounded-full bg-panel-2">
              <div class="h-full rounded-full bg-green" :style="{ width: pct(f.profilsCouverts) + '%' }" />
            </div>
            <span class="w-20 shrink-0 text-right text-[11px] text-ink-2">{{ f.profilsCouverts }} profils</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-16 shrink-0 text-[11px] text-ink-3">demandé</span>
            <div class="h-2 flex-1 overflow-hidden rounded-full bg-panel-2">
              <div class="h-full rounded-full bg-green-deep" :style="{ width: pct(f.demande) + '%' }" />
            </div>
            <span class="w-20 shrink-0 text-right text-[11px] text-ink-2">{{ f.demande }} attendus</span>
          </div>
          <p class="mt-2.5 text-[11px] text-ink-3">
            Niveau moyen {{ f.niveauMoyen ?? '—' }} · {{ f.detenues }} compétences détenues
          </p>
        </div>
      </div>
    </BaseCard>
  </div>
</template>
