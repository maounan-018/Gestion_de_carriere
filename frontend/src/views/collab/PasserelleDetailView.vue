<script setup lang="ts">
/**
 * Écran DESCRIPTIF d'une passerelle métier — même traitement que le poste visé
 * (retour tuteur : « quand on clique sur une recommandation, on doit avoir un
 * écran descriptif et explicatif comme celui du poste visé »). Redirections :
 * ← liste des passerelles · → offres internes correspondantes · → Coach.
 */
import { ref, computed, onMounted } from 'vue'
import { roleRoute } from '@/composables/useRoleRoute'
import { useRoute, useRouter } from 'vue-router'
import { Sparkles, ArrowLeft, Search } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import type { Passerelle } from '@/types/domain'
import { scoreText } from '@/utils/score'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const route = useRoute()
const router = useRouter()
const passerelles = ref<Passerelle[]>([])
const posteVise = ref('')
const loading = ref(true)
const error = ref('')

const pass = computed<Passerelle | null>(
  () => passerelles.value.find((p) => p.title === route.params.metier) ?? null,
)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const reco = await apiService.getReco()
    passerelles.value = reco.passerelles
    posteVise.value = reco.posteVise
  } catch {
    error.value = 'Impossible de charger cette passerelle.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

function description(p: Passerelle): string {
  return (
    `Le métier « ${p.title} » présente une ${p.label.toLowerCase()} avec votre profil `
    + `(${p.pct} % de compétences en commun), identifiée par recherche sémantique sur le `
    + `référentiel ${p.source.toUpperCase()}. C'est une passerelle d'évolution alternative `
    + `à votre poste visé${posteVise.value ? ` (${posteVise.value})` : ''} : les compétences `
    + `déjà acquises y sont largement transférables, ce qui en fait une piste de mobilité interne `
    + `réaliste. Explorez les offres internes correspondantes pour concrétiser cette évolution.`
  )
}
</script>

<template>
  <div class="space-y-5">
    <RouterLink
      :to="{ name: roleRoute('passerelles') }"
      class="inline-flex items-center gap-1.5 text-sm font-semibold text-green-deep hover:underline"
    >
      <ArrowLeft :size="15" /> Toutes les passerelles
    </RouterLink>

    <LoadingState v-if="loading" label="Chargement de la passerelle…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <template v-else-if="pass">
      <BaseCard>
        <div class="flex flex-wrap items-center gap-4">
          <div class="min-w-0 flex-1">
            <div class="text-xs font-semibold uppercase tracking-wide text-green-deep">Passerelle métier</div>
            <h2 class="font-display text-2xl font-bold text-ink">{{ pass.title }}</h2>
            <div class="mt-1.5 flex flex-wrap items-center gap-2">
              <BasePill :tone="pass.tone">{{ pass.label }}</BasePill>
              <BaseChip>{{ pass.source.toUpperCase() }}</BaseChip>
            </div>
          </div>
          <div class="text-center">
            <div class="font-display text-4xl font-bold leading-none" :class="scoreText(pass.pct)">{{ pass.pct }} %</div>
            <div class="text-[11px] text-ink-3">compétences en commun</div>
          </div>
        </div>
      </BaseCard>

      <BaseCard title="Pourquoi cette passerelle ?">
        <p class="text-sm leading-relaxed text-ink-2">{{ description(pass) }}</p>
      </BaseCard>

      <div class="flex flex-wrap gap-3">
        <BaseButton @click="router.push({ name: roleRoute('offres'), query: { q: pass.title } })">
          <Search :size="15" /> Voir les offres internes correspondantes
        </BaseButton>
        <RouterLink :to="{ name: roleRoute('coach') }">
          <BaseButton variant="ai"><Sparkles :size="15" /> En discuter avec le Coach</BaseButton>
        </RouterLink>
      </div>
    </template>

    <ErrorState v-else message="Cette passerelle n'existe plus.">
      <template #action>
        <RouterLink :to="{ name: roleRoute('passerelles') }"><BaseButton size="sm">Retour</BaseButton></RouterLink>
      </template>
    </ErrorState>
  </div>
</template>
