<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { Formation, FormationStatus } from '@/types/domain'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BasePill from '@/components/ui/BasePill.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const items = ref<Formation[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()

const filters = [
  { key: 'all', label: 'Toutes' },
  { key: 'in-progress', label: 'En cours' },
  { key: 'recommended', label: 'Recommandées' },
  { key: 'done', label: 'Terminées' },
] as const
const active = ref<'all' | FormationStatus>('all')

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await apiService.getFormations()
  } catch {
    error.value = 'Impossible de charger les formations.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const filtered = computed(() =>
  active.value === 'all' ? items.value : items.value.filter((f) => f.status === active.value),
)

const STATUS: Record<FormationStatus, { label: string; tone: 'new' | 'ai' | 'ok' }> = {
  'recommended': { label: 'Recommandée', tone: 'ai' },
  'in-progress': { label: 'En cours', tone: 'new' },
  'done': { label: 'Terminée', tone: 'ok' },
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap gap-2">
      <button
        v-for="f in filters"
        :key="f.key"
        class="rounded-full border px-3 py-1 text-xs font-semibold transition"
        :class="active === f.key ? 'border-green bg-green text-white' : 'border-border bg-paper text-ink-2 hover:border-green-line hover:text-green-deep'"
        @click="active = f.key"
      >{{ f.label }}</button>
    </div>

    <LoadingState v-if="loading" label="Chargement des formations…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>
    <EmptyState v-else-if="filtered.length === 0" title="Aucune formation" text="Aucune formation dans cette catégorie pour le moment." />

    <div v-else class="grid gap-4 sm:grid-cols-2">
      <div v-for="f in filtered" :key="f.id" class="flex flex-col rounded-2xl border border-border bg-paper p-4 shadow-card">
        <div class="flex items-start justify-between gap-2">
          <div class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-green-soft text-green-deep"><AppIcon name="book" :size="18" /></div>
          <BasePill :tone="STATUS[f.status].tone">{{ STATUS[f.status].label }}</BasePill>
        </div>
        <h4 class="mt-2.5 text-sm font-bold text-ink">{{ f.title }}</h4>
        <p class="text-xs text-ink-3">{{ f.provider }}</p>
        <div class="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-ink-3">
          <span class="inline-flex items-center gap-1"><AppIcon name="clock" :size="11" /> {{ f.duration }}</span>
          <span class="inline-flex items-center gap-1"><AppIcon name="spark" :size="11" /> {{ f.level }}</span>
        </div>
        <div class="mt-2 flex flex-wrap gap-1.5">
          <BaseChip v-for="t in f.tags" :key="t">{{ t }}</BaseChip>
        </div>
        <p v-if="f.reason" class="mt-2 text-xs text-green-deep"><AppIcon name="spark" :size="12" class="inline" /> {{ f.reason }}</p>

        <div v-if="f.status === 'in-progress'" class="mt-3">
          <div class="mb-1 flex justify-between text-xs"><span class="text-ink-3">Avancement</span><b class="text-green-deep">{{ f.progress }} %</b></div>
          <div class="h-2 overflow-hidden rounded-full bg-panel-2"><div class="h-full rounded-full bg-green" :style="{ width: f.progress + '%' }" /></div>
        </div>

        <div class="mt-3 flex-1" />
        <div class="mt-2">
          <BaseButton
            v-if="f.status === 'done'"
            variant="secondary" size="sm" block
            @click="toast('Attestation — à venir', 'info')"
          ><AppIcon name="check" :size="14" /> Voir l'attestation</BaseButton>
          <BaseButton
            v-else size="sm" block
            @click="toast(f.status === 'in-progress' ? 'Reprise de la formation…' : 'Inscription enregistrée')"
          >{{ f.status === 'in-progress' ? 'Reprendre' : "S'inscrire" }}</BaseButton>
        </div>
      </div>
    </div>
  </div>
</template>
