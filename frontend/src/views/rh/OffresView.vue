<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { RhOffer } from '@/data/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import PublishOffreModal from '@/components/shared/PublishOffreModal.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const offers = ref<RhOffer[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()
const router = useRouter()

function goCandidats(key: string) {
  router.push({ name: 'rh.revueCandidats', params: { key } })
}

// Cycle de vie : transition de statut d'une offre (PATCH /offres/{id}).
const busyKey = ref<string | null>(null)
async function changeStatut(o: RhOffer, statut: 'ouverte' | 'pourvue' | 'fermee', label: string) {
  if (busyKey.value) return
  busyKey.value = o.key
  try {
    await apiService.updateOffreStatut(o.key, statut)
    toast(label, 'ok')
    await load()
  } catch (e) {
    toast(e instanceof Error ? e.message : 'Échec de la transition', 'error')
  } finally {
    busyKey.value = null
  }
}

// Publier une offre (RH) — formulaire riche partagé (fiche de poste + détails).
const showPublish = ref(false)

async function load() {
  loading.value = true
  error.value = ''
  try {
    offers.value = await apiService.getRhOffers()
  } catch {
    error.value = 'Impossible de charger les offres.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const inValidation = computed(() => offers.value.filter((o) => o.status === 'validation').length)

const statusTone: Record<string, 'new' | 'warn' | 'mut'> = {
  ouvert: 'new', validation: 'warn', brouillon: 'mut', 'clôturé': 'mut',
}
const statusLabel: Record<string, string> = {
  ouvert: 'Diffusée', validation: 'En validation finale', brouillon: 'Brouillon', 'clôturé': 'Clôturée',
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <p class="text-sm text-ink-3">
        Offres du Groupe · <b class="text-ink-2">{{ inValidation }} en validation finale</b>.
      </p>
      <BaseButton size="sm" @click="showPublish = true">
        <Plus :size="15" /> Publier une offre
      </BaseButton>
    </div>

    <LoadingState v-if="loading" label="Chargement des offres…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <div v-else class="space-y-3">
      <BaseCard v-for="o in offers" :key="o.key">
        <div class="flex flex-wrap items-center gap-3">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <h4 class="text-sm font-bold text-ink">{{ o.title }}</h4>
              <BasePill :tone="statusTone[o.status]">{{ statusLabel[o.status] }}</BasePill>
              <span class="text-xs text-ink-3">{{ o.type }} · {{ o.ligne }}</span>
            </div>
            <div class="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-3">
              <span><b class="text-ink-2">{{ o.candidates }}</b> candidats</span>
              <span><b class="text-green-deep">{{ o.compatible }}</b> compatibles</span>
              <span v-if="o.retenu">Retenu : <b class="text-ink">{{ o.retenu }}</b></span>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <!-- Cycle de vie -->
            <BaseButton
              v-if="o.status === 'brouillon'"
              size="sm"
              :disabled="busyKey === o.key"
              @click="changeStatut(o, 'ouverte', 'Offre diffusée')"
            >
              <AppIcon name="send" :size="14" /> Diffuser
            </BaseButton>
            <template v-else-if="o.status === 'ouvert'">
              <BaseButton
                size="sm"
                variant="secondary"
                :disabled="busyKey === o.key"
                @click="changeStatut(o, 'pourvue', 'Offre marquée pourvue')"
              >
                Marquer pourvue
              </BaseButton>
              <BaseButton
                size="sm"
                variant="ghost"
                :disabled="busyKey === o.key"
                @click="changeStatut(o, 'fermee', 'Offre clôturée')"
              >
                Clôturer
              </BaseButton>
            </template>
            <!-- Candidats -->
            <BaseButton v-if="o.retenu" size="sm" variant="secondary" @click="goCandidats(o.key)">
              Candidat retenu
            </BaseButton>
            <BaseButton v-else-if="o.candidates > 0" size="sm" variant="secondary" @click="goCandidats(o.key)">
              Voir les candidats
            </BaseButton>
          </div>
        </div>
      </BaseCard>
    </div>

    <PublishOffreModal v-model="showPublish" @published="load" />
  </div>
</template>
