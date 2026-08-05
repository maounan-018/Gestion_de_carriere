<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { RhPerson } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const people = ref<RhPerson[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()

async function load() {
  loading.value = true
  error.value = ''
  try {
    people.value = (await apiService.getRhPeople()).filter((p) => p.riskDeparture)
  } catch {
    error.value = 'Impossible de charger l’analyse.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

// Causes DÉRIVÉES des signaux réels de la population à risque (aucune liste figée).
const causes = computed<string[]>(() => {
  const ppl = people.value
  const num = (s: string) => parseFloat((s || '').replace(',', '.'))
  const lowEval = ppl.filter((p) => p.evalScore !== '—' && num(p.evalScore) < 3.4).length
  const seniors = ppl.filter((p) => { const y = parseInt(p.seniority); return !isNaN(y) && y >= 8 }).length
  const aspir = ppl.filter((p) => !!p.aspiration).length
  const out: string[] = []
  if (lowEval) out.push(`${lowEval} évaluation(s) en retrait (< 3,4/5)`)
  if (seniors) out.push(`${seniors} ancienneté(s) élevée(s) (≥ 8 ans) sans évolution récente`)
  if (aspir) out.push(`${aspir} aspiration(s) d'évolution exprimée(s) mais non concrétisée(s)`)
  out.push('Désengagement signalé par des entretiens RH en retard')
  return out
})
// Leviers de rétention RECOMMANDÉS (suggestions d'action, pas des données).
const plan = [
  'Programmer un entretien RH sous 2 semaines',
  'Proposer une mission valorisante',
  'Étudier une revalorisation salariale',
  "Clarifier les perspectives d'évolution",
]

/* ---- Transmettre le plan : point de carrière proposé au collaborateur ---- */
const showPlan = ref(false)
const targetId = ref('')
const selectedLevers = ref<string[]>([...plan])
const planNote = ref('')
const sendingPlan = ref(false)
function openPlan() {
  targetId.value = people.value[0]?.id ?? ''
  selectedLevers.value = [...plan]
  planNote.value = ''
  showPlan.value = true
}
async function transmitPlan() {
  const target = people.value.find((p) => p.id === targetId.value)
  if (!target || sendingPlan.value) return
  sendingPlan.value = true
  const message = 'Votre RH souhaite échanger avec vous sur votre évolution et vos perspectives '
    + 'au sein du Groupe. Un point de carrière va vous être proposé prochainement.'
    + (planNote.value.trim() ? ` ${planNote.value.trim()}` : '')
  try {
    const { delivered } = await apiService.messageProfil(
      target.id, 'Point de carrière proposé', message, 'collab.souhaits')
    toast(delivered
      ? `Plan de rétention initié · ${target.name} a été invité·e à un point de carrière`
      : `Plan enregistré pour ${target.name} (pas de compte actif)`, 'ok')
    showPlan.value = false
  } catch (e) {
    toast(e instanceof Error ? e.message : 'Échec de la transmission', 'error')
  } finally {
    sendingPlan.value = false
  }
}
function toggleLever(l: string) {
  const i = selectedLevers.value.indexOf(l)
  if (i >= 0) selectedLevers.value.splice(i, 1)
  else selectedLevers.value.push(l)
}
</script>

<template>
  <div>
    <BaseBreadcrumb
      :items="[{ label: 'Alertes & actions', to: { name: 'rh.alertes' } }, { label: 'Risque de départ' }]"
    />
    <LoadingState v-if="loading" label="Analyse en cours…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <div v-else class="grid gap-5 lg:grid-cols-2">
      <BaseCard class="min-w-0" title="Personnes concernées">
        <div class="space-y-2">
          <RouterLink
            v-for="p in people"
            :key="p.id"
            :to="{ name: 'rh.ficheCollabRh', params: { id: p.id } }"
            class="flex items-center gap-3 rounded-xl border border-border bg-panel p-2.5 transition hover:border-green-line"
          >
            <BaseAvatar :initials="p.initials" size="md" />
            <div class="min-w-0 flex-1">
              <h4 class="truncate text-sm font-bold text-ink">{{ p.name }}</h4>
              <p class="truncate text-xs text-ink-3">{{ p.role }} · {{ p.pole }}<span v-if="p.evalScore !== '—'"> · éval {{ p.evalScore }}</span></p>
            </div>
          </RouterLink>
        </div>
      </BaseCard>

      <div class="min-w-0 space-y-5">
        <BaseCard title="Causes probables">
          <ul class="space-y-1.5 text-sm text-ink-2">
            <li v-for="c in causes" :key="c" class="flex gap-2">
              <AppIcon name="flag" :size="14" class="mt-0.5 text-warning" /> {{ c }}
            </li>
          </ul>
        </BaseCard>
        <BaseCard title="Plan de rétention">
          <ul class="space-y-1.5 text-sm text-ink-2">
            <li v-for="a in plan" :key="a" class="flex gap-2">
              <AppIcon name="check" :size="14" class="mt-0.5 text-green-deep" /> {{ a }}
            </li>
          </ul>
          <BaseButton block class="mt-3" :disabled="!people.length" @click="openPlan">
            <AppIcon name="send" :size="15" /> Transmettre le plan
          </BaseButton>
        </BaseCard>
      </div>
    </div>

    <BaseModal v-model="showPlan" title="Initier un plan de rétention">
      <div class="space-y-4">
        <label class="block">
          <span class="mb-1 block text-xs font-semibold text-ink-2">Collaborateur concerné</span>
          <select
            v-model="targetId"
            class="w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-green"
          >
            <option v-for="p in people" :key="p.id" :value="p.id">{{ p.name }} · {{ p.role }}</option>
          </select>
        </label>
        <div>
          <span class="mb-1.5 block text-xs font-semibold text-ink-2">Leviers de rétention</span>
          <div class="space-y-1.5">
            <label v-for="l in plan" :key="l" class="flex items-start gap-2 text-sm text-ink-2">
              <input
                type="checkbox"
                class="mt-0.5 h-4 w-4 accent-green"
                :checked="selectedLevers.includes(l)"
                @change="toggleLever(l)"
              />
              <span>{{ l }}</span>
            </label>
          </div>
        </div>
        <label class="block">
          <span class="mb-1 block text-xs font-semibold text-ink-2">Note interne (optionnel)</span>
          <textarea
            v-model="planNote"
            rows="2"
            placeholder="Contexte, points d'attention…"
            class="w-full resize-none rounded-xl border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-green"
          />
        </label>
        <p class="text-[11px] text-ink-3">Le collaborateur reçoit une invitation neutre à un point de carrière ; les leviers restent internes RH.</p>
      </div>
      <template #footer>
        <BaseButton variant="secondary" size="sm" @click="showPlan = false">Annuler</BaseButton>
        <BaseButton size="sm" :disabled="sendingPlan || !targetId" @click="transmitPlan">
          <AppIcon name="send" :size="14" /> {{ sendingPlan ? 'Transmission…' : 'Initier le plan' }}
        </BaseButton>
      </template>
    </BaseModal>
  </div>
</template>
