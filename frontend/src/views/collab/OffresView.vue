<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Search } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import type { Offer } from '@/types/domain'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const route = useRoute()
const offers = ref<Offer[]>([])
const loading = ref(true)
const error = ref('')
// Recherche pré-remplie si on arrive depuis une passerelle de mobilité (?q=métier).
const query = ref(typeof route.query.q === 'string' ? route.query.q : '')
const ligne = ref<string>('Tout')

async function load() {
  loading.value = true
  error.value = ''
  try {
    offers.value = await apiService.getOffers()
  } catch {
    error.value = 'Impossible de charger les offres internes.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

// Filtres dérivés des offres réellement chargées → jamais de filtre « vide »
// (les valeurs de `ligne` proviennent du backend, pas d'une liste figée).
const OFFER_LIGNES = computed(() => {
  const lignes = [...new Set(offers.value.map((o) => o.ligne).filter(Boolean))].sort()
  return ['Tout', ...lignes]
})

const ligneFiltered = computed(() =>
  offers.value.filter((o) => ligne.value === 'Tout' || o.ligne === ligne.value),
)
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  return ligneFiltered.value.filter(
    (o) => !q || (o.title + ' ' + o.sub + ' ' + o.skills.join(' ')).toLowerCase().includes(q),
  )
})
// Depuis une passerelle, la recherche par métier ne correspond pas toujours à un
// intitulé d'offre. Plutôt qu'une page vide, on RETOMBE sur les vraies offres ouvertes
// (aucune offre fabriquée) avec un avis clair · toutes les offres affichées existent.
const noMatch = computed(
  () => !!query.value.trim() && filtered.value.length === 0 && offers.value.length > 0,
)
const displayed = computed(() => (noMatch.value ? ligneFiltered.value : filtered.value))
</script>

<template>
  <div class="space-y-4">
    <!-- Barre d'outils -->
    <div class="flex flex-wrap items-center gap-2">
      <div class="flex min-w-56 flex-1 items-center gap-2 rounded-xl border border-border bg-paper px-3 py-2">
        <Search :size="16" class="text-ink-3" />
        <input
          v-model="query"
          type="search"
          placeholder="Rechercher un métier, une compétence, une ville…"
          class="w-full bg-transparent text-sm outline-none placeholder:text-ink-3"
        />
      </div>
      <RouterLink :to="{ name: 'collab.mesCandidatures' }">
        <BaseButton variant="secondary"><AppIcon name="send" :size="15" /> Mes candidatures</BaseButton>
      </RouterLink>
    </div>

    <!-- Filtres par ligne métier -->
    <div class="flex flex-wrap gap-2">
      <button
        v-for="f in OFFER_LIGNES"
        :key="f"
        class="rounded-full border px-3 py-1 text-xs font-semibold transition"
        :class="ligne === f
          ? 'border-green bg-green text-white'
          : 'border-border bg-paper text-ink-2 hover:border-green-line hover:text-green-deep'"
        @click="ligne = f"
      >
        {{ f }}
      </button>
    </div>

    <p class="text-xs text-ink-3">
      Offres classées par <b class="text-ink-2">adéquation</b> avec votre profil · baromètre vert à
      gauche de chaque carte.
    </p>

    <LoadingState v-if="loading" label="Chargement des offres…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>
    <EmptyState
      v-else-if="displayed.length === 0"
      title="Aucune offre ouverte"
      text="Aucune offre interne n'est ouverte pour ce filtre actuellement."
    />

    <template v-else>
      <div v-if="noMatch" class="flex items-start gap-2.5 rounded-xl border border-green-line bg-green-soft p-3 text-xs text-ink-2">
        <AppIcon name="search" :size="15" class="mt-0.5 shrink-0 text-green-deep" />
        <span>
          Aucune offre interne ne correspond exactement à <b class="text-ink">« {{ query }} »</b>.
          Voici les offres internes actuellement ouvertes · explorez celles proches de votre projet.
        </span>
      </div>

    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <RouterLink
        v-for="o in displayed"
        :key="o.key"
        :to="{ name: 'collab.offreDetail', params: { key: o.key } }"
        class="group flex flex-col rounded-2xl border border-border bg-paper p-4 shadow-card transition hover:-translate-y-0.5 hover:border-green-line hover:shadow-float"
      >
        <div class="flex items-start justify-between gap-2">
          <BasePill :tone="o.tone">{{ o.type }}</BasePill>
          <div class="text-right">
            <div class="font-display text-[15px] font-bold text-green-deep">{{ o.pct }} %</div>
            <div class="text-[10px] text-ink-3">{{ o.adq }}</div>
          </div>
        </div>
        <div class="my-2 h-1.5 overflow-hidden rounded-full bg-panel-2">
          <div class="h-full rounded-full bg-green" :style="{ width: o.pct + '%' }" />
        </div>
        <h4 class="text-sm font-bold text-ink group-hover:text-green-deep">{{ o.title }}</h4>
        <p class="mt-0.5 text-xs text-ink-3">{{ o.sub }}</p>
        <div class="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-ink-3">
          <span v-for="(m, i) in o.meta" :key="i" class="inline-flex items-center gap-1">
            <AppIcon :name="m.icon" :size="12" /> {{ m.label }}
          </span>
        </div>
        <div class="mt-3 flex items-center gap-1.5 text-[11px]" :class="o.managerInformed ? 'text-warning' : 'text-ink-3'">
          <AppIcon :name="o.managerInformed ? 'bell' : 'shield'" :size="12" />
          {{ o.managerInformed ? 'Manager informé si vous postulez' : 'Candidature confidentielle' }}
        </div>
        <div class="mt-3 flex-1" />
        <div class="mt-2">
          <BaseButton size="sm" block>{{ o.cta }}</BaseButton>
        </div>
      </RouterLink>
    </div>
    </template>
  </div>
</template>
