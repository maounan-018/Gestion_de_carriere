<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Sparkles } from 'lucide-vue-next'
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
    reco.value = await apiService.getManagerReco()
  } catch {
    error.value = 'Impossible de charger les recommandations.'
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
          <p class="text-sm text-ink-3">
            Le matching classe les postes par compatibilité avec votre profil.
          </p>
        </div>
        <div class="text-center">
          <div class="font-display text-3xl font-extrabold text-green-deep">{{ reco.pct }}%</div>
          <div class="text-xs text-ink-3">adéquation</div>
        </div>
        <RouterLink :to="{ name: 'manager.coach' }">
          <BaseButton variant="ai"><Sparkles :size="15" /> Discuter avec le Coach</BaseButton>
        </RouterLink>
      </div>
    </BaseCard>

    <div class="grid gap-5 lg:grid-cols-2">
      <BaseCard title="Compétences à développer">
        <div class="space-y-3">
          <div
            v-for="(s, i) in reco.skills"
            :key="i"
            class="flex gap-3 rounded-xl border p-3"
            :class="s.critical ? 'border-danger/30 bg-danger-soft/30' : 'border-border bg-panel'"
          >
            <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green-soft text-green-deep">
              <AppIcon :name="s.icon" :size="16" />
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <h4 class="text-sm font-bold text-ink">{{ s.title }}</h4>
                <BasePill tone="new">{{ s.tag }}</BasePill>
              </div>
              <p class="text-xs text-ink-3">{{ s.desc }}</p>
            </div>
          </div>
        </div>
      </BaseCard>

      <BaseCard title="Passerelles métiers">
        <template #actions><BasePill tone="ai"><Sparkles :size="12" /> IA</BasePill></template>
        <div class="space-y-2">
          <div
            v-for="(p, i) in reco.passerelles"
            :key="i"
            class="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border bg-panel p-3"
          >
            <div class="flex items-center gap-2">
              <div class="grid h-8 w-8 place-items-center rounded-lg bg-green text-white">
                <AppIcon name="brief" :size="15" />
              </div>
              <h4 class="text-sm font-bold text-ink">{{ p.title }}</h4>
            </div>
            <div class="flex items-center gap-2">
              <BasePill :tone="p.tone">{{ p.pct }}% · {{ p.label }}</BasePill>
              <BaseChip>{{ p.source }}</BaseChip>
            </div>
          </div>
        </div>
      </BaseCard>
    </div>

    <div class="flex gap-3 rounded-2xl border border-green-line bg-green-soft p-4">
      <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green text-white">
        <Sparkles :size="16" />
      </div>
      <div>
        <h4 class="text-sm font-bold text-green-deep">Plan de développement · Coach Carrière</h4>
        <p class="mt-0.5 text-xs text-ink-2">{{ reco.plan }}</p>
      </div>
    </div>
  </div>
</template>
