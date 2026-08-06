<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSessionStore } from '@/stores/session'
import { byPctDesc, scoreText, scoreBar } from '@/utils/score'
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
import EditProfilModal from '@/components/shared/EditProfilModal.vue'

const session = useSessionStore()
const profile = ref<CollabProfile | null>(null)
const loading = ref(true)
const error = ref('')
const showEdit = ref(false)

async function load() {
  loading.value = true
  error.value = ''
  try {
    profile.value = await apiService.getManagerProfile()
  } catch {
    error.value = 'Impossible de charger votre profil.'
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
        <BaseAvatar :initials="session.user?.initials || 'KN'" size="xl" :photo="session.user?.photo" />
        <div class="min-w-0 flex-1">
          <h2 class="font-display text-2xl font-bold text-ink">
            {{ session.user?.name || 'Karim Naji' }}
          </h2>
          <p class="text-sm text-ink-3">{{ session.user?.title }} · {{ session.user?.entity }}</p>
        </div>
        <BaseButton variant="secondary" @click="showEdit = true">
          <AppIcon name="user" :size="15" /> Éditer mon profil
        </BaseButton>
      </div>
    </BaseCard>

    <LoadingState v-if="loading" label="Chargement de votre profil…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <template v-else-if="profile">
      <BaseCard>
        <ProgressionCurve :stations="profile.stations" :pct="profile.progressionPct" />
      </BaseCard>

      <div class="grid gap-5 lg:grid-cols-2">
        <BaseCard title="Mes compétences">
          <div class="space-y-3">
            <div v-for="s in byPctDesc(profile.skills)" :key="s.label">
              <div class="mb-1 flex justify-between text-xs">
                <span class="font-medium text-ink-2">{{ s.label }}</span>
                <span class="font-semibold" :class="scoreText(s.pct)">{{ s.pct }}%</span>
              </div>
              <div class="h-1.5 overflow-hidden rounded-full bg-panel-2">
                <div class="h-full rounded-full" :class="scoreBar(s.pct)" :style="{ width: s.pct + '%' }" />
              </div>
            </div>
          </div>
        </BaseCard>

        <BaseCard title="Poste visé & aspirations">
          <div class="rounded-xl border border-green-line bg-green-ghost p-3">
            <div class="flex items-center gap-2 text-green-deep">
              <AppIcon name="route" :size="16" />
              <h4 class="text-sm font-bold">{{ profile.posteVise }}</h4>
            </div>
            <div class="mt-2 flex flex-wrap gap-1.5">
              <BaseChip v-if="profile.horizon" tone="green">Horizon : {{ profile.horizon }}</BaseChip>
              <BaseChip v-if="profile.typeEvolution" tone="green">{{ profile.typeEvolution }}</BaseChip>
              <BaseChip v-if="profile.zones" tone="green">{{ profile.zones }}</BaseChip>
              <BaseChip v-if="profile.disponibilite" tone="green">Dispo : {{ profile.disponibilite }}</BaseChip>
            </div>
          </div>
          <div class="mt-3 flex flex-wrap gap-2">
            <BaseChip v-for="a in profile.aspirations" :key="a" tone="green">{{ a }}</BaseChip>
          </div>
          <p class="mt-3 text-sm leading-relaxed text-ink-2">{{ profile.description }}</p>
        </BaseCard>
      </div>

      <BaseCard title="Avis & évaluations">
        <div class="grid gap-3 sm:grid-cols-2">
          <div v-for="(r, i) in profile.peerReviews" :key="i" class="rounded-xl border border-border bg-panel p-3">
            <div class="flex items-center gap-2">
              <BaseAvatar :initials="r.initials" size="sm" />
              <div>
                <div class="text-xs font-bold text-ink">{{ r.name }}</div>
                <div class="text-[11px] text-ink-3">{{ r.role }}</div>
              </div>
              <span class="ml-auto text-sm text-gold">{{ '★'.repeat(r.stars) }}</span>
            </div>
            <p class="mt-2 text-xs text-ink-2">« {{ r.text }} »</p>
          </div>
        </div>
      </BaseCard>
    </template>

    <EditProfilModal v-model="showEdit" @saved="load" />
  </div>
</template>
