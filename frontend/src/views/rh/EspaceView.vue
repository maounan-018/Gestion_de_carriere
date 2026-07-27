<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSessionStore } from '@/stores/session'
import { apiService } from '@/services/apiService'
import type { CollabProfile } from '@/types/domain'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import ProgressionCurve from '@/components/shared/ProgressionCurve.vue'

const session = useSessionStore()
const profile = ref<CollabProfile | null>(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    profile.value = await apiService.getRhProfile()
  } catch {
    error.value = 'Impossible de charger votre espace.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<template>
  <div class="space-y-5">
    <BaseCard>
      <div class="flex flex-wrap items-center gap-4">
        <BaseAvatar :initials="session.user?.initials || 'NA'" size="xl" :photo="session.user?.photo" />
        <div class="min-w-0 flex-1">
          <h2 class="font-display text-2xl font-bold text-ink">
            {{ session.user?.name || 'Nadia Alami' }}
          </h2>
          <p class="text-sm text-ink-3">{{ session.user?.title }} · {{ session.user?.entity }}</p>
        </div>
      </div>
    </BaseCard>

    <LoadingState v-if="loading" label="Chargement de votre espace…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <template v-else-if="profile">
      <BaseCard title="Mon parcours">
        <ProgressionCurve :stations="profile.stations" :pct="profile.progressionPct" />
      </BaseCard>
      <div class="grid gap-5 lg:grid-cols-2">
        <BaseCard title="Mes compétences">
          <div class="space-y-3">
            <div v-for="s in profile.skills" :key="s.label">
              <div class="mb-1 flex justify-between text-xs">
                <span class="font-medium text-ink-2">{{ s.label }}</span>
                <span class="text-ink-3">{{ s.pct }}%</span>
              </div>
              <div class="h-1.5 overflow-hidden rounded-full bg-panel-2">
                <div class="h-full rounded-full bg-green" :style="{ width: s.pct + '%' }" />
              </div>
            </div>
          </div>
        </BaseCard>
        <BaseCard title="Poste visé & aspirations">
          <div class="rounded-xl border border-green-line bg-green-ghost p-3">
            <div class="flex items-center gap-2 text-green-deep">
              <AppIcon name="route" :size="16" /><h4 class="text-sm font-bold">{{ profile.posteVise }}</h4>
            </div>
            <p class="mt-1 text-xs text-ink-2">{{ profile.horizon }} · {{ profile.zones }}</p>
          </div>
          <div class="mt-3 flex flex-wrap gap-2">
            <BaseChip v-for="a in profile.aspirations" :key="a" tone="green">{{ a }}</BaseChip>
          </div>
          <p class="mt-3 text-sm leading-relaxed text-ink-2">{{ profile.description }}</p>
        </BaseCard>
      </div>
    </template>
  </div>
</template>
