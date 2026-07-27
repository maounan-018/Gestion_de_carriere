<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Sparkles } from 'lucide-vue-next'
import { useSessionStore } from '@/stores/session'
import { apiService } from '@/services/apiService'
import type { CollabProfile, NotificationItem } from '@/types/domain'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import ProgressionCurve from '@/components/shared/ProgressionCurve.vue'

const session = useSessionStore()
const profile = ref<CollabProfile | null>(null)
const notifs = ref<NotificationItem[]>([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [p, n] = await Promise.all([
      apiService.getCollabProfile(),
      apiService.getNotifications(),
    ])
    profile.value = p
    notifs.value = n
  } catch {
    error.value = 'Impossible de charger votre tableau de bord.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<template>
  <div class="space-y-5">
    <!-- Hero -->
    <BaseCard>
      <div class="flex flex-wrap items-center gap-4">
        <BaseAvatar :initials="session.user?.initials || 'MB'" size="xl" :photo="session.user?.photo" />
        <div class="min-w-0 flex-1">
          <div class="text-xs font-semibold uppercase tracking-wide text-green-deep">
            Espace collaborateur
          </div>
          <h2 class="font-display text-2xl font-bold text-ink">
            Bonjour {{ session.user?.firstName || 'Marc' }}
          </h2>
          <p class="text-sm text-ink-3">{{ session.user?.title }} · {{ session.user?.entity }}</p>
        </div>
        <RouterLink :to="{ name: 'collab.profil' }">
          <BaseButton variant="secondary"><AppIcon name="user" :size="15" /> Mon profil</BaseButton>
        </RouterLink>
      </div>
    </BaseCard>

    <LoadingState v-if="loading" label="Chargement de votre tableau de bord…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <template v-else-if="profile">
      <!-- Progression (« La Courbe ») -->
      <BaseCard>
        <ProgressionCurve :stations="profile.stations" :pct="profile.progressionPct" />
      </BaseCard>

      <div class="grid gap-5 lg:grid-cols-3">
        <!-- À faire -->
        <BaseCard title="À faire">
          <template #actions><BasePill tone="mut">priorités</BasePill></template>
          <div class="space-y-3">
            <div
              v-for="(t, i) in profile.todos"
              :key="i"
              class="flex gap-3 rounded-xl border border-border bg-panel p-3"
            >
              <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green-soft text-green-deep">
                <AppIcon :name="t.icon" :size="16" />
              </div>
              <div class="min-w-0">
                <h4 class="text-sm font-bold text-ink">{{ t.title }}</h4>
                <p class="text-xs text-ink-3">{{ t.text }}</p>
                <RouterLink
                  :to="{ name: t.to }"
                  class="mt-1 inline-block text-xs font-semibold text-green-deep hover:underline"
                >{{ t.linkLabel }} →</RouterLink>
              </div>
            </div>
          </div>
        </BaseCard>

        <!-- Notifications -->
        <BaseCard title="Notifications">
          <template #actions>
            <RouterLink
              :to="{ name: 'collab.notifications' }"
              class="text-xs font-semibold text-green-deep hover:underline"
            >Tout voir</RouterLink>
          </template>
          <div class="space-y-0.5">
            <RouterLink
              v-for="n in notifs.slice(0, 4)"
              :key="n.id"
              :to="{ name: n.to }"
              class="flex gap-3 rounded-xl px-2 py-2 transition hover:bg-panel"
            >
              <div
                class="grid h-8 w-8 shrink-0 place-items-center rounded-lg"
                :class="n.unread ? 'bg-green-soft text-green-deep' : 'bg-panel-2 text-ink-3'"
              >
                <AppIcon :name="n.icon" :size="15" />
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <h4 class="truncate text-[13px] font-bold text-ink">{{ n.title }}</h4>
                  <BasePill v-if="n.unread" tone="new">Nouveau</BasePill>
                </div>
                <p class="line-clamp-2 text-xs text-ink-3">{{ n.text }}</p>
                <div class="text-[11px] text-ink-3/70">{{ n.time }}</div>
              </div>
            </RouterLink>
          </div>
        </BaseCard>

        <!-- Coach -->
        <BaseCard>
          <div class="flex h-full flex-col">
            <div class="mb-2 inline-flex w-max items-center gap-1.5 rounded-full border border-green-line bg-green-ghost px-2.5 py-0.5 text-[11px] font-bold text-green-deep">
              <Sparkles :size="13" /> Coach Carrière
            </div>
            <h3 class="font-display text-base font-bold text-ink">Votre assistant carrière</h3>
            <p class="mt-1 flex-1 text-sm text-ink-3">
              Posez vos questions sur votre évolution, vos compétences et vos souhaits — en toute
              confidentialité.
            </p>
            <RouterLink :to="{ name: 'collab.coach' }" class="mt-3 block">
              <BaseButton variant="ai" block><Sparkles :size="15" /> Discuter avec le Coach</BaseButton>
            </RouterLink>
          </div>
        </BaseCard>
      </div>
    </template>
  </div>
</template>
