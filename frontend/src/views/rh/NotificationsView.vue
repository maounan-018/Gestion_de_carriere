<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { NotificationItem } from '@/types/domain'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const notifs = ref<NotificationItem[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()

async function load() {
  loading.value = true
  error.value = ''
  try {
    notifs.value = await apiService.getRhNotifications()
  } catch {
    error.value = 'Impossible de charger les notifications.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function markAll() {
  const prev = notifs.value.map((n) => n.unread)
  notifs.value = notifs.value.map((n) => ({ ...n, unread: false }))
  try {
    await apiService.markAllNotificationsRead()
    toast('Notifications marquées comme lues')
  } catch (e) {
    notifs.value = notifs.value.map((n, i) => ({ ...n, unread: prev[i] }))
    toast(e instanceof Error ? e.message : 'Échec de la mise à jour', 'error')
  }
}
</script>

<template>
  <BaseCard>
    <template #header><h3 class="font-display text-base font-bold text-ink">Vos notifications</h3></template>
    <template #actions>
      <BaseButton size="sm" variant="secondary" @click="markAll">
        <AppIcon name="check" :size="14" /> Tout marquer comme lu
      </BaseButton>
    </template>

    <LoadingState v-if="loading" label="Chargement…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <div v-else class="divide-y divide-border">
      <RouterLink
        v-for="n in notifs"
        :key="n.id"
        :to="{ name: n.to }"
        class="-mx-2 flex gap-3 rounded-xl px-2 py-3 transition hover:bg-panel"
      >
        <div
          class="grid h-9 w-9 shrink-0 place-items-center rounded-lg"
          :class="n.unread ? 'bg-green-soft text-green-deep' : 'bg-panel-2 text-ink-3'"
        >
          <AppIcon :name="n.icon" :size="16" />
        </div>
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <h4 class="text-sm font-bold text-ink">{{ n.title }}</h4>
            <BasePill v-if="n.unread" tone="new">Non lu</BasePill>
          </div>
          <p class="text-xs text-ink-2">{{ n.text }}</p>
        </div>
        <span class="shrink-0 text-[11px] text-ink-3">{{ n.time }}</span>
      </RouterLink>
    </div>
  </BaseCard>
</template>
