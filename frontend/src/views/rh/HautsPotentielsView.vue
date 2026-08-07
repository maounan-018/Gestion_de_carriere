<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { HautPotentiel, RhPerson, SuccessionPlan } from '@/types/rh'
import { scoreText } from '@/utils/score'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
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

// Plan de succession CALCULÉ (déterministe, instantané — POST /rh/succession).
const depts = ref<{ key: string; nom: string }[]>([])
const selectedDept = ref('')
const succBusy = ref(false)
const succPlan = ref<SuccessionPlan | null>(null)
const readinessTone: Record<string, 'new' | 'ai' | 'warn'> = {
  'Prêt': 'new', '12-24 mois': 'ai', 'À développer': 'warn',
}

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

      <BaseCard title="Postes clés · plan de succession">
        <p class="mb-3 text-xs text-ink-3">
          Relève interne calculée par adéquation de compétences : successeurs pressentis, niveau de
          préparation et postes clés à risque (aucun successeur prêt).
        </p>
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
            <AppIcon name="route" :size="15" /> {{ succBusy ? 'Calcul…' : 'Calculer le plan de succession' }}
          </BaseButton>
        </div>

        <template v-if="succPlan">
          <div class="mt-4 flex flex-wrap items-center gap-2">
            <BasePill tone="ai">{{ succPlan.postesCles }} poste(s) clé(s)</BasePill>
            <BasePill tone="new">{{ succPlan.couverts }} avec relève</BasePill>
            <BasePill :tone="succPlan.aRisque ? 'warn' : 'mut'">{{ succPlan.aRisque }} à risque</BasePill>
            <span class="text-xs text-ink-3">· effectif analysé : {{ succPlan.effectif }}</span>
          </div>
          <p v-if="!succPlan.roles.length" class="mt-3 text-sm text-ink-3">
            Aucun poste d'encadrement identifié dans ce département.
          </p>
          <div v-else class="mt-3 space-y-3">
            <div
              v-for="(r, i) in succPlan.roles"
              :key="i"
              class="rounded-xl border p-3.5"
              :class="r.risque ? 'border-warning/30 bg-warning-soft/40' : 'border-border bg-panel'"
            >
              <div class="flex flex-wrap items-center gap-2">
                <h4 class="text-sm font-bold text-ink">{{ r.poste }}</h4>
                <BasePill v-if="r.risque" tone="warn">Poste à risque</BasePill>
                <span class="text-xs text-ink-3">· titulaire : {{ r.titulaire }}</span>
              </div>
              <p v-if="r.risque" class="mt-1 text-xs text-ink-2">
                Aucun successeur interne suffisamment prêt · vivier à constituer.
              </p>
              <div v-else class="mt-2 space-y-2">
                <div
                  v-for="(s, j) in r.successeurs"
                  :key="j"
                  class="flex flex-wrap items-center gap-2 border-t border-border pt-2 first:border-0 first:pt-0"
                >
                  <span class="text-sm font-semibold text-ink">{{ s.nom }}</span>
                  <span class="text-xs text-ink-3">{{ s.poste }}</span>
                  <span class="font-display text-sm font-bold" :class="scoreText(s.score)">{{ s.score }} %</span>
                  <BasePill :tone="readinessTone[s.readiness] ?? 'mut'">{{ s.readiness }}</BasePill>
                  <span v-if="s.ecarts.length" class="flex flex-wrap items-center gap-1 text-xs text-ink-3">
                    · à combler : <BaseChip v-for="e in s.ecarts" :key="e">{{ e }}</BaseChip>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </BaseCard>
    </template>
  </div>
</template>
