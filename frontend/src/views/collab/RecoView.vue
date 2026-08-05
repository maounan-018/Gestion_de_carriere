<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Sparkles, Info } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import type { RecoData, Passerelle } from '@/types/domain'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const router = useRouter()
const reco = ref<RecoData | null>(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    reco.value = await apiService.getReco()
  } catch {
    error.value = 'Impossible de charger vos recommandations.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

// Passerelle : clic sur l'intitulé → description + direction (offres correspondantes).
const selPass = ref<Passerelle | null>(null)
const showPass = computed({
  get: () => selPass.value !== null,
  set: (v: boolean) => { if (!v) selPass.value = null },
})
function passDesc(p: Passerelle): string {
  return `« ${p.title} » présente une ${p.label.toLowerCase()} avec votre profil `
    + `(${p.pct} % de compétences en commun), identifiée par recherche sémantique sur le référentiel `
    + `${p.source.toUpperCase()}. Explorez les offres internes correspondantes pour envisager cette évolution.`
}
function goOffres(metier: string) {
  selPass.value = null
  router.push({ name: 'collab.offres', query: { q: metier } })
}
</script>

<template>
  <LoadingState v-if="loading" label="Génération de vos recommandations par l'IA locale · quelques secondes…" />
  <ErrorState v-else-if="error" :message="error">
    <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
  </ErrorState>

  <div v-else-if="reco" class="space-y-5">
    <!-- Objectif ambigu : bandeau de clarification seul (on masque les cartes vides). -->
    <div
      v-if="reco.confiance === 'ambigu'"
      class="flex items-start gap-3 rounded-2xl border border-warning/30 bg-warning-soft/50 p-4"
    >
      <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-warning text-white">
        <Info :size="18" />
      </div>
      <div>
        <h3 class="text-sm font-bold text-ink">Objectif à préciser</h3>
        <p class="mt-0.5 text-sm text-ink-2">{{ reco.plan }}</p>
      </div>
    </div>

    <template v-else>
    <BaseCard>
      <div class="flex flex-wrap items-center gap-4">
        <div class="min-w-0 flex-1">
          <div class="text-xs font-semibold uppercase tracking-wide text-green-deep">Poste visé</div>
          <h2 class="font-display text-2xl font-bold text-ink">{{ reco.posteVise }}</h2>
          <p class="text-xs text-ink-3">Recommandations ancrées sur les compétences du poste · ESCO · O*NET · SFIA</p>
        </div>
        <div class="text-center">
          <div class="font-display text-4xl font-bold leading-none text-green-deep">{{ reco.pct }} %</div>
          <div class="text-[11px] text-ink-3">adéquation actuelle</div>
        </div>
        <RouterLink :to="{ name: 'collab.coach' }">
          <BaseButton variant="ai"><Sparkles :size="15" /> Discuter avec le Coach</BaseButton>
        </RouterLink>
      </div>
    </BaseCard>

    <div class="grid gap-5 lg:grid-cols-2">
      <BaseCard title="Compétences à développer">
        <template #actions><BasePill tone="mut">écarts</BasePill></template>
        <div class="space-y-3">
          <div
            v-for="(s, i) in reco.skills"
            :key="i"
            class="rounded-xl border p-3.5"
            :class="s.critical ? 'border-warning/25 bg-warning-soft/40' : 'border-green-line bg-green-ghost'"
          >
            <div class="flex items-start gap-3">
              <div
                class="grid h-9 w-9 shrink-0 place-items-center rounded-lg"
                :class="s.critical ? 'bg-warning text-white' : 'bg-green text-white'"
              >
                <AppIcon :name="s.icon" :size="16" />
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex items-center justify-between gap-2">
                  <h4 class="text-sm font-bold text-ink">{{ s.title }}</h4>
                  <BasePill tone="new">{{ s.critical ? 'essentielle' : 'à renforcer' }}</BasePill>
                </div>
                <p class="mt-0.5 text-xs text-ink-2">{{ s.desc }} <BaseChip>{{ s.tag }}</BaseChip></p>
                <RouterLink :to="{ name: 'collab.formation' }" class="mt-1.5 inline-flex items-center gap-1 text-xs font-semibold text-green-deep hover:underline">
                  <AppIcon name="book" :size="12" /> Rechercher des cours
                </RouterLink>
              </div>
            </div>
          </div>
        </div>
      </BaseCard>

      <div class="space-y-5">
        <BaseCard title="Passerelles métiers">
          <template #actions><BasePill tone="ai"><Sparkles :size="12" /> recherche sémantique</BasePill></template>
          <p class="mb-2.5 text-xs text-ink-3">Cliquez une passerelle pour sa description et les offres correspondantes.</p>
          <div class="space-y-2.5">
            <button
              v-for="(p, i) in reco.passerelles"
              :key="i"
              type="button"
              class="flex w-full items-center justify-between gap-3 rounded-xl border border-border bg-panel p-3 text-left transition hover:border-green-line hover:bg-green-ghost"
              @click="selPass = p"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div class="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-green text-white"><AppIcon name="brief" :size="15" /></div>
                <h4 class="truncate text-sm font-bold text-ink">{{ p.title }}</h4>
              </div>
              <div class="flex shrink-0 items-center gap-2">
                <BasePill :tone="p.tone">{{ p.pct }} % · {{ p.label }}</BasePill>
                <BaseChip>{{ p.source }}</BaseChip>
              </div>
            </button>
          </div>
        </BaseCard>
      </div>
    </div>

    <!-- Plan de développement : pleine largeur, aéré -->
    <BaseCard>
      <template #header>
        <div class="flex items-center gap-2.5">
          <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green text-white"><Sparkles :size="16" /></div>
          <div>
            <h3 class="font-display text-base font-bold text-ink">Plan de développement</h3>
            <p class="text-xs text-ink-3">Personnalisé par le Coach Carrière · IA locale</p>
          </div>
        </div>
      </template>
      <p class="whitespace-pre-line text-sm leading-relaxed text-ink-2">{{ reco.plan }}</p>
      <RouterLink :to="{ name: 'collab.coach' }" class="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-green-deep hover:underline">
        <Sparkles :size="14" /> Approfondir avec le Coach Carrière →
      </RouterLink>
    </BaseCard>
    </template>

    <BaseModal v-model="showPass" :title="selPass?.title || 'Passerelle métier'">
      <div v-if="selPass" class="space-y-3">
        <div class="flex flex-wrap items-center gap-2">
          <BasePill :tone="selPass.tone">{{ selPass.pct }} % · {{ selPass.label }}</BasePill>
          <BaseChip>{{ selPass.source.toUpperCase() }}</BaseChip>
        </div>
        <p class="text-sm leading-relaxed text-ink-2">{{ passDesc(selPass) }}</p>
      </div>
      <template #footer>
        <BaseButton variant="secondary" size="sm" @click="showPass = false">Fermer</BaseButton>
        <BaseButton size="sm" @click="goOffres(selPass!.title)">
          <AppIcon name="search" :size="14" /> Voir les offres
        </BaseButton>
      </template>
    </BaseModal>
  </div>
</template>
