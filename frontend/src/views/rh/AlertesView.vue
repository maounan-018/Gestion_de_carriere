<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Sparkles } from 'lucide-vue-next'
import { apiService } from '@/services/apiService'
import type { RhAlert } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const alerts = ref<RhAlert[]>([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    alerts.value = await apiService.getRhAlerts()
  } catch {
    error.value = 'Impossible de charger les alertes.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const sevTone: Record<string, 'hot' | 'warn' | 'ai'> = { crit: 'hot', warn: 'warn', info: 'ai' }
const sevLabel: Record<string, string> = { crit: 'critique', warn: 'à traiter', info: 'info' }
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center gap-2 text-sm text-ink-3">
      <Sparkles :size="15" class="text-green-deep" /> Feed IA · analyse consolidée des talents du Groupe.
    </div>

    <LoadingState v-if="loading" label="Chargement des alertes…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <div v-else class="space-y-3">
      <BaseCard v-for="a in alerts" :key="a.id">
        <div class="flex flex-wrap items-start gap-3">
          <div
            class="grid h-10 w-10 shrink-0 place-items-center rounded-xl"
            :class="a.severity === 'crit' ? 'bg-danger-soft text-danger' : a.severity === 'warn' ? 'bg-warning-soft text-warning' : 'bg-green-soft text-green-deep'"
          >
            <AppIcon :name="a.icon" :size="18" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <h3 class="font-display text-base font-bold text-ink">{{ a.title }}</h3>
              <BasePill :tone="sevTone[a.severity]">{{ sevLabel[a.severity] }}</BasePill>
            </div>
            <p class="mt-1 text-sm text-ink-2">{{ a.text }}</p>
          </div>
          <RouterLink :to="{ name: a.to }" class="self-center">
            <BaseButton size="sm">{{ a.cta }}</BaseButton>
          </RouterLink>
        </div>
      </BaseCard>
    </div>
  </div>
</template>
