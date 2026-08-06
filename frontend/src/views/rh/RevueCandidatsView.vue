<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Sparkles } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import { useSessionStore } from '@/stores/session'
import type { RhOffer, RhCandidate } from '@/data/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import CvPreview from '@/components/shared/CvPreview.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const route = useRoute()
const { toast } = useToast()
const offer = ref<RhOffer | null>(null)
const candidates = ref<RhCandidate[]>([])
const loading = ref(true)
const error = ref('')

// Vue partagée RH / manager : le manager consulte les candidats de SES offres
// publiées (méta via « mes-offres ») ; le RH via la liste RH globale.
const isManager = computed(() => useSessionStore().role === 'manager')
const backHome = computed(() =>
  isManager.value
    ? { label: 'Mes offres publiées', to: { name: 'manager.mesOffres' } }
    : { label: 'Offres', to: { name: 'rh.offres' } },
)
const ficheRoute = computed(() => (isManager.value ? 'manager.ficheCollab' : 'rh.ficheCollabRh'))

// Aperçu CV intégré (visionneuse) — sans téléchargement.
const cvOpen = ref(false)
const cvProfilId = ref<number | null>(null)
const cvNom = ref('')
function voirCv(c: RhCandidate) {
  cvProfilId.value = Number(c.personId)
  cvNom.value = c.name
  cvOpen.value = true
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const key = route.params.key as string
    const o = isManager.value
      ? await apiService.getMesOffreRevue(key)
      : await apiService.getRhOffer(key)
    offer.value = o ?? null
    candidates.value = o?.candidateList ? [...o.candidateList] : []
  } catch {
    error.value = 'Impossible de charger les candidatures.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

// Retenu en tête, puis par score décroissant.
const ranked = computed(() =>
  [...candidates.value].sort((a, b) => {
    if (a.status === 'retenu' !== (b.status === 'retenu')) return a.status === 'retenu' ? -1 : 1
    return b.score - a.score
  }),
)

const statusMeta: Record<RhCandidate['status'], { tone: 'ok' | 'ai' | 'new' | 'mut' | 'warn'; label: string }> = {
  retenu: { tone: 'ok', label: 'Retenu' },
  entretien: { tone: 'ai', label: 'En entretien' },
  preselection: { tone: 'new', label: 'Présélectionné' },
  nouveau: { tone: 'mut', label: 'Nouveau' },
  ecarte: { tone: 'warn', label: 'Écarté' },
}
function scoreColor(s: number) {
  return s >= 80 ? 'bg-green' : s >= 65 ? 'bg-gold' : 'bg-warning'
}

// Statut front → décision backend (les 3 seules valeurs acceptées par l'API).
const BACKEND_DECISION: Partial<Record<RhCandidate['status'], 'retenue' | 'rejetee' | 'en_evaluation'>> = {
  retenu: 'retenue',
  ecarte: 'rejetee',
  entretien: 'en_evaluation',
  preselection: 'en_evaluation',
}

async function setStatus(c: RhCandidate, status: RhCandidate['status'], msg: string) {
  const prev = c.status
  // Un seul candidat retenu à la fois (démotion locale du précédent).
  if (status === 'retenu') {
    candidates.value.forEach((x) => {
      if (x !== c && x.status === 'retenu') x.status = 'entretien'
    })
  }
  c.status = status
  const decision = BACKEND_DECISION[status]
  // En live, on persiste la décision ; en mock (pas de candidatureId), simple retour visuel.
  if (c.candidatureId && decision) {
    try {
      await apiService.decideCandidature(c.candidatureId, decision)
      toast(msg, status === 'ecarte' ? 'info' : 'ok')
    } catch (e) {
      c.status = prev
      toast(e instanceof Error ? e.message : 'Échec de la décision', 'error')
    }
  } else {
    toast(msg, status === 'ecarte' ? 'info' : 'ok')
  }
}

// Recalculer le score (attendus de l'offre modifiés depuis le dépôt).
const reevalKey = ref<string | null>(null)
async function reevaluer(c: RhCandidate) {
  if (!c.candidatureId || reevalKey.value) return
  reevalKey.value = c.candidatureId
  try {
    c.score = await apiService.reevaluerCandidature(c.candidatureId)
    toast(`Score recalculé : ${c.score} %`, 'ok')
  } catch (e) {
    toast(e instanceof Error ? e.message : 'Échec de la réévaluation', 'error')
  } finally {
    reevalKey.value = null
  }
}
</script>

<template>
  <div>
    <BaseBreadcrumb :items="[backHome, { label: 'Revue des candidatures' }]" />

    <LoadingState v-if="loading" label="Chargement des candidatures…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <template v-else-if="offer">
      <BaseCard class="mb-4">
        <div class="flex flex-wrap items-center gap-2">
          <h1 class="font-display text-lg font-bold text-ink">{{ offer.title }}</h1>
          <BasePill tone="mut">{{ offer.type }} · {{ offer.ligne }}</BasePill>
        </div>
        <p class="mt-1 text-sm text-ink-3">
          <b class="text-ink-2">{{ offer.candidates }}</b> candidatures ·
          <b class="text-green-deep">{{ offer.compatible }}</b> au-dessus du seuil de compatibilité.
        </p>
        <div class="mt-3 flex items-start gap-2 rounded-xl border border-green-line bg-green-ghost p-3">
          <Sparkles :size="15" class="mt-0.5 shrink-0 text-green-deep" />
          <p class="text-xs text-ink-2">
            Le <b>score de compatibilité</b> mesure la couverture des compétences du poste · c'est une
            aide à la décision, <b>pas un filtre</b> : tous les candidats restent consultables, y
            compris ceux sous le seuil.
          </p>
        </div>
      </BaseCard>

      <EmptyState
        v-if="ranked.length === 0"
        title="Aucune candidature nominative"
        text="Les candidatures détaillées ne sont pas encore disponibles pour cette offre."
      />

      <div v-else class="space-y-3">
        <BaseCard v-for="c in ranked" :key="c.personId" class="min-w-0">
          <div class="flex flex-wrap items-center gap-3">
            <BaseAvatar :initials="c.initials" size="md" />
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <RouterLink
                  :to="{ name: ficheRoute, params: { id: c.personId } }"
                  class="text-sm font-bold text-ink hover:text-green-deep hover:underline"
                >
                  {{ c.name }}
                </RouterLink>
                <BasePill :tone="statusMeta[c.status].tone">{{ statusMeta[c.status].label }}</BasePill>
              </div>
              <p class="truncate text-xs text-ink-3">{{ c.role }} · {{ c.pole }}</p>
            </div>
            <div class="w-full sm:w-40">
              <div class="flex items-center justify-between text-xs">
                <span class="text-ink-3">Compatibilité</span>
                <b class="text-ink">{{ c.score }} %</b>
              </div>
              <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-panel-2">
                <div class="h-full rounded-full" :class="scoreColor(c.score)" :style="{ width: c.score + '%' }" />
              </div>
            </div>
          </div>

          <div class="mt-3 grid gap-3 sm:grid-cols-2">
            <div>
              <div class="mb-1 text-[11px] font-semibold uppercase tracking-wide text-green-deep">
                Compétences couvertes
              </div>
              <div class="flex flex-wrap gap-1.5">
                <BaseChip v-for="m in c.matched" :key="m" tone="green">{{ m }}</BaseChip>
              </div>
            </div>
            <div>
              <div class="mb-1 text-[11px] font-semibold uppercase tracking-wide text-warning">
                Écarts
              </div>
              <div class="flex flex-wrap gap-1.5">
                <BaseChip v-for="g in c.gaps" :key="g" tone="gap">{{ g }}</BaseChip>
              </div>
            </div>
          </div>

          <p v-if="c.note" class="mt-2 text-xs italic text-ink-3">{{ c.note }}</p>

          <div class="mt-3 flex flex-wrap gap-2 border-t border-border pt-3">
            <BaseButton v-if="c.cvFilename" size="sm" variant="secondary" @click="voirCv(c)">
              <AppIcon name="brief" :size="14" /> Voir le CV
            </BaseButton>
            <BaseButton
              v-if="c.status !== 'retenu'"
              size="sm"
              @click="setStatus(c, 'retenu', `${c.name} retenu·e pour « ${offer.title} »`)"
            >
              Retenir
            </BaseButton>
            <BaseButton
              v-if="c.status !== 'entretien' && c.status !== 'retenu'"
              size="sm"
              variant="secondary"
              @click="setStatus(c, 'entretien', `${c.name} convoqué·e en entretien`)"
            >
              Convoquer en entretien
            </BaseButton>
            <BaseButton
              v-if="c.status === 'nouveau'"
              size="sm"
              variant="secondary"
              @click="setStatus(c, 'preselection', `${c.name} présélectionné·e`)"
            >
              Présélectionner
            </BaseButton>
            <BaseButton
              v-if="c.status !== 'ecarte' && c.status !== 'retenu'"
              size="sm"
              variant="ghost"
              @click="setStatus(c, 'ecarte', `${c.name} écarté·e de cette offre`)"
            >
              Écarter
            </BaseButton>
            <BaseButton
              v-if="c.candidatureId"
              size="sm"
              variant="ghost"
              class="ml-auto"
              :disabled="reevalKey === c.candidatureId"
              @click="reevaluer(c)"
            >
              {{ reevalKey === c.candidatureId ? 'Recalcul…' : 'Réévaluer' }}
            </BaseButton>
          </div>
        </BaseCard>
      </div>
    </template>

    <EmptyState v-else title="Offre introuvable" text="Cette offre n'existe pas ou a été retirée." />

    <CvPreview v-if="cvProfilId" v-model="cvOpen" :profil-id="cvProfilId" :nom="cvNom" />
  </div>
</template>
