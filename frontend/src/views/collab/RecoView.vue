<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Sparkles } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import type { RecoData } from '@/types/domain'
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
}
onMounted(load)
</script>

<template>
  <LoadingState v-if="loading" label="Chargement des recommandations…" />
  <ErrorState v-else-if="error" :message="error">
    <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
  </ErrorState>

  <div v-else-if="reco" class="space-y-5">
    <BaseCard>
      <div class="flex flex-wrap items-center gap-4">
        <div class="min-w-0 flex-1">
          <div class="text-xs font-semibold uppercase tracking-wide text-green-deep">Poste visé</div>
          <h2 class="font-display text-2xl font-bold text-ink">{{ reco.posteVise }}</h2>
          <p class="text-xs text-ink-3">Recommandations ancrées sur les compétences du poste · ESCO · O*NET · SFIA</p>
        </div>
        <div class="text-center">
          <div class="font-display text-4xl font-bold leading-none text-green-deep">{{ reco.pct }} %</div>
          <div class="text-[11px] text-ink-3">adéquation actuelle</div>
        </div>
        <RouterLink :to="{ name: 'collab.coach' }">
          <BaseButton variant="ai"><Sparkles :size="15" /> Discuter avec le Coach</BaseButton>
        </RouterLink>
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

      <div class="space-y-5">
        <BaseCard title="Passerelles métiers">
          <template #actions><BasePill tone="ai"><Sparkles :size="12" /> recherche sémantique</BasePill></template>
          <div class="space-y-2.5">
            <div v-for="(p, i) in reco.passerelles" :key="i" class="flex items-center justify-between gap-3 rounded-xl border border-border bg-panel p-3">
              <div class="flex items-center gap-3 min-w-0">
                <div class="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-green text-white"><AppIcon name="brief" :size="15" /></div>
                <h4 class="truncate text-sm font-bold text-ink">{{ p.title }}</h4>
              </div>
              <div class="flex shrink-0 items-center gap-2">
                <BasePill :tone="p.tone">{{ p.pct }} % · {{ p.label }}</BasePill>
                <BaseChip>{{ p.source }}</BaseChip>
              </div>
            </div>
          </div>
        </BaseCard>

        <div class="flex gap-3 rounded-2xl border border-green-line bg-green-soft p-4">
          <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green text-white"><Sparkles :size="16" /></div>
          <div>
            <h4 class="text-sm font-bold text-green-deep">Plan de développement · Coach Carrière</h4>
            <p class="mt-0.5 text-xs text-ink-2">{{ reco.plan }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
