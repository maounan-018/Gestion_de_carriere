<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { apiService } from '@/services/apiService'
import type { CollabProfile, MobiliteItem } from '@/types/domain'
import { byPctDesc, scoreText, scoreBar } from '@/utils/score'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import ProgressionCurve from '@/components/shared/ProgressionCurve.vue'
import ScoringInfo from '@/components/shared/ScoringInfo.vue'
import { Sparkles } from '@lucide/vue'

const session = useSessionStore()
const profile = ref<CollabProfile | null>(null)
const mobilite = ref<MobiliteItem[]>([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    profile.value = await apiService.getCollabProfile()
    // Passerelles de mobilité : best-effort (n'empêche pas l'affichage du profil).
    apiService.getMyMobilite().then((m) => { mobilite.value = m }).catch(() => { mobilite.value = [] })
  } catch {
    error.value = 'Impossible de charger votre profil.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const stars = (n: number) => '★★★★★'.slice(0, n) + '☆☆☆☆☆'.slice(0, 5 - n)

// Passerelle de mobilité : clic → description + direction (offres correspondantes).
const router = useRouter()
const selMob = ref<MobiliteItem | null>(null)
const showMob = computed({
  get: () => selMob.value !== null,
  set: (v: boolean) => { if (!v) selMob.value = null },
})
function mobDesc(m: MobiliteItem): string {
  return `« ${m.metier} » ressort comme une évolution possible : vous partagez déjà ${m.partagees} `
    + `compétence${m.partagees > 1 ? 's' : ''} clé${m.partagees > 1 ? 's' : ''} avec ce métier, `
    + `identifiée${m.partagees > 1 ? 's' : ''} via le référentiel ${m.source.toUpperCase()}. `
    + `Explorez les offres internes correspondantes pour envisager cette passerelle.`
}
function goOffres(metier: string) {
  selMob.value = null
  router.push({ name: 'collab.offres', query: { q: metier } })
}
</script>

<template>
  <LoadingState v-if="loading" label="Chargement de votre profil…" />
  <ErrorState v-else-if="error" :message="error">
    <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
  </ErrorState>

  <div v-else-if="profile" class="space-y-5">
    <BaseCard>
      <div class="flex flex-wrap items-center gap-4">
        <BaseAvatar :initials="session.user?.initials || 'YE'" size="xl" :photo="session.user?.photo" />
        <div class="min-w-0 flex-1">
          <h2 class="font-display text-xl font-bold text-ink">{{ session.user?.name || 'Youssef El Amrani' }}</h2>
          <p class="text-sm text-ink-3">{{ session.user?.title }} · {{ session.user?.entity }}</p>
          <p class="mt-2 max-w-2xl text-sm text-ink-2">{{ profile.description }}</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <RouterLink :to="{ name: 'collab.editProfil' }">
            <BaseButton variant="secondary">
              <AppIcon name="user" :size="15" /> Éditer mon profil
            </BaseButton>
          </RouterLink>
        </div>
      </div>
    </BaseCard>

    <BaseCard><ProgressionCurve :stations="profile.stations" :pct="profile.progressionPct" /></BaseCard>

    <div class="grid gap-5 lg:grid-cols-[1fr_340px]">
      <div class="space-y-5">
        <BaseCard title="Mes compétences">
          <div class="space-y-3">
            <div v-for="s in byPctDesc(profile.skills)" :key="s.label">
              <div class="mb-1 flex items-center justify-between text-sm">
                <span class="text-ink-2">{{ s.label }}</span>
                <b v-if="s.evaluee !== false" :class="scoreText(s.pct)">{{ s.pct }} %</b>
                <span v-else class="rounded-full bg-panel-2 px-2 py-0.5 text-[11px] font-semibold text-ink-3">En attente d'évaluation</span>
              </div>
              <div v-if="s.evaluee !== false" class="h-2 overflow-hidden rounded-full bg-panel-2">
                <div class="h-full rounded-full" :class="scoreBar(s.pct)" :style="{ width: s.pct + '%' }" />
              </div>
            </div>
          </div>
          <div class="mt-4"><ScoringInfo /></div>
        </BaseCard>

        <BaseCard title="Avis des pairs">
          <div class="space-y-4">
            <div v-for="(r, i) in profile.peerReviews" :key="i" class="flex gap-3">
              <BaseAvatar :initials="r.initials" size="sm" />
              <div>
                <p class="text-sm text-ink-2">« {{ r.text }} »</p>
                <div class="mt-0.5 text-xs text-ink-3">
                  <span class="text-gold">{{ stars(r.stars) }}</span> {{ r.name }} · {{ r.role }}
                </div>
              </div>
            </div>
          </div>
        </BaseCard>
      </div>

      <div class="space-y-5">
        <BaseCard title="Poste visé & aspirations">
          <div class="flex gap-3 rounded-xl border border-green-line bg-green-soft p-3.5">
            <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green text-white"><AppIcon name="route" :size="16" /></div>
            <div>
              <h4 class="text-sm font-bold text-green-deep">{{ profile.posteVise }}</h4>
              <p class="text-xs text-ink-2">
                Horizon {{ profile.horizon }}<span v-if="profile.typeEvolution"> · {{ profile.typeEvolution }}</span>
              </p>
            </div>
          </div>
          <div class="mt-3 flex flex-wrap gap-2">
            <BaseChip v-for="a in profile.aspirations" :key="a" tone="green">{{ a }}</BaseChip>
          </div>
          <p class="mt-3 text-xs text-ink-3">
            <AppIcon name="pin" :size="12" class="inline" /> Zones · {{ profile.zones }}<span v-if="profile.disponibilite"> · Dispo {{ profile.disponibilite }}</span>
          </p>
          <RouterLink :to="{ name: 'collab.souhaits' }" class="mt-3 block">
            <BaseButton variant="ai" block><AppIcon name="route" :size="15" /> Mes demandes d'évolution</BaseButton>
          </RouterLink>
        </BaseCard>

        <BaseCard v-if="mobilite.length" title="Passerelles de mobilité">
          <p class="mb-2.5 text-xs text-ink-3">Métiers proches de vos compétences détenues (graphe ESCO/O*NET). Cliquez pour en savoir plus.</p>
          <ul class="space-y-2">
            <li v-for="m in mobilite" :key="m.id">
              <button
                type="button"
                class="flex w-full items-center justify-between gap-2 rounded-xl border border-border bg-panel-2 px-3 py-2 text-left transition hover:border-green-line hover:bg-green-ghost"
                @click="selMob = m"
              >
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold text-ink">{{ m.metier }}</p>
                  <p class="text-xs uppercase tracking-wide text-ink-3">{{ m.source }}</p>
                </div>
                <span
                  class="inline-flex shrink-0 items-center justify-center rounded-full bg-green-soft px-2.5 py-1 text-[11px] font-semibold text-green-deep"
                  style="min-width: 96px"
                >{{ m.partagees }} en commun</span>
              </button>
            </li>
          </ul>
        </BaseCard>

        <div class="flex gap-3 rounded-2xl border border-green-line bg-green-ghost p-4">
          <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green text-white"><Sparkles :size="16" /></div>
          <div>
            <h4 class="text-sm font-bold text-green-deep">Recommandations personnalisées</h4>
            <p class="mt-0.5 text-xs text-ink-2">Découvrez les passerelles vers votre objectif.</p>
            <RouterLink :to="{ name: 'collab.reco' }" class="mt-2 inline-block text-xs font-semibold text-green-deep hover:underline">Voir les recommandations →</RouterLink>
          </div>
        </div>
      </div>
    </div>

    <BaseModal v-model="showMob" :title="selMob?.metier || 'Passerelle de mobilité'">
      <div v-if="selMob" class="space-y-3">
        <div class="flex flex-wrap items-center gap-2">
          <BaseChip tone="green">{{ selMob.partagees }} compétences en commun</BaseChip>
          <BaseChip>{{ selMob.source.toUpperCase() }}</BaseChip>
        </div>
        <p class="text-sm leading-relaxed text-ink-2">{{ mobDesc(selMob) }}</p>
      </div>
      <template #footer>
        <BaseButton variant="secondary" size="sm" @click="showMob = false">Fermer</BaseButton>
        <BaseButton size="sm" @click="goOffres(selMob!.metier)">
          <AppIcon name="search" :size="14" /> Voir les offres
        </BaseButton>
      </template>
    </BaseModal>
  </div>
</template>
