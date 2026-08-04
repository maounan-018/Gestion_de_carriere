<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Plus } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import type { Offer } from '@/types/domain'
import type { Vacancy } from '@/types/manager'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import PublishOffreModal from '@/components/shared/PublishOffreModal.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const offers = ref<Offer[]>([])
const vacancies = ref<Vacancy[]>([])
const loading = ref(true)
const error = ref('')
const ligne = ref<string>('Tout')

async function load() {
  loading.value = true
  error.value = ''
  try {
    ;[offers.value, vacancies.value] = await Promise.all([
      apiService.getManagerOffers(),
      apiService.getVacancies(),
    ])
  } catch {
    error.value = 'Impossible de charger les offres.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

// Filtres dérivés des offres réellement chargées (plus de liste figée → jamais vide).
const MANAGER_OFFER_LIGNES = computed(() => {
  const lignes = [...new Set(offers.value.map((o) => o.ligne).filter(Boolean))].sort()
  return ['Tout', ...lignes]
})

const filtered = computed(() =>
  offers.value.filter((o) => ligne.value === 'Tout' || o.ligne === ligne.value),
)

// Publier une offre — formulaire riche partagé (fiche de poste + détails).
// Un manager publie des missions/projets ; les POSTES relèvent de la RH (allowPoste=false).
const showPublish = ref(false)

const statusTone: Record<string, 'new' | 'ai' | 'warn' | 'mut'> = {
  ouvert: 'new', validation: 'warn', brouillon: 'mut', 'clôturé': 'mut',
}
const statusLabel: Record<string, string> = {
  ouvert: 'Diffusé', validation: 'En validation RH', brouillon: 'Brouillon', 'clôturé': 'Clôturé',
}
</script>

<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex flex-wrap gap-2">
        <button
          v-for="f in MANAGER_OFFER_LIGNES"
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
      <BaseButton size="sm" @click="showPublish = true"><Plus :size="15" /> Publier une offre</BaseButton>
    </div>

    <LoadingState v-if="loading" label="Chargement des offres…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <template v-else>
      <!-- Ma mobilité -->
      <div>
        <h3 class="mb-2 font-display text-base font-bold text-ink">
          Ma mobilité <span class="text-sm font-normal text-ink-3">· opportunités de niveau dirigeant</span>
        </h3>
        <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <RouterLink
            v-for="o in filtered"
            :key="o.key"
            :to="{ name: 'manager.offreDetail', params: { key: o.key } }"
            class="group flex flex-col rounded-2xl border border-border bg-paper p-4 shadow-card transition hover:-translate-y-0.5 hover:border-green-line hover:shadow-float"
          >
            <div class="flex items-start justify-between gap-2">
              <BasePill :tone="o.tone">{{ o.type }}</BasePill>
              <div class="text-right">
                <div class="font-display text-[15px] font-bold text-green-deep">{{ o.pct }}%</div>
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
            <div class="mt-3 flex-1" />
            <BaseButton size="sm" block class="mt-2">{{ o.cta }}</BaseButton>
          </RouterLink>
        </div>
      </div>

      <!-- Postes de l'équipe -->
      <div>
        <h3 class="mb-2 font-display text-base font-bold text-ink">
          Postes de mon équipe <span class="text-sm font-normal text-ink-3">· profils internes recommandés</span>
        </h3>
        <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <div
            v-for="v in vacancies"
            :key="v.key"
            class="flex flex-col rounded-2xl border border-border bg-paper p-4 shadow-card"
          >
            <div class="flex items-start justify-between gap-2">
              <BasePill :tone="statusTone[v.status]">{{ statusLabel[v.status] }}</BasePill>
              <span class="text-[11px] text-ink-3">{{ v.openSince }}</span>
            </div>
            <h4 class="mt-2 text-sm font-bold text-ink">{{ v.title }}</h4>
            <p class="mt-0.5 text-xs text-ink-3">{{ v.sub }}</p>
            <div class="mt-2 flex-1" />
            <div class="mt-2 flex items-center justify-between gap-2">
              <span class="text-xs text-ink-3">
                <b class="text-ink-2">{{ v.recos.length }}</b> profil{{ v.recos.length > 1 ? 's' : '' }} recommandé{{ v.recos.length > 1 ? 's' : '' }}
              </span>
              <RouterLink :to="{ name: 'manager.profilsCompatibles', params: { key: v.key } }">
                <BaseButton size="sm" variant="secondary">Voir les profils</BaseButton>
              </RouterLink>
            </div>
          </div>
        </div>
      </div>
    </template>

    <PublishOffreModal v-model="showPublish" :allow-poste="false" @published="load" />
  </div>
</template>
