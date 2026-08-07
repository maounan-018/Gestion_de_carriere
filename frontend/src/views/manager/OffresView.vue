<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Plus } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { MANAGER_PEUT_PUBLIER } from '@/config/features'
import type { Offer, Besoin } from '@/types/domain'
import type { Vacancy } from '@/types/manager'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import PublishOffreModal from '@/components/shared/PublishOffreModal.vue'
import BesoinModal from '@/components/shared/BesoinModal.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const offers = ref<Offer[]>([])
const vacancies = ref<Vacancy[]>([])
const besoins = ref<Besoin[]>([])
const loading = ref(true)
const error = ref('')
const ligne = ref<string>('Tout')

async function load() {
  loading.value = true
  error.value = ''
  try {
    ;[offers.value, vacancies.value, besoins.value] = await Promise.all([
      apiService.getManagerOffers(),
      apiService.getVacancies(),
      apiService.getMesBesoins(),
    ])
  } catch {
    error.value = 'Impossible de charger les offres.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

// Suivi des besoins de recrutement (workflow manager → HRBP).
const besoinTone: Record<Besoin['statut'], 'new' | 'ai' | 'warn' | 'mut'> = {
  transmis: 'warn', valide: 'ai', publie: 'new', refuse: 'mut',
}
const besoinLabel: Record<Besoin['statut'], string> = {
  transmis: 'Transmis à la HRBP', valide: 'Validé', publie: 'Offre publiée', refuse: 'Non retenu',
}

// Filtres dérivés des offres réellement chargées (plus de liste figée → jamais vide).
const MANAGER_OFFER_LIGNES = computed(() => {
  const lignes = [...new Set(offers.value.map((o) => o.ligne).filter(Boolean))].sort()
  return ['Tout', ...lignes]
})

const filtered = computed(() =>
  offers.value.filter((o) => ligne.value === 'Tout' || o.ligne === ligne.value),
)

// Publication directe : réservée si le flag est réactivé (sinon → besoin de recrutement).
const showPublish = ref(false)
const showBesoin = ref(false)

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
      <BaseButton v-if="MANAGER_PEUT_PUBLIER" size="sm" @click="showPublish = true">
        <Plus :size="15" /> Publier une offre
      </BaseButton>
      <BaseButton v-else size="sm" @click="showBesoin = true">
        <Plus :size="15" /> Exprimer un besoin de recrutement
      </BaseButton>
    </div>

    <LoadingState v-if="loading" label="Chargement des offres…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <template v-else>
      <!-- Mes besoins de recrutement (workflow manager → HRBP) -->
      <div v-if="!MANAGER_PEUT_PUBLIER">
        <h3 class="mb-2 font-display text-base font-bold text-ink">
          Mes besoins de recrutement <span class="text-sm font-normal text-ink-3">· transmis à la HRBP</span>
        </h3>
        <div v-if="!besoins.length" class="rounded-2xl border border-dashed border-border bg-paper p-4 text-sm text-ink-3">
          Aucun besoin exprimé. Cliquez « Exprimer un besoin de recrutement » pour transmettre un besoin à la HRBP.
        </div>
        <div v-else class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <component
            :is="b.offreId ? 'RouterLink' : 'div'"
            v-for="b in besoins"
            :key="b.id"
            :to="b.offreId ? { name: 'manager.mesOffres' } : undefined"
            class="block rounded-2xl border border-border bg-paper p-4 shadow-card"
            :class="b.offreId ? 'transition hover:-translate-y-0.5 hover:border-green-line hover:shadow-float' : ''"
          >
            <div class="flex items-start justify-between gap-2">
              <BasePill :tone="besoinTone[b.statut]">{{ besoinLabel[b.statut] }}</BasePill>
            </div>
            <h4 class="mt-2 text-sm font-bold text-ink">{{ b.poste }}</h4>
            <p v-if="b.description" class="mt-0.5 line-clamp-2 text-xs text-ink-3">{{ b.description }}</p>
            <p v-if="b.statut === 'publie'" class="mt-2 text-[11px] font-semibold text-green-deep">
              Offre publiée → suivre les candidatures
            </p>
            <p v-else-if="b.statut === 'refuse' && b.motifRefus" class="mt-2 text-[11px] text-ink-3">
              Motif : {{ b.motifRefus }}
            </p>
          </component>
        </div>
      </div>

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
              <RouterLink
                v-if="v.status === 'clôturé'"
                :to="{ name: 'manager.evaluationMission', params: { key: v.key } }"
              >
                <BaseButton size="sm">Évaluer les participants</BaseButton>
              </RouterLink>
              <RouterLink v-else :to="{ name: 'manager.profilsCompatibles', params: { key: v.key } }">
                <BaseButton size="sm" variant="secondary">Voir les profils</BaseButton>
              </RouterLink>
            </div>
          </div>
        </div>
      </div>
    </template>

    <PublishOffreModal v-if="MANAGER_PEUT_PUBLIER" v-model="showPublish" :allow-poste="false" @published="load" />
    <BesoinModal v-model="showBesoin" @created="load" />
  </div>
</template>
