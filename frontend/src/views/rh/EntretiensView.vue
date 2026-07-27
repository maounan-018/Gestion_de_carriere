<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import type { VeilleType } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const veille = ref<VeilleType[]>([])
const loading = ref(true)
const error = ref('')
const filter = ref<'both' | 'annuels' | 'rh'>('both')

async function load() {
  loading.value = true
  error.value = ''
  try {
    veille.value = await apiService.getVeille()
  } catch {
    error.value = 'Impossible de charger la veille des entretiens.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const shown = computed(() =>
  filter.value === 'both' ? veille.value : veille.value.filter((v) => v.key === filter.value),
)
const totals = computed(() => {
  const s = shown.value
  return {
    done: s.reduce((a, v) => a + v.done, 0),
    planned: s.reduce((a, v) => a + v.planned, 0),
    late: s.reduce((a, v) => a + v.late, 0),
  }
})
</script>

<template>
  <div class="space-y-4">
    <div class="inline-flex rounded-xl border border-border bg-paper p-1">
      <button
        v-for="f in (['both', 'annuels', 'rh'] as const)"
        :key="f"
        class="rounded-lg px-3.5 py-1.5 text-sm font-semibold transition"
        :class="filter === f ? 'bg-green text-white' : 'text-ink-2 hover:text-ink'"
        @click="filter = f"
      >
        {{ f === 'both' ? 'Tous' : f === 'annuels' ? 'Annuels (managers)' : 'RH ↔ collab' }}
      </button>
    </div>

    <LoadingState v-if="loading" label="Chargement…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <template v-else>
      <div class="grid gap-3 sm:grid-cols-3">
        <div class="rounded-2xl border border-border bg-paper p-4 shadow-card">
          <div class="font-display text-2xl font-extrabold text-green-deep">{{ totals.done }}</div>
          <div class="text-xs text-ink-3">Réalisés</div>
        </div>
        <div class="rounded-2xl border border-border bg-paper p-4 shadow-card">
          <div class="font-display text-2xl font-extrabold text-ink">{{ totals.planned }}</div>
          <div class="text-xs text-ink-3">Planifiés</div>
        </div>
        <div class="rounded-2xl border border-border bg-paper p-4 shadow-card">
          <div class="font-display text-2xl font-extrabold text-warning">{{ totals.late }}</div>
          <div class="text-xs text-ink-3">En retard</div>
        </div>
      </div>

      <div class="grid gap-4" :class="shown.length > 1 ? 'lg:grid-cols-2' : ''">
        <BaseCard v-for="v in shown" :key="v.key" :title="v.label">
          <p class="text-sm text-ink-3">{{ v.desc }}</p>
          <div class="mt-3 flex flex-wrap gap-4 text-sm">
            <span>Réalisés <b class="text-green-deep">{{ v.done }}</b></span>
            <span>Planifiés <b class="text-ink">{{ v.planned }}</b></span>
            <span>En retard <b class="text-warning">{{ v.late }}</b></span>
          </div>
          <div class="mt-2 h-2 overflow-hidden rounded-full bg-panel-2">
            <div class="h-full rounded-full bg-green" :style="{ width: (v.done / (v.done + v.planned)) * 100 + '%' }" />
          </div>
        </BaseCard>
      </div>
    </template>
  </div>
</template>
