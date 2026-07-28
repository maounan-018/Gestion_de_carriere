<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSessionStore } from '@/stores/session'
import { useToast } from '@/composables/useToast'
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
import { Sparkles } from '@lucide/vue'

const session = useSessionStore()
const { toast } = useToast()
const profile = ref<CollabProfile | null>(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    profile.value = await apiService.getCollabProfile()
  } catch {
    error.value = 'Impossible de charger votre profil.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const stars = (n: number) => '★★★★★'.slice(0, n) + '☆☆☆☆☆'.slice(0, 5 - n)
</script>

<template>
  <LoadingState v-if="loading" label="Chargement de votre profil…" />
  <ErrorState v-else-if="error" :message="error">
    <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
  </ErrorState>

  <div v-else-if="profile" class="space-y-5">
    <BaseCard>
      <div class="flex flex-wrap items-center gap-4">
        <BaseAvatar :initials="session.user?.initials || 'MB'" size="xl" :photo="session.user?.photo" />
        <div class="min-w-0 flex-1">
          <h2 class="font-display text-xl font-bold text-ink">{{ session.user?.name || 'Marc Bennani' }}</h2>
          <p class="text-sm text-ink-3">{{ session.user?.title }} · {{ session.user?.entity }}</p>
          <p class="mt-2 max-w-2xl text-sm text-ink-2">{{ profile.description }}</p>
        </div>
        <BaseButton variant="secondary" @click="toast('La mise à jour de votre profil se fait avec votre RH (poste, aspirations).', 'info')">
          <AppIcon name="user" :size="15" /> Éditer
        </BaseButton>
      </div>
    </BaseCard>

    <BaseCard><ProgressionCurve :stations="profile.stations" :pct="profile.progressionPct" /></BaseCard>

    <div class="grid gap-5 lg:grid-cols-[1fr_340px]">
      <div class="space-y-5">
        <BaseCard title="Mes compétences">
          <div class="space-y-3">
            <div v-for="s in profile.skills" :key="s.label">
              <div class="mb-1 flex items-center justify-between text-sm">
                <span class="text-ink-2">{{ s.label }}</span><b class="text-ink">{{ s.pct }} %</b>
              </div>
              <div class="h-2 overflow-hidden rounded-full bg-panel-2">
                <div class="h-full rounded-full" :class="s.pct < 55 ? 'bg-warning' : 'bg-green'" :style="{ width: s.pct + '%' }" />
              </div>
            </div>
          </div>
        </BaseCard>

        <BaseCard title="Avis des pairs">
          <div class="space-y-4">
            <div v-for="(r, i) in profile.peerReviews" :key="i" class="flex gap-3">
              <BaseAvatar :initials="r.initials" size="sm" />
              <div>
                <p class="text-sm text-ink-2">« {{ r.text }} »</p>
                <div class="mt-0.5 text-xs text-ink-3">
                  <span class="text-gold">{{ stars(r.stars) }}</span> {{ r.name }} · {{ r.role }}
                </div>
              </div>
            </div>
          </div>
        </BaseCard>
      </div>

      <div class="space-y-5">
        <BaseCard title="Poste visé & aspirations">
          <div class="flex gap-3 rounded-xl border border-green-line bg-green-soft p-3.5">
            <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green text-white"><AppIcon name="route" :size="16" /></div>
            <div>
              <h4 class="text-sm font-bold text-green-deep">{{ profile.posteVise }}</h4>
              <p class="text-xs text-ink-2">Horizon {{ profile.horizon }}</p>
            </div>
          </div>
          <div class="mt-3 flex flex-wrap gap-2">
            <BaseChip v-for="a in profile.aspirations" :key="a" tone="green">{{ a }}</BaseChip>
          </div>
          <p class="mt-3 text-xs text-ink-3"><AppIcon name="pin" :size="12" class="inline" /> Zones · {{ profile.zones }}</p>
          <RouterLink :to="{ name: 'collab.souhaits' }" class="mt-3 block">
            <BaseButton variant="ai" block><AppIcon name="route" :size="15" /> Gérer mes souhaits d'évolution</BaseButton>
          </RouterLink>
        </BaseCard>

        <div class="flex gap-3 rounded-2xl border border-green-line bg-green-ghost p-4">
          <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green text-white"><Sparkles :size="16" /></div>
          <div>
            <h4 class="text-sm font-bold text-green-deep">Recommandations personnalisées</h4>
            <p class="mt-0.5 text-xs text-ink-2">Découvrez les passerelles vers votre objectif.</p>
            <RouterLink :to="{ name: 'collab.reco' }" class="mt-2 inline-block text-xs font-semibold text-green-deep hover:underline">Voir les recommandations →</RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
