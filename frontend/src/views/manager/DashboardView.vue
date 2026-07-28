<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Sparkles } from '@lucide/vue'
import { useSessionStore } from '@/stores/session'
import { apiService } from '@/services/apiService'
import type { TeamMember, KpiCard } from '@/types/manager'
import type { NotificationItem } from '@/types/domain'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const session = useSessionStore()
const kpis = ref<KpiCard[]>([])
const team = ref<TeamMember[]>([])
const notifs = ref<NotificationItem[]>([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [k, t, n] = await Promise.all([
      apiService.getManagerKpis(),
      apiService.getTeam(),
      apiService.getManagerNotifications(),
    ])
    kpis.value = k
    team.value = t
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
    <BaseCard>
      <div class="flex flex-wrap items-center gap-4">
        <BaseAvatar :initials="session.user?.initials || 'JM'" size="xl" :photo="session.user?.photo" />
        <div class="min-w-0 flex-1">
          <div class="text-xs font-semibold uppercase tracking-wide text-green-deep">Espace manager</div>
          <h2 class="font-display text-2xl font-bold text-ink">
            Bonjour {{ session.user?.firstName || 'Jean-Marc' }}
          </h2>
          <p class="text-sm text-ink-3">{{ session.user?.title }} · {{ session.user?.entity }}</p>
        </div>
        <RouterLink :to="{ name: 'manager.profil' }">
          <BaseButton variant="secondary"><AppIcon name="user" :size="15" /> Mon profil</BaseButton>
        </RouterLink>
      </div>
    </BaseCard>

    <LoadingState v-if="loading" label="Chargement de votre tableau de bord…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <template v-else>
      <!-- KPIs -->
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <RouterLink
          v-for="k in kpis"
          :key="k.label"
          :to="{ name: k.to }"
          class="rounded-2xl border border-border bg-paper p-4 shadow-card transition hover:-translate-y-0.5 hover:border-green-line hover:shadow-float"
        >
          <div class="grid h-9 w-9 place-items-center rounded-lg bg-green-soft text-green-deep">
            <AppIcon :name="k.icon" :size="16" />
          </div>
          <div class="mt-2 font-display text-2xl font-extrabold text-ink">{{ k.value }}</div>
          <div class="text-xs text-ink-3">
            {{ k.label }}<span v-if="k.hint"> · {{ k.hint }}</span>
          </div>
        </RouterLink>
      </div>

      <div class="grid gap-5 lg:grid-cols-3">
        <!-- Équipe -->
        <BaseCard title="Mon équipe" class="lg:col-span-2">
          <template #actions>
            <RouterLink :to="{ name: 'manager.equipe' }" class="text-xs font-semibold text-green-deep hover:underline">Voir tout</RouterLink>
          </template>
          <div class="grid gap-2 sm:grid-cols-2">
            <RouterLink
              v-for="m in team.slice(0, 6)"
              :key="m.id"
              :to="{ name: 'manager.ficheCollab', params: { id: m.id } }"
              class="flex items-center gap-3 rounded-xl border border-border bg-panel p-2.5 transition hover:border-green-line"
            >
              <BaseAvatar :initials="m.initials" size="md" />
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-1.5">
                  <h4 class="truncate text-[13px] font-bold text-ink">{{ m.name }}</h4>
                  <BasePill v-if="m.flag === 'top'" tone="new">Haut potentiel</BasePill>
                  <BasePill v-else-if="m.flag === 'watch'" tone="warn">À suivre</BasePill>
                </div>
                <p class="truncate text-xs text-ink-3">{{ m.role }}</p>
              </div>
              <div class="font-display text-sm font-bold text-green-deep">{{ m.ring }}%</div>
            </RouterLink>
          </div>
        </BaseCard>

        <!-- Notifications -->
        <BaseCard title="Notifications">
          <template #actions>
            <RouterLink :to="{ name: 'manager.notifications' }" class="text-xs font-semibold text-green-deep hover:underline">Tout voir</RouterLink>
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
              </div>
            </RouterLink>
          </div>
        </BaseCard>
      </div>

      <!-- Coach -->
      <BaseCard>
        <div class="flex flex-wrap items-center gap-3">
          <div class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-green text-white">
            <Sparkles :size="18" />
          </div>
          <div class="min-w-0 flex-1">
            <h3 class="font-display text-base font-bold text-ink">Coach Carrière</h3>
            <p class="text-sm text-ink-3">
              Préparez vos entretiens et votre propre évolution, en toute confidentialité.
            </p>
          </div>
          <RouterLink :to="{ name: 'manager.coach' }">
            <BaseButton variant="ai"><Sparkles :size="15" /> Discuter</BaseButton>
          </RouterLink>
        </div>
      </BaseCard>
    </template>
  </div>
</template>
