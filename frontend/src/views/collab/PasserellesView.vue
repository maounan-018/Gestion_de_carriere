<script setup lang="ts">
/**
 * Liste des PASSERELLES métiers (autres recommandations d'évolution) — écran
 * dédié atteint depuis la reco du poste visé (retour tuteur : « les passerelles
 * résumées dans un onglet qui conduit à un écran avec la liste des autres
 * recommandations »). Chaque ligne redirige vers l'écran descriptif dédié.
 */
import { ref, onMounted } from 'vue'
import { roleRoute } from '@/composables/useRoleRoute'
import { useRouter } from 'vue-router'
import { ChevronRight, ArrowLeft } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import type { Passerelle } from '@/types/domain'
import { scoreText, byPctDesc } from '@/utils/score'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const router = useRouter()
const passerelles = ref<Passerelle[]>([])
const posteVise = ref('')
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const reco = await apiService.getReco()
    // Tri décroissant par compatibilité (les plus fortes en tête) — cohérent Lot 2.
    passerelles.value = byPctDesc(reco.passerelles)
    posteVise.value = reco.posteVise
  } catch {
    error.value = 'Impossible de charger les passerelles.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

// Redirection vers l'écran descriptif, clé = intitulé du métier (indépendant du tri).
function open(p: Passerelle) {
  router.push({ name: roleRoute('passerelleDetail'), params: { metier: p.title } })
}
</script>

<template>
  <div class="space-y-5">
    <RouterLink
      :to="{ name: roleRoute('reco') }"
      class="inline-flex items-center gap-1.5 text-sm font-semibold text-green-deep hover:underline"
    >
      <ArrowLeft :size="15" /> Retour aux recommandations
    </RouterLink>

    <div>
      <h2 class="font-display text-2xl font-bold text-ink">Passerelles métiers</h2>
      <p class="text-sm text-ink-3">
        Évolutions alternatives fondées sur vos compétences transférables · recherche sémantique
        ESCO · O*NET · SFIA. Cliquez une passerelle pour son analyse détaillée.
      </p>
    </div>

    <LoadingState v-if="loading" label="Chargement des passerelles…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>
    <EmptyState
      v-else-if="!passerelles.length"
      title="Aucune passerelle pour le moment"
      text="Précisez votre poste visé et vos compétences pour révéler des passerelles d'évolution."
    />

    <div v-else class="space-y-2.5">
      <button
        v-for="p in passerelles"
        :key="p.title"
        type="button"
        class="flex w-full items-center justify-between gap-3 rounded-2xl border border-border bg-paper p-4 text-left shadow-card transition hover:-translate-y-0.5 hover:border-green-line hover:shadow-float"
        @click="open(p)"
      >
        <div class="flex min-w-0 items-center gap-3">
          <div class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-green-soft text-green-deep">
            <AppIcon name="brief" :size="18" />
          </div>
          <div class="min-w-0">
            <h4 class="truncate text-sm font-bold text-ink">{{ p.title }}</h4>
            <div class="mt-0.5 flex flex-wrap items-center gap-1.5">
              <BasePill :tone="p.tone">{{ p.label }}</BasePill>
              <BaseChip>{{ p.source.toUpperCase() }}</BaseChip>
            </div>
          </div>
        </div>
        <div class="flex shrink-0 items-center gap-3">
          <div class="text-right">
            <div class="font-display text-lg font-bold leading-none" :class="scoreText(p.pct)">{{ p.pct }} %</div>
            <div class="text-[10px] text-ink-3">en commun</div>
          </div>
          <ChevronRight :size="18" class="text-ink-3" />
        </div>
      </button>
    </div>
  </div>
</template>
