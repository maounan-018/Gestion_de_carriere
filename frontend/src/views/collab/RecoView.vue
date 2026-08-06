<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Sparkles, Info } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import type { RecoData } from '@/types/domain'
import { scoreText, byPctDesc } from '@/utils/score'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const reco = ref<RecoData | null>(null)
const loading = ref(true)
const error = ref('')

// Faisabilité de l'aspiration (inférence de trajectoire) — best-effort, n'empêche
// pas l'affichage des recommandations.
const faisa = ref<Awaited<ReturnType<typeof apiService.getMaFaisabiliteAspiration>>>(null)
const VERDICT: Record<string, { tone: 'new' | 'warn' | 'ai'; label: string }> = {
  accessible: { tone: 'new', label: 'Accessible' },
  ambitieuse: { tone: 'warn', label: 'Ambitieuse' },
  a_defricher: { tone: 'ai', label: 'À défricher' },
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    reco.value = await apiService.getReco()
  } catch {
    error.value = 'Impossible de charger vos recommandations.'
  } finally {
    loading.value = false
  }
  apiService.getMaFaisabiliteAspiration().then((f) => { faisa.value = f }).catch(() => { faisa.value = null })
}
onMounted(load)
</script>

<template>
  <LoadingState v-if="loading" label="Génération de vos recommandations par l'IA locale · quelques secondes…" />
  <ErrorState v-else-if="error" :message="error">
    <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
  </ErrorState>

  <div v-else-if="reco" class="space-y-5">
    <!-- Objectif ambigu : bandeau de clarification seul (on masque les cartes vides). -->
    <div
      v-if="reco.confiance === 'ambigu'"
      class="flex items-start gap-3 rounded-2xl border border-warning/30 bg-warning-soft/50 p-4"
    >
      <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-warning text-white">
        <Info :size="18" />
      </div>
      <div>
        <h3 class="text-sm font-bold text-ink">Objectif à préciser</h3>
        <p class="mt-0.5 text-sm text-ink-2">{{ reco.plan }}</p>
      </div>
    </div>

    <template v-else>
    <BaseCard>
      <div class="flex flex-wrap items-center gap-4">
        <div class="min-w-0 flex-1">
          <div class="text-xs font-semibold uppercase tracking-wide text-green-deep">Poste visé</div>
          <h2 class="font-display text-2xl font-bold text-ink">{{ reco.posteVise }}</h2>
          <p class="text-xs text-ink-3">Recommandations ancrées sur les compétences du poste · ESCO · O*NET · SFIA</p>
        </div>
        <div class="text-center">
          <div class="font-display text-4xl font-bold leading-none" :class="scoreText(reco.pct)">{{ reco.pct }} %</div>
          <div class="text-[11px] text-ink-3">adéquation actuelle</div>
        </div>
        <RouterLink :to="{ name: 'collab.coach' }">
          <BaseButton variant="ai"><Sparkles :size="15" /> Discuter avec le Coach</BaseButton>
        </RouterLink>
      </div>
    </BaseCard>

    <!-- Faisabilité de l'aspiration : inférence de trajectoire sur les parcours réels -->
    <BaseCard v-if="faisa">
      <template #header>
        <div class="flex flex-wrap items-center gap-2.5">
          <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green-soft text-green-deep">
            <AppIcon name="route" :size="16" />
          </div>
          <div class="min-w-0 flex-1">
            <h3 class="font-display text-base font-bold text-ink">Faisabilité de votre aspiration</h3>
            <p class="truncate text-xs text-ink-3">D'après les parcours réels de collègues · {{ faisa.aspiration }}</p>
          </div>
          <BasePill :tone="VERDICT[faisa.verdict]?.tone || 'ai'">{{ VERDICT[faisa.verdict]?.label || faisa.verdict }}</BasePill>
          <BasePill :tone="faisa.lineaire ? 'new' : 'ai'">{{ faisa.lineaire ? 'Linéaire' : 'Non linéaire' }}</BasePill>
        </div>
      </template>
      <p class="text-sm leading-relaxed text-ink-2">{{ faisa.explication }}</p>
      <div v-if="faisa.intermediaires.length" class="mt-3">
        <p class="mb-1 text-xs font-semibold text-ink-2">Étapes typiques observées</p>
        <div class="flex flex-wrap gap-1.5">
          <BaseChip v-for="(s, i) in faisa.intermediaires" :key="i">{{ s }}</BaseChip>
        </div>
      </div>
    </BaseCard>

    <div class="grid gap-5 lg:grid-cols-2">
      <BaseCard title="Compétences à développer">
        <template #actions><BasePill tone="mut">écarts</BasePill></template>
        <div class="space-y-3">
          <div
            v-for="(s, i) in reco.skills"
            :key="i"
            class="rounded-xl border p-3.5"
            :class="s.critical ? 'border-warning/25 bg-warning-soft/40' : 'border-green-line bg-green-ghost'"
          >
            <div class="flex items-start gap-3">
              <div
                class="grid h-9 w-9 shrink-0 place-items-center rounded-lg"
                :class="s.critical ? 'bg-warning text-white' : 'bg-green text-white'"
              >
                <AppIcon :name="s.icon" :size="16" />
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex items-center justify-between gap-2">
                  <h4 class="text-sm font-bold text-ink">{{ s.title }}</h4>
                  <BasePill tone="new">{{ s.critical ? 'essentielle' : 'à renforcer' }}</BasePill>
                </div>
                <p class="mt-0.5 text-xs text-ink-2">{{ s.desc }} <BaseChip>{{ s.tag }}</BaseChip></p>
                <RouterLink :to="{ name: 'collab.formation' }" class="mt-1.5 inline-flex items-center gap-1 text-xs font-semibold text-green-deep hover:underline">
                  <AppIcon name="book" :size="12" /> Rechercher des cours
                </RouterLink>
              </div>
            </div>
          </div>
        </div>
      </BaseCard>

      <!-- Passerelles RÉSUMÉES → écran dédié listant toutes les recommandations. -->
      <BaseCard title="Passerelles métiers">
        <template #actions><BasePill tone="ai"><Sparkles :size="12" /> recherche sémantique</BasePill></template>
        <p class="mb-2.5 text-xs text-ink-3">
          Évolutions alternatives fondées sur vos compétences transférables. Cliquez pour l'analyse détaillée.
        </p>
        <div v-if="reco.passerelles.length" class="space-y-2.5">
          <RouterLink
            v-for="p in byPctDesc(reco.passerelles).slice(0, 3)"
            :key="p.title"
            :to="{ name: 'collab.passerelleDetail', params: { metier: p.title } }"
            class="flex items-center justify-between gap-3 rounded-xl border border-border bg-panel p-3 transition hover:border-green-line hover:bg-green-ghost"
          >
            <div class="flex min-w-0 items-center gap-3">
              <div class="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-green-soft text-green-deep"><AppIcon name="brief" :size="15" /></div>
              <h4 class="truncate text-sm font-bold text-ink">{{ p.title }}</h4>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <span class="font-display text-sm font-bold" :class="scoreText(p.pct)">{{ p.pct }} %</span>
              <BaseChip>{{ p.source }}</BaseChip>
            </div>
          </RouterLink>
        </div>
        <p v-else class="text-sm text-ink-3">Aucune passerelle pour le moment.</p>
        <RouterLink
          v-if="reco.passerelles.length"
          :to="{ name: 'collab.passerelles' }"
          class="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-green-deep hover:underline"
        >
          Voir toutes les passerelles ({{ reco.passerelles.length }}) →
        </RouterLink>
      </BaseCard>
    </div>

    <!-- Plan de développement : pleine largeur, aéré -->
    <BaseCard>
      <template #header>
        <div class="flex items-center gap-2.5">
          <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green text-white"><Sparkles :size="16" /></div>
          <div>
            <h3 class="font-display text-base font-bold text-ink">Plan de développement</h3>
            <p class="text-xs text-ink-3">Personnalisé par le Coach Carrière · IA locale</p>
          </div>
        </div>
      </template>
      <p class="whitespace-pre-line text-sm leading-relaxed text-ink-2">{{ reco.plan }}</p>
      <RouterLink :to="{ name: 'collab.coach' }" class="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-green-deep hover:underline">
        <Sparkles :size="14" /> Approfondir avec le Coach Carrière →
      </RouterLink>
    </BaseCard>
    </template>
  </div>
</template>
