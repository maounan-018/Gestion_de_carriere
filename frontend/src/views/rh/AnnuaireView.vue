<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search } from 'lucide-vue-next'
import { apiService } from '@/services/apiService'
import type { RhPerson } from '@/types/rh'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const people = ref<RhPerson[]>([])
const loading = ref(true)
const error = ref('')
const query = ref('')
const pole = ref('Tous')

async function load() {
  loading.value = true
  error.value = ''
  try {
    people.value = await apiService.getRhPeople()
  } catch {
    error.value = 'Impossible de charger l’annuaire.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const poles = computed(() => ['Tous', ...Array.from(new Set(people.value.map((p) => p.pole)))])
const filtered = computed(() =>
  people.value.filter((p) => {
    const okPole = pole.value === 'Tous' || p.pole === pole.value
    const q = query.value.trim().toLowerCase()
    const okQ = !q || (p.name + ' ' + p.role + ' ' + p.pole).toLowerCase().includes(q)
    return okPole && okQ
  }),
)
</script>

<template>
  <div class="space-y-4">
    <div class="flex min-w-56 items-center gap-2 rounded-xl border border-border bg-paper px-3 py-2">
      <Search :size="16" class="text-ink-3" />
      <input
        v-model="query"
        type="search"
        placeholder="Rechercher un collaborateur, un pôle…"
        class="w-full bg-transparent text-sm outline-none placeholder:text-ink-3"
      />
    </div>
    <div class="flex flex-wrap gap-2">
      <button
        v-for="f in poles"
        :key="f"
        class="rounded-full border px-3 py-1 text-xs font-semibold transition"
        :class="pole === f
          ? 'border-green bg-green text-white'
          : 'border-border bg-paper text-ink-2 hover:border-green-line hover:text-green-deep'"
        @click="pole = f"
      >
        {{ f }}
      </button>
    </div>

    <LoadingState v-if="loading" label="Chargement de l'annuaire…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>
    <EmptyState v-else-if="!filtered.length" title="Aucun collaborateur" text="Aucun résultat pour ces critères." />

    <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <RouterLink
        v-for="p in filtered"
        :key="p.id"
        :to="{ name: 'rh.ficheCollabRh', params: { id: p.id } }"
        class="rounded-2xl border border-border bg-paper p-4 shadow-card transition hover:-translate-y-0.5 hover:border-green-line hover:shadow-float"
      >
        <div class="flex items-center gap-3">
          <BaseAvatar :initials="p.initials" size="md" />
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-1.5">
              <h4 class="truncate text-sm font-bold text-ink">{{ p.name }}</h4>
              <BasePill v-if="p.flag === 'top'" tone="new">Haut potentiel</BasePill>
              <BasePill v-else-if="p.riskDeparture" tone="hot">Risque</BasePill>
            </div>
            <p class="truncate text-xs text-ink-3">{{ p.role }} · {{ p.pole }}</p>
          </div>
        </div>
        <div class="mt-2 flex items-center justify-between text-xs text-ink-3">
          <span>Dernier RH : {{ p.lastRh }}</span>
          <span class="font-display text-sm font-bold text-green-deep">{{ p.ring }}%</span>
        </div>
      </RouterLink>
    </div>
  </div>
</template>
