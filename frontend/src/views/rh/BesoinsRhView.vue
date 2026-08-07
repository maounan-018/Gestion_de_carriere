<script setup lang="ts">
/**
 * Besoins de recrutement (HRBP) — les besoins exprimés par les managers. La HRBP
 * valide / refuse, puis PUBLIE l'offre en continuité (le manager d'origine garde
 * la visibilité sur les candidatures via `Offre.manager_id`).
 */
import { ref, computed, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { Besoin } from '@/types/domain'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const { toast } = useToast()
const besoins = ref<Besoin[]>([])
const loading = ref(true)
const error = ref('')
const busy = ref<number | null>(null)

async function load() {
  loading.value = true
  error.value = ''
  try {
    besoins.value = await apiService.getBesoins()
  } catch {
    error.value = 'Impossible de charger les besoins.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

// Actionnables d'abord (transmis, validé), puis publiés / refusés.
const ordreStatut: Record<Besoin['statut'], number> = { transmis: 0, valide: 1, publie: 2, refuse: 3 }
const tries = computed(() =>
  [...besoins.value].sort((a, b) => ordreStatut[a.statut] - ordreStatut[b.statut]))

const tone: Record<Besoin['statut'], 'new' | 'ai' | 'warn' | 'mut'> = {
  transmis: 'warn', valide: 'ai', publie: 'new', refuse: 'mut',
}
const label: Record<Besoin['statut'], string> = {
  transmis: 'À traiter', valide: 'Validé', publie: 'Offre publiée', refuse: 'Refusé',
}

async function action(fn: () => Promise<void>, id: number, ok: string) {
  if (busy.value) return
  busy.value = id
  try {
    await fn()
    toast(ok, 'ok')
    await load()
  } catch (e) {
    toast(e instanceof Error ? e.message : 'Action impossible', 'error')
  } finally {
    busy.value = null
  }
}

const valider = (b: Besoin) => action(() => apiService.validerBesoin(b.id), b.id, 'Besoin validé')
const publier = (b: Besoin) => action(() => apiService.publierBesoin(b.id), b.id, 'Offre publiée')
function refuser(b: Besoin) {
  const motif = window.prompt('Motif du refus (facultatif) :') ?? undefined
  action(() => apiService.refuserBesoin(b.id, motif), b.id, 'Besoin refusé')
}
</script>

<template>
  <div class="space-y-5">
    <div>
      <h2 class="font-display text-2xl font-bold text-ink">Besoins de recrutement</h2>
      <p class="text-sm text-ink-3">Besoins exprimés par les managers · validez et publiez l'offre en continuité.</p>
    </div>

    <LoadingState v-if="loading" label="Chargement des besoins…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>
    <EmptyState
      v-else-if="!besoins.length"
      title="Aucun besoin de recrutement"
      text="Les besoins exprimés par les managers apparaîtront ici."
    />

    <div v-else class="space-y-3">
      <div
        v-for="b in tries"
        :key="b.id"
        class="rounded-2xl border border-border bg-paper p-4 shadow-card"
      >
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <BasePill :tone="tone[b.statut]">{{ label[b.statut] }}</BasePill>
              <span class="text-xs text-ink-3">Demandé par {{ b.managerNom || 'un manager' }}</span>
            </div>
            <RouterLink :to="{ name: 'rh.besoinDetail', params: { id: b.id } }"
              class="mt-1.5 block text-sm font-bold text-ink hover:text-green-deep hover:underline">
              {{ b.poste }}
            </RouterLink>
            <p v-if="b.description" class="mt-0.5 line-clamp-2 text-xs text-ink-2">{{ b.description }}</p>
            <p v-if="b.statut === 'refuse' && b.motifRefus" class="mt-1 text-[11px] text-ink-3">
              Motif : {{ b.motifRefus }}
            </p>
          </div>
          <div class="flex shrink-0 flex-wrap items-center gap-2">
            <template v-if="b.statut === 'transmis' || b.statut === 'valide'">
              <BaseButton size="sm" :disabled="busy === b.id" @click="publier(b)">Publier l'offre</BaseButton>
              <BaseButton
                v-if="b.statut === 'transmis'"
                variant="secondary" size="sm" :disabled="busy === b.id" @click="valider(b)"
              >Valider</BaseButton>
              <BaseButton variant="secondary" size="sm" :disabled="busy === b.id" @click="refuser(b)">Refuser</BaseButton>
            </template>
            <RouterLink
              v-else-if="b.statut === 'publie' && b.offreId"
              :to="{ name: 'rh.revueCandidats', params: { key: String(b.offreId) } }"
            >
              <BaseButton size="sm" variant="secondary">Voir les candidatures</BaseButton>
            </RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
