<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { NotificationItem } from '@/types/domain'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseBadge from '@/components/ui/BaseBadge.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const items = ref<NotificationItem[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = (await apiService.getNotifications()).map((n) => ({ ...n }))
  } catch {
    error.value = 'Impossible de charger vos notifications.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const unreadCount = computed(() => items.value.filter((n) => n.unread).length)
function markAll() {
  items.value.forEach((n) => (n.unread = false))
  toast('Notifications marquées comme lues')
}
</script>

<template>
  <div>
    <BaseBreadcrumb
      :items="[{ label: 'Tableau de bord', to: { name: 'collab.dashboard' } }, { label: 'Notifications' }]"
    />

    <LoadingState v-if="loading" label="Chargement des notifications…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <BaseCard v-else>
      <template #header>
        <h3 class="flex items-center gap-2 font-display text-base font-bold text-ink">
          Vos notifications
          <BaseBadge tone="mut">{{ unreadCount }} non lues</BaseBadge>
        </h3>
      </template>
      <template #actions>
        <BaseButton variant="secondary" size="sm" :disabled="unreadCount === 0" @click="markAll">
          <AppIcon name="check" :size="14" /> Tout marquer comme lu
        </BaseButton>
      </template>

      <div class="divide-y divide-border">
        <RouterLink
          v-for="n in items"
          :key="n.id"
          :to="{ name: n.to }"
          class="flex gap-3 py-3 transition first:pt-0 last:pb-0 hover:bg-panel"
        >
          <div
            class="grid h-10 w-10 shrink-0 place-items-center rounded-xl"
            :class="n.unread ? 'bg-green-soft text-green-deep' : 'bg-panel-2 text-ink-3'"
          >
            <AppIcon :name="n.icon" :size="17" />
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
  </div>
</template>
