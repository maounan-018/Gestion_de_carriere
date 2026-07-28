<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from 'lucide-vue-next'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { RhOffer } from '@/data/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
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

// Publier une offre (RH) — la RH peut publier tous les types, POSTES inclus.
const showPublish = ref(false)
const publishing = ref(false)
const pubType = ref<'Poste' | 'Mission transverse' | 'Projet innovation'>('Poste')
const pubTitle = ref('')
async function publish() {
  if (publishing.value || !pubTitle.value.trim()) return
  publishing.value = true
  try {
    await apiService.publishOffer({ titre: pubTitle.value.trim(), type: pubType.value })
    showPublish.value = false
    toast('Offre créée en brouillon')
    pubTitle.value = ''
    await load()
  } catch (e) {
    toast(e instanceof Error ? e.message : 'Échec de la publication', 'error')
  } finally {
    publishing.value = false
  }
}

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
          <BaseButton v-if="o.retenu" size="sm" variant="secondary" @click="goCandidats(o.key)">
            Candidat retenu
          </BaseButton>
          <BaseButton v-else-if="o.candidates > 0" size="sm" variant="secondary" @click="goCandidats(o.key)">
            Voir les candidats
          </BaseButton>
        </div>
      </BaseCard>
    </div>

    <BaseModal v-model="showPublish" title="Publier une offre">
      <div class="space-y-4">
        <div>
          <label class="mb-1.5 block text-xs font-semibold text-ink-2">Type</label>
          <div class="grid grid-cols-3 gap-1.5">
            <button
              v-for="t in (['Poste', 'Mission transverse', 'Projet innovation'] as const)"
              :key="t"
              type="button"
              class="rounded-lg border px-2 py-1.5 text-xs font-semibold transition"
              :class="pubType === t
                ? 'border-green bg-green text-white'
                : 'border-border bg-paper text-ink-2 hover:text-ink'"
              @click="pubType = t"
            >
              {{ t }}
            </button>
          </div>
        </div>
        <div>
          <label for="rh-pub-title" class="mb-1.5 block text-xs font-semibold text-ink-2">Intitulé</label>
          <input
            id="rh-pub-title"
            v-model="pubTitle"
            placeholder="Ex : Responsable Conformité"
            class="w-full rounded-xl border border-border bg-paper px-3 py-2 text-sm outline-none focus:border-green-line"
          />
        </div>
        <div class="flex items-start gap-2 rounded-xl border border-green-line bg-green-ghost px-3 py-2 text-xs text-green-deep">
          <AppIcon name="shield" :size="14" />
          <span>La RH publie tous les types d'offres, <b>postes</b> inclus. L'offre est créée en <b>brouillon</b>.</span>
        </div>
      </div>
      <template #footer>
        <BaseButton variant="secondary" size="sm" @click="showPublish = false">Annuler</BaseButton>
        <BaseButton size="sm" :disabled="!pubTitle.trim() || publishing" @click="publish">
          <AppIcon name="send" :size="14" /> {{ publishing ? 'Publication…' : 'Publier' }}
        </BaseButton>
      </template>
    </BaseModal>
  </div>
</template>
