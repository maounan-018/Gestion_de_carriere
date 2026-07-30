<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { HautPotentiel, RhPerson } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const hps = ref<HautPotentiel[]>([])
const people = ref<RhPerson[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()

// Plan de succession (IA de raisonnement, POST /rh/succession).
const depts = ref<{ key: string; nom: string }[]>([])
const selectedDept = ref('')
const succBusy = ref(false)
const succPlan = ref<{ effectif: number; plan: string; model: string } | null>(null)

async function load() {
  loading.value = true
  error.value = ''
  try {
    ;[hps.value, people.value] = await Promise.all([
      apiService.getHautsPotentiels(),
      apiService.getRhPeople(),
    ])
    apiService
      .getDepartements()
      .then((d) => {
        depts.value = d
        if (d[0] && !selectedDept.value) selectedDept.value = d[0].key
      })
      .catch(() => { depts.value = [] })
  } catch {
    error.value = 'Impossible de charger les hauts potentiels.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

function person(id: string) {
  return people.value.find((p) => p.id === id)
}

async function generateSuccession() {
  if (!selectedDept.value || succBusy.value) return
  succBusy.value = true
  succPlan.value = null
  try {
    succPlan.value = await apiService.getSuccession(selectedDept.value)
  } catch {
    toast('Analyse de succession indisponible pour le moment.', 'error')
  } finally {
    succBusy.value = false
  }
}
</script>

<template>
  <div class="space-y-5">
    <LoadingState v-if="loading" label="Chargement…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <template v-else>
      <BaseCard title="Hauts potentiels identifiés">
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div v-for="h in hps" :key="h.personId" class="rounded-2xl border border-border bg-paper p-4 shadow-card">
            <div class="flex items-center gap-3">
              <BaseAvatar :initials="person(h.personId)?.initials || '?'" size="md" />
              <div class="min-w-0 flex-1">
                <h4 class="text-sm font-bold text-ink">{{ person(h.personId)?.name }}</h4>
                <p class="truncate text-xs text-ink-3">{{ person(h.personId)?.role }}</p>
              </div>
              <div class="font-display text-lg font-bold text-green-deep">{{ h.score }}</div>
            </div>
            <div class="mt-2"><BasePill tone="new">{{ h.readiness }}</BasePill></div>
            <p class="mt-2 text-xs text-ink-2">Cible : <b class="text-ink">{{ h.target }}</b></p>
            <RouterLink :to="{ name: 'rh.ficheCollabRh', params: { id: h.personId } }" class="mt-3 block">
              <BaseButton size="sm" block variant="secondary">Ouvrir le dossier</BaseButton>
            </RouterLink>
          </div>
        </div>
      </BaseCard>

      <BaseCard title="Postes critiques · succession">
        <div class="mb-3 flex flex-wrap items-center gap-3 rounded-xl border border-warning/25 bg-warning-soft p-3">
          <AppIcon name="flag" :size="18" class="text-warning" />
          <div class="min-w-0 flex-1">
            <h4 class="text-sm font-bold text-ink">Directeur Asset Management</h4>
            <p class="text-xs text-ink-2">Poste clé sans successeur désigné · vivier à constituer.</p>
          </div>
        </div>

        <div class="flex flex-wrap items-end gap-3">
          <div>
            <label class="mb-1 block text-xs font-semibold text-ink-2">Département à analyser</label>
            <select
              v-model="selectedDept"
              class="rounded-xl border border-border bg-paper px-3 py-2 text-sm outline-none focus:border-green-line"
            >
              <option v-for="d in depts" :key="d.key" :value="d.key">{{ d.nom }}</option>
            </select>
          </div>
          <BaseButton :disabled="succBusy || !selectedDept" @click="generateSuccession">
            <AppIcon name="route" :size="15" />
            {{ succBusy ? 'Analyse en cours…' : 'Générer le plan de succession' }}
          </BaseButton>
        </div>
        <p v-if="succBusy" class="mt-2 text-xs text-ink-3">
          Raisonnement IA en cours — cela peut prendre plus d'une minute.
        </p>

        <div v-if="succPlan" class="mt-4 rounded-xl border border-border bg-panel p-4">
          <p class="mb-2 text-xs text-ink-3">
            Effectif analysé : {{ succPlan.effectif }} · modèle {{ succPlan.model }}
          </p>
          <div class="whitespace-pre-wrap text-sm leading-relaxed text-ink-2">{{ succPlan.plan }}</div>
        </div>
      </BaseCard>
    </template>
  </div>
</template>
