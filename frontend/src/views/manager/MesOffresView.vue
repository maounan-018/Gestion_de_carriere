<script setup lang="ts">
/**
 * « Mes offres publiées » — les offres CRÉÉES par le compte courant (manager /
 * HRBP), atteint depuis le KPI « Offres publiées » du tableau de bord (et non
 * l'écran des offres internes). Chaque offre montre son statut et ses
 * statistiques de candidatures, et mène à son détail.
 */
import { ref, computed, onMounted } from 'vue'
import { Plus } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { useSessionStore } from '@/stores/session'
import type { RhOffer } from '@/data/rh'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import PublishOffreModal from '@/components/shared/PublishOffreModal.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const offers = ref<RhOffer[]>([])
const loading = ref(true)
const error = ref('')
const showPublish = ref(false)
// Vue partagée manager / HRBP : le détail d'offre et le type publiable dépendent du rôle.
const isRh = computed(() => useSessionStore().role === 'rh')
const offreDetailRoute = computed(() => (isRh.value ? 'rh.revueCandidats' : 'manager.revueCandidats'))

async function load() {
  loading.value = true
  error.value = ''
  try {
    offers.value = await apiService.getMesOffres()
  } catch {
    error.value = 'Impossible de charger vos offres.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const statusTone: Record<RhOffer['status'], 'new' | 'ai' | 'warn' | 'mut'> = {
  ouvert: 'new', validation: 'warn', brouillon: 'mut', 'clôturé': 'mut',
}
const statusLabel: Record<RhOffer['status'], string> = {
  ouvert: 'Diffusée', validation: 'En validation', brouillon: 'Brouillon', 'clôturé': 'Clôturée',
}
</script>

<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div>
        <h2 class="font-display text-2xl font-bold text-ink">Mes offres publiées</h2>
        <p class="text-sm text-ink-3">Les offres que vous avez créées · statut et candidatures.</p>
      </div>
      <BaseButton size="sm" @click="showPublish = true"><Plus :size="15" /> Publier une offre</BaseButton>
    </div>

    <LoadingState v-if="loading" label="Chargement de vos offres…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>
    <EmptyState
      v-else-if="!offers.length"
      title="Aucune offre publiée"
      text="Publiez une mission, un projet ou un poste : elle apparaîtra ici avec ses candidatures."
    />

    <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <RouterLink
        v-for="o in offers"
        :key="o.key"
        :to="{ name: offreDetailRoute, params: { key: o.key } }"
        class="flex flex-col rounded-2xl border border-border bg-paper p-4 shadow-card transition hover:-translate-y-0.5 hover:border-green-line hover:shadow-float"
      >
        <div class="flex items-start justify-between gap-2">
          <BasePill tone="ai">{{ o.type }}</BasePill>
          <BasePill :tone="statusTone[o.status]">{{ statusLabel[o.status] }}</BasePill>
        </div>
        <h4 class="mt-2 text-sm font-bold text-ink">{{ o.title }}</h4>
        <p class="mt-0.5 text-xs text-ink-3">{{ o.ligne }}</p>
        <div class="mt-3 flex-1" />
        <div class="mt-2 flex items-center justify-between border-t border-border pt-2.5 text-xs text-ink-3">
          <span><b class="text-ink-2">{{ o.candidates }}</b> candidat{{ o.candidates > 1 ? 's' : '' }}</span>
          <span><b class="text-green-deep">{{ o.compatible }}</b> compatible{{ o.compatible > 1 ? 's' : '' }}</span>
        </div>
        <p v-if="o.retenu" class="mt-1 text-[11px] text-ink-3">Retenu : <b class="text-ink-2">{{ o.retenu }}</b></p>
      </RouterLink>
    </div>

    <PublishOffreModal v-model="showPublish" :allow-poste="isRh" @published="load" />
  </div>
</template>
