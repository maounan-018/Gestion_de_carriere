<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import type { VeilleType, EntretienCas } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const veille = ref<VeilleType[]>([])
const cas = ref<EntretienCas[]>([])
const loading = ref(true)
const error = ref('')
const filter = ref<'both' | 'annuels' | 'rh'>('both')

async function load() {
  loading.value = true
  error.value = ''
  try {
    veille.value = await apiService.getVeille()
    // Cas concrets : best-effort (n'empêche pas l'affichage de la veille).
    apiService.getEntretiensATraiter().then((c) => { cas.value = c }).catch(() => { cas.value = [] })
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
const casShown = computed(() =>
  filter.value === 'both'
    ? cas.value
    : cas.value.filter((c) => (filter.value === 'annuels' ? c.type === 'annuel' : c.type === 'rh')),
)
function ancien(c: EntretienCas): string {
  if (c.moisDepuisDernier == null) return 'Jamais'
  return c.moisDepuisDernier <= 0 ? "moins d'un mois" : `${c.moisDepuisDernier} mois`
}
function echeance(c: EntretienCas): string {
  if (!c.datePrevue) return '—'
  return new Date(c.datePrevue).toLocaleDateString('fr-FR', { dateStyle: 'medium' })
}
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
        {{ f === 'both' ? 'Tous' : f === 'annuels' ? 'Annuels (managers)' : 'HRBP ↔ collab' }}
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

      <!-- Cas concrets à traiter : qui recevoir, quel manager, depuis quand. -->
      <BaseCard v-if="casShown.length" title="Cas à traiter">
        <p class="mb-3 text-sm text-ink-3">
          Collaborateurs à recevoir en entretien et managers qui doivent le réaliser · en retard d'abord.
        </p>
        <div class="max-h-[520px] overflow-auto rounded-xl border border-border">
          <table class="w-full text-left text-sm">
            <thead class="sticky top-0 bg-panel text-xs uppercase tracking-wide text-ink-3">
              <tr>
                <th class="px-3 py-2 font-semibold">Collaborateur</th>
                <th class="px-3 py-2 font-semibold">Type</th>
                <th class="px-3 py-2 font-semibold">Statut</th>
                <th class="px-3 py-2 font-semibold">Manager</th>
                <th class="px-3 py-2 font-semibold">Échéance</th>
                <th class="px-3 py-2 font-semibold">Dernier entretien</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in casShown" :key="`${c.profilId}-${c.type}`" class="border-t border-border">
                <td class="px-3 py-2">
                  <div class="font-semibold text-ink">{{ c.prenom }} {{ c.nom }}</div>
                  <div class="text-xs text-ink-3">{{ c.posteActuel || '—' }}</div>
                </td>
                <td class="px-3 py-2">
                  <BasePill :tone="c.type === 'annuel' ? 'ai' : 'new'">
                    {{ c.type === 'annuel' ? 'Annuel' : 'RH' }}
                  </BasePill>
                </td>
                <td class="px-3 py-2">
                  <BasePill :tone="c.statut === 'en_retard' ? 'warn' : 'mut'">
                    {{ c.statut === 'en_retard' ? 'En retard' : 'À planifier' }}
                  </BasePill>
                </td>
                <td class="px-3 py-2 text-ink-2">{{ c.managerNom || '—' }}</td>
                <td class="px-3 py-2 text-ink-2">{{ echeance(c) }}</td>
                <td class="px-3 py-2">
                  <span :class="c.moisDepuisDernier == null ? 'text-warning' : 'text-ink-2'">{{ ancien(c) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </BaseCard>
    </template>
  </div>
</template>
