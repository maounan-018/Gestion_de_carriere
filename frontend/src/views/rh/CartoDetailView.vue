<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { apiService } from '@/services/apiService'
import type { CartoLigne } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const route = useRoute()
const familles = ref<string[]>([])
const pole = ref<CartoLigne | null>(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const m = await apiService.getCarto()
    familles.value = m.familles
    pole.value = m.lignes.find((l) => l.departementKey === route.params.pole) ?? null
  } catch {
    error.value = 'Impossible de charger le pôle.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => route.params.pole, load)

// Synthèse FACTUELLE (dérivée des données, pas d'IA fictive) : forces / écarts.
function ranked(top: boolean) {
  const p = pole.value
  if (!p) return []
  const pairs = familles.value
    .map((f, i) => ({ f, v: p.niveaux[i] }))
    .filter((x): x is { f: string; v: number } => x.v != null)
  pairs.sort((a, b) => (top ? b.v - a.v : a.v - b.v))
  return pairs.slice(0, 2)
}
const forces = computed(() => ranked(true))
const ecarts = computed(() => ranked(false))
// Criticité factuelle : un pôle avec un niveau moyen faible est plus « à risque ».
const critTone = computed<'hot' | 'warn' | 'new'>(() => {
  const m = pole.value?.niveauMoyen ?? 0
  return m < 3 ? 'hot' : m < 4 ? 'warn' : 'new'
})
const critLabel = computed(() => {
  const m = pole.value?.niveauMoyen ?? 0
  return m < 3 ? 'à renforcer' : m < 4 ? 'à consolider' : 'solide'
})
</script>

<template>
  <LoadingState v-if="loading" label="Chargement du pôle…" />
  <ErrorState v-else-if="error" :message="error">
    <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
  </ErrorState>
  <EmptyState v-else-if="!pole" title="Pôle introuvable" text="Ce pôle n'existe pas.">
    <template #action>
      <RouterLink :to="{ name: 'rh.cartographie' }"><BaseButton size="sm">Retour</BaseButton></RouterLink>
    </template>
  </EmptyState>

  <div v-else>
    <BaseBreadcrumb
      :items="[{ label: 'Cartographie', to: { name: 'rh.cartographie' } }, { label: pole.label }]"
    />
    <div class="grid gap-5 lg:grid-cols-[1fr_320px]">
      <BaseCard :title="`Compétences · ${pole.label}`">
        <div class="space-y-3">
          <div v-for="(f, i) in familles" :key="f">
            <div class="mb-1 flex justify-between text-xs">
              <span class="font-medium text-ink-2">{{ f }}</span>
              <span class="text-ink-3">{{ pole.niveaux[i] != null ? pole.niveaux[i] + '/5' : '—' }}</span>
            </div>
            <div class="h-2 overflow-hidden rounded-full bg-panel-2">
              <div
                class="h-full rounded-full bg-green"
                :style="{ width: ((pole.niveaux[i] ?? 0) / 5) * 100 + '%' }"
              />
            </div>
          </div>
        </div>
        <div v-if="pole.people.length" class="mt-4">
          <div class="mb-1 text-xs font-semibold text-ink-3">
            Collaborateurs du pôle · {{ pole.effectif }}
          </div>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="n in pole.people"
              :key="n"
              class="rounded-lg bg-panel-2 px-2.5 py-1 text-xs text-ink-2"
            >{{ n }}</span>
          </div>
        </div>
      </BaseCard>

      <BaseCard>
        <div class="mb-2 flex items-center gap-2">
          <div class="grid h-8 w-8 place-items-center rounded-lg bg-green text-white">
            <AppIcon name="grid" :size="15" />
          </div>
          <h3 class="font-display text-sm font-bold text-ink">Synthèse du pôle</h3>
        </div>
        <div class="mb-3 flex flex-wrap items-center gap-2">
          <BasePill :tone="critTone">Maîtrise {{ critLabel }}</BasePill>
          <span class="text-xs text-ink-3">Niveau moyen : <b class="text-ink-2">{{ pole.niveauMoyen ?? '—' }}/5</b></span>
        </div>
        <div v-if="forces.length" class="mb-2">
          <div class="mb-1 text-[11px] font-semibold uppercase tracking-wide text-green-deep">Points forts</div>
          <div class="flex flex-wrap gap-1.5">
            <span v-for="x in forces" :key="x.f" class="rounded-lg bg-green-ghost px-2 py-1 text-xs text-green-deep">
              {{ x.f }} · {{ x.v }}/5
            </span>
          </div>
        </div>
        <div v-if="ecarts.length">
          <div class="mb-1 text-[11px] font-semibold uppercase tracking-wide text-warning">Familles à développer</div>
          <div class="flex flex-wrap gap-1.5">
            <span v-for="x in ecarts" :key="x.f" class="rounded-lg bg-warning-soft px-2 py-1 text-xs text-warning">
              {{ x.f }} · {{ x.v }}/5
            </span>
          </div>
          <div class="mt-3 flex items-center gap-2 rounded-xl border border-green-line bg-green-ghost px-3 py-2 text-xs text-green-deep">
            <AppIcon name="route" :size="14" /> Priorité de développement : <b>{{ ecarts[0].f }}</b>
          </div>
        </div>
      </BaseCard>
    </div>
  </div>
</template>
