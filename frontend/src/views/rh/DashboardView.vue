<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Sparkles } from '@lucide/vue'
import { useSessionStore } from '@/stores/session'
import { apiService } from '@/services/apiService'
import { kpiAccent } from '@/utils/kpiAccent'
import type { RhKpi, RhAlert, CartoMatrix, SyntheseRh } from '@/types/rh'
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
const synthese = ref<SyntheseRh | null>(null)
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
    // Synthèse consolidée : best-effort (n'empêche pas le reste du dashboard).
    apiService.getSyntheseRh().then((s) => { synthese.value = s }).catch(() => { synthese.value = null })
  } catch {
    error.value = 'Impossible de charger le tableau de bord.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const sevTone: Record<string, 'hot' | 'warn' | 'ai'> = { crit: 'hot', warn: 'warn', info: 'ai' }
const sevLabel: Record<string, string> = { crit: 'critique', warn: 'à traiter', info: 'info' }

const poleMax = computed(() => Math.max(1, ...(synthese.value?.parPole.map((p) => p.effectif) ?? [])))
const poleWidth = (v: number) => Math.round((v / poleMax.value) * 100)
const STATUT_LABEL: Record<string, string> = {
  deposee: 'Déposées', en_evaluation: 'En évaluation', retenue: 'Retenues',
  rejetee: 'Rejetées', retiree: 'Retirées',
}
const statutLabel = (s: string) => STATUT_LABEL[s] ?? s
function goPole(name: string) {
  router.push({ name: 'rh.cartoDetail', params: { pole: name } })
}

// Analyse stratégique IA (G) · à la demande : l'IA lit les indicateurs consolidés.
const analyse = ref('')
const analyseModel = ref('')
const analyseDate = ref('')
const analysing = ref(false)
async function lancerAnalyse() {
  if (analysing.value) return
  analysing.value = true
  try {
    const r = await apiService.lancerAnalyseRh()
    analyse.value = r.synthese
    analyseModel.value = r.model
    analyseDate.value = new Date(r.genere_le).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })
  } catch {
    analyse.value = "L'analyse n'a pas pu être générée. Réessayez dans un moment."
  } finally {
    analysing.value = false
  }
}
</script>

<template>
  <div class="space-y-5">
    <BaseCard>
      <div class="text-xs font-semibold uppercase tracking-wide text-green-deep">
        Espace HRBP · Groupe BMCI
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
        <div v-for="(k, i) in kpis" :key="k.label" class="rounded-2xl border border-border bg-paper p-4 shadow-card">
          <div class="grid h-9 w-9 place-items-center rounded-lg" :class="kpiAccent(i)">
            <AppIcon :name="k.icon" :size="16" />
          </div>
          <div class="mt-2 font-display text-2xl font-extrabold text-ink">{{ k.value }}</div>
          <div class="text-xs text-ink-3">{{ k.label }}<span v-if="k.hint"> · {{ k.hint }}</span></div>
        </div>
      </div>

      <BaseCard>
        <template #header>
          <div class="flex flex-wrap items-center gap-2.5">
            <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green text-white"><Sparkles :size="16" /></div>
            <div class="min-w-0 flex-1">
              <h3 class="font-display text-base font-bold text-ink">Analyse stratégique · IA</h3>
              <p class="text-xs text-ink-3">L'IA locale lit les indicateurs consolidés de la plateforme et en tire une synthèse actionnable.</p>
            </div>
            <BaseButton :disabled="analysing" @click="lancerAnalyse">
              <Sparkles :size="15" /> {{ analysing ? 'Analyse en cours…' : (analyse ? "Relancer l'analyse" : "Lancer l'analyse") }}
            </BaseButton>
          </div>
        </template>
        <div v-if="analysing" class="flex items-center gap-2 py-3 text-sm text-ink-3">
          <Sparkles :size="16" class="animate-pulse text-green-deep" /> L'IA analyse la donnée consolidée · cela peut prendre jusqu'à une minute…
        </div>
        <div v-else-if="analyse">
          <p class="whitespace-pre-line text-sm leading-relaxed text-ink-2">{{ analyse }}</p>
          <p class="mt-3 text-[11px] text-ink-3">Généré le {{ analyseDate }} · modèle {{ analyseModel }} · fondé sur les données réelles de la plateforme.</p>
        </div>
        <p v-else class="py-2 text-sm text-ink-3">
          Cliquez « Lancer l'analyse » pour une synthèse stratégique : tensions de compétences, hauts
          potentiels, signaux de rétention et qualité des données.
        </p>
      </BaseCard>

      <BaseCard v-if="synthese" title="Synthèse HRBP">
        <div class="grid gap-5 sm:grid-cols-2">
          <div class="min-w-0">
            <p class="mb-2 text-xs font-semibold text-ink-2">Effectifs par pôle</p>
            <div class="space-y-1.5">
              <div v-for="p in synthese.parPole.slice(0, 6)" :key="p.pole" class="flex items-center gap-2">
                <span class="w-40 shrink-0 truncate text-xs text-ink-2">{{ p.pole }}</span>
                <div class="h-2 flex-1 overflow-hidden rounded-full bg-panel-2">
                  <div class="h-full rounded-full bg-green" :style="{ width: poleWidth(p.effectif) + '%' }" />
                </div>
                <span class="w-6 shrink-0 text-right text-xs text-ink-3">{{ p.effectif }}</span>
              </div>
            </div>
          </div>
          <div class="min-w-0">
            <p class="mb-2 text-xs font-semibold text-ink-2">Pipeline des candidatures</p>
            <div class="flex flex-wrap gap-2">
              <span v-for="c in synthese.candidaturesParStatut" :key="c.statut"
                    class="inline-flex items-center gap-1.5 rounded-lg border border-border bg-panel px-2.5 py-1 text-xs text-ink-2">
                {{ statutLabel(c.statut) }} <b class="text-ink">{{ c.nombre }}</b>
              </span>
              <span v-if="!synthese.candidaturesParStatut.length" class="text-xs text-ink-3">Aucune candidature.</span>
            </div>
            <div class="mt-4 flex items-center gap-2 rounded-xl border border-warning/25 bg-warning-soft/50 px-3 py-2">
              <AppIcon name="flag" :size="15" class="text-warning" />
              <span class="text-xs text-ink-2">
                <b class="text-ink">{{ synthese.famillesEnTension }}</b> famille(s) de compétences en tension forte
              </span>
            </div>
          </div>
        </div>
      </BaseCard>

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
