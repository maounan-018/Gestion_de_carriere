<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { Candidature } from '@/types/domain'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const items = ref<Candidature[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()
const busyId = ref<string | null>(null)

/** Une candidature n'est retirable que tant qu'elle n'est pas décidée/déjà retirée. */
function canWithdraw(c: Candidature): boolean {
  return !!c.id && (c.status === 'Envoyée' || c.status === 'En revue' || c.status === 'Entretien planifié')
}

async function retirer(c: Candidature) {
  if (!c.id || busyId.value) return
  busyId.value = c.id
  const prev = { status: c.status, tone: c.tone }
  c.status = 'Retirée'
  c.tone = 'mut'
  try {
    await apiService.retirerCandidature(c.id)
    toast('Candidature retirée')
  } catch (e) {
    c.status = prev.status
    c.tone = prev.tone
    toast(e instanceof Error ? e.message : 'Échec du retrait', 'error')
  } finally {
    busyId.value = null
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await apiService.getCandidatures()
  } catch {
    error.value = 'Impossible de charger vos candidatures.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const kpis = computed(() => {
  const total = items.value.length
  const enCours = items.value.filter((c) => c.status === 'En revue' || c.status === 'Entretien planifié').length
  const entretien = items.value.filter((c) => c.status === 'Entretien planifié').length
  const repondues = items.value.filter((c) => c.status !== 'Envoyée').length
  const taux = total ? Math.round((repondues / total) * 100) : 0
  return [
    { icon: 'send' as const, value: String(total), label: 'Candidatures' },
    { icon: 'clock' as const, value: String(enCours), label: 'En cours' },
    { icon: 'cal' as const, value: String(entretien), label: 'Entretien planifié' },
    { icon: 'check' as const, value: taux + ' %', label: 'Taux de réponse' },
  ]
})
</script>

<template>
  <div>
    <BaseBreadcrumb
      :items="[{ label: 'Offres internes', to: { name: 'collab.offres' } }, { label: 'Mes candidatures' }]"
    />

    <LoadingState v-if="loading" label="Chargement de vos candidatures…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>
    <EmptyState
      v-else-if="items.length === 0"
      title="Aucune candidature"
      text="Explorez les offres internes et postulez à celles qui correspondent à votre projet."
    >
      <template #action>
        <RouterLink :to="{ name: 'collab.offres' }"><BaseButton size="sm">Explorer les offres</BaseButton></RouterLink>
      </template>
    </EmptyState>

    <div v-else class="space-y-4">
      <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div v-for="k in kpis" :key="k.label" class="rounded-2xl border border-border bg-paper p-4 shadow-card">
          <div class="mb-1 grid h-8 w-8 place-items-center rounded-lg bg-green-soft text-green-deep">
            <AppIcon :name="k.icon" :size="16" />
          </div>
          <div class="font-display text-2xl font-bold text-ink">{{ k.value }}</div>
          <div class="text-xs text-ink-3">{{ k.label }}</div>
        </div>
      </div>

      <BaseCard title="Historique">
        <template #actions>
          <RouterLink :to="{ name: 'collab.offres' }">
            <BaseButton variant="secondary" size="sm"><AppIcon name="search" :size="14" /> Explorer</BaseButton>
          </RouterLink>
        </template>
        <div class="divide-y divide-border">
          <div v-for="(c, i) in items" :key="i" class="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
            <div class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-panel-2 text-ink-2">
              <AppIcon :name="c.icon" :size="17" />
            </div>
            <div class="min-w-0 flex-1">
              <h4 class="truncate text-sm font-bold text-ink">{{ c.title }}</h4>
              <div class="flex flex-wrap gap-x-3 text-[11px] text-ink-3">
                <span class="inline-flex items-center gap-1"><AppIcon name="brief" :size="11" /> {{ c.type }}</span>
                <span class="inline-flex items-center gap-1"><AppIcon name="cal" :size="11" /> Envoyée le {{ c.date }}</span>
              </div>
            </div>
            <BasePill :tone="c.tone">{{ c.status }}</BasePill>
            <BaseButton
              v-if="canWithdraw(c)"
              variant="secondary"
              size="sm"
              :disabled="busyId === c.id"
              @click="retirer(c)"
            >
              Retirer
            </BaseButton>
          </div>
        </div>
      </BaseCard>
    </div>
  </div>
</template>
