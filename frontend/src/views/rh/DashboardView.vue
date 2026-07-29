<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Sparkles } from '@lucide/vue'
import { useSessionStore } from '@/stores/session'
import { apiService } from '@/services/apiService'
import type { RhKpi, RhAlert, CartoMatrix } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import Heatmap from '@/components/shared/Heatmap.vue'

const session = useSessionStore()
const router = useRouter()
const kpis = ref<RhKpi[]>([])
const alerts = ref<RhAlert[]>([])
const carto = ref<CartoMatrix>({ familles: [], lignes: [] })
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [k, a, c] = await Promise.all([
      apiService.getRhKpis(),
      apiService.getRhAlerts(),
      apiService.getCarto(),
    ])
    kpis.value = k
    alerts.value = a
    carto.value = c
  } catch {
    error.value = 'Impossible de charger le tableau de bord.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const sevTone: Record<string, 'hot' | 'warn' | 'ai'> = { crit: 'hot', warn: 'warn', info: 'ai' }
const sevLabel: Record<string, string> = { crit: 'critique', warn: 'à traiter', info: 'info' }
function goPole(name: string) {
  router.push({ name: 'rh.cartoDetail', params: { pole: name } })
}
</script>

<template>
  <div class="space-y-5">
    <BaseCard>
      <div class="text-xs font-semibold uppercase tracking-wide text-green-deep">
        Espace RH · Groupe BMCI
      </div>
      <h2 class="font-display text-2xl font-bold text-ink">
        Bonjour {{ session.user?.firstName || 'Nadia' }}
      </h2>
      <p class="text-sm text-ink-3">Pilotage des talents · vue consolidée du capital humain</p>
    </BaseCard>

    <LoadingState v-if="loading" label="Chargement du tableau de bord…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <template v-else>
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="k in kpis" :key="k.label" class="rounded-2xl border border-border bg-paper p-4 shadow-card">
          <div class="grid h-9 w-9 place-items-center rounded-lg bg-green-soft text-green-deep">
            <AppIcon :name="k.icon" :size="16" />
          </div>
          <div class="mt-2 font-display text-2xl font-extrabold text-ink">{{ k.value }}</div>
          <div class="text-xs text-ink-3">{{ k.label }}<span v-if="k.hint"> · {{ k.hint }}</span></div>
        </div>
      </div>

      <div class="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
        <BaseCard class="min-w-0" title="Cartographie des compétences par pôle">
          <template #actions>
            <RouterLink :to="{ name: 'rh.cartographie' }" class="text-xs font-semibold text-green-deep hover:underline">Voir en grand</RouterLink>
          </template>
          <Heatmap :familles="carto.familles" :lignes="carto.lignes" @pole="goPole" />
          <p class="mt-3 text-[11px] text-ink-3">
            Le niveau (1→5) est indiqué en chiffre dans chaque case · l'information ne repose pas que
            sur la couleur (accessibilité WCAG). Cliquez un pôle pour son analyse.
          </p>
        </BaseCard>

        <BaseCard title="Alertes & actions">
          <template #actions><BasePill tone="ai"><Sparkles :size="12" /> IA</BasePill></template>
          <div class="space-y-2">
            <RouterLink
              v-for="a in alerts"
              :key="a.id"
              :to="{ name: a.to }"
              class="block rounded-xl border border-border bg-panel p-3 transition hover:border-green-line"
            >
              <div class="flex items-center gap-2">
                <div
                  class="grid h-7 w-7 shrink-0 place-items-center rounded-lg"
                  :class="a.severity === 'crit' ? 'bg-danger-soft text-danger' : a.severity === 'warn' ? 'bg-warning-soft text-warning' : 'bg-green-soft text-green-deep'"
                >
                  <AppIcon :name="a.icon" :size="14" />
                </div>
                <h4 class="text-sm font-bold text-ink">{{ a.title }}</h4>
                <BasePill class="ml-auto" :tone="sevTone[a.severity]">{{ sevLabel[a.severity] }}</BasePill>
              </div>
              <p class="mt-1 text-xs text-ink-2">{{ a.text }}</p>
            </RouterLink>
          </div>
        </BaseCard>
      </div>
    </template>
  </div>
</template>
