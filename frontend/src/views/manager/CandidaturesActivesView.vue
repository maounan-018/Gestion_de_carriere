<script setup lang="ts">
/**
 * « Candidatures » — candidats des offres du compte courant ENCORE EN COURS
 * (non clôturées / non retirées). Atteint depuis le KPI « Candidatures » du
 * tableau de bord. Groupé par offre ; chaque candidat mène à sa fiche.
 */
import { ref, computed, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useSessionStore } from '@/stores/session'
import type { CandidatureActive } from '@/services/mappers'
import { scoreText } from '@/utils/score'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const rows = ref<CandidatureActive[]>([])
const loading = ref(true)
const error = ref('')
// Vue partagée manager / HRBP : le détail d'offre et la fiche candidat dépendent du rôle.
const isRh = computed(() => useSessionStore().role === 'rh')
const offreDetailRoute = computed(() => (isRh.value ? 'rh.revueCandidats' : 'manager.offreDetail'))
const ficheRoute = computed(() => (isRh.value ? 'rh.ficheCollabRh' : 'manager.ficheCollab'))

async function load() {
  loading.value = true
  error.value = ''
  try {
    rows.value = await apiService.getMesCandidaturesActives()
  } catch {
    error.value = 'Impossible de charger les candidatures.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

// Regroupement par offre (l'ordre backend préserve offre puis score décroissant).
const groupes = computed(() => {
  const map = new Map<string, { titre: string; type: string; candidats: CandidatureActive[] }>()
  for (const c of rows.value) {
    if (!map.has(c.offreId)) map.set(c.offreId, { titre: c.offreTitre, type: c.offreType, candidats: [] })
    map.get(c.offreId)!.candidats.push(c)
  }
  return [...map.entries()].map(([offreId, g]) => ({ offreId, ...g }))
})

const statutTone: Record<string, 'new' | 'ai' | 'warn' | 'mut'> = {
  Retenue: 'new', 'En évaluation': 'ai', Déposée: 'mut', Refusée: 'warn', Retirée: 'mut',
}
</script>

<template>
  <div class="space-y-5">
    <div>
      <h2 class="font-display text-2xl font-bold text-ink">Candidatures</h2>
      <p class="text-sm text-ink-3">
        Candidats des offres <b class="text-ink-2">encore en cours</b> · les offres clôturées ou
        retirées ne sont pas listées ici.
      </p>
    </div>

    <LoadingState v-if="loading" label="Chargement des candidatures…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>
    <EmptyState
      v-else-if="!rows.length"
      title="Aucune candidature en cours"
      text="Les candidatures de vos offres ouvertes apparaîtront ici."
    />

    <template v-else>
      <BaseCard v-for="g in groupes" :key="g.offreId">
        <template #header>
          <div class="flex flex-wrap items-center gap-2.5">
            <div class="min-w-0 flex-1">
              <h3 class="font-display text-base font-bold text-ink">{{ g.titre }}</h3>
              <p class="text-xs text-ink-3">{{ g.type }} · {{ g.candidats.length }} candidat{{ g.candidats.length > 1 ? 's' : '' }}</p>
            </div>
            <RouterLink
              :to="{ name: offreDetailRoute, params: { key: g.offreId } }"
              class="text-xs font-semibold text-green-deep hover:underline"
            >
              Voir l'offre
            </RouterLink>
          </div>
        </template>
        <div class="divide-y divide-border">
          <RouterLink
            v-for="c in g.candidats"
            :key="c.candidatureId"
            :to="{ name: ficheRoute, params: { id: c.profilId } }"
            class="flex items-center gap-3 py-2.5 transition hover:bg-panel"
          >
            <BaseAvatar :initials="c.initials" size="md" :seed="c.profilId" />
            <div class="min-w-0 flex-1">
              <h4 class="truncate text-sm font-bold text-ink">{{ c.name }}</h4>
              <p class="truncate text-xs text-ink-3">{{ c.posteActuel }}</p>
            </div>
            <span v-if="c.score !== null" class="font-display text-sm font-bold" :class="scoreText(c.score)">
              {{ Math.round(c.score) }} %
            </span>
            <span v-else class="text-xs text-ink-3">—</span>
            <BasePill :tone="statutTone[c.statut] ?? 'mut'">{{ c.statut }}</BasePill>
          </RouterLink>
        </div>
      </BaseCard>
    </template>
  </div>
</template>
