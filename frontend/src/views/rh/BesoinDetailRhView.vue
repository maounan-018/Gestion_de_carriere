<script setup lang="ts">
/**
 * Détail d'un besoin de recrutement (HRBP) — toutes les infos (description longue),
 * actions (valider / refuser / publier l'offre) et « Contacter le manager » émetteur.
 * Atteint depuis l'écran des besoins (ou la notification).
 */
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { Besoin } from '@/types/domain'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const route = useRoute()
const router = useRouter()
const { toast } = useToast()
const besoin = ref<Besoin | null>(null)
const loading = ref(true)
const error = ref('')
const busy = ref(false)
const showContact = ref(false)
const contactMsg = ref('')

const tone: Record<Besoin['statut'], 'new' | 'ai' | 'warn' | 'mut'> = {
  transmis: 'warn', valide: 'ai', publie: 'new', refuse: 'mut',
}
const label: Record<Besoin['statut'], string> = {
  transmis: 'À traiter', valide: 'Validé', publie: 'Offre publiée', refuse: 'Refusé',
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    besoin.value = await apiService.getBesoin(Number(route.params.id))
  } catch {
    error.value = 'Impossible de charger le besoin.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function run(fn: () => Promise<void>, ok: string) {
  if (busy.value || !besoin.value) return
  busy.value = true
  try {
    await fn()
    toast(ok, 'ok')
    await load()
  } catch (e) {
    toast(e instanceof Error ? e.message : 'Action impossible', 'error')
  } finally {
    busy.value = false
  }
}
const valider = () => run(() => apiService.validerBesoin(besoin.value!.id), 'Besoin validé')
const publier = () => run(() => apiService.publierBesoin(besoin.value!.id), 'Offre publiée')
function refuser() {
  const motif = window.prompt('Motif du refus (facultatif) :') ?? undefined
  run(() => apiService.refuserBesoin(besoin.value!.id, motif), 'Besoin refusé')
}
async function envoyerContact() {
  if (!contactMsg.value.trim() || !besoin.value) return
  await run(() => apiService.contacterManagerBesoin(besoin.value!.id, contactMsg.value.trim()),
            'Message envoyé au manager')
  showContact.value = false
  contactMsg.value = ''
}
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-4">
    <BaseBreadcrumb
      :items="[{ label: 'Besoins de recrutement', to: { name: 'rh.besoins' } }, { label: besoin?.poste || 'Besoin' }]"
    />
    <LoadingState v-if="loading" label="Chargement du besoin…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>
    <ErrorState v-else-if="!besoin" message="Ce besoin n'existe pas." />

    <template v-else>
      <BaseCard>
        <div class="flex flex-wrap items-center gap-2">
          <BasePill :tone="tone[besoin.statut]">{{ label[besoin.statut] }}</BasePill>
          <span class="text-xs text-ink-3">Demandé par {{ besoin.managerNom || 'un manager' }}</span>
        </div>
        <h1 class="mt-2 font-display text-2xl font-bold text-ink">{{ besoin.poste }}</h1>
        <div class="mt-3">
          <div class="text-xs font-semibold uppercase tracking-wide text-green-deep">Description du besoin</div>
          <p class="mt-1 whitespace-pre-line text-sm text-ink-2">
            {{ besoin.description || 'Aucune description fournie.' }}
          </p>
        </div>
        <p v-if="besoin.statut === 'refuse' && besoin.motifRefus" class="mt-3 text-xs text-ink-3">
          Motif du refus : {{ besoin.motifRefus }}
        </p>

        <div class="mt-5 flex flex-wrap gap-2 border-t border-border pt-4">
          <template v-if="besoin.statut === 'transmis' || besoin.statut === 'valide'">
            <BaseButton size="sm" :disabled="busy" @click="publier">Publier l'offre</BaseButton>
            <BaseButton v-if="besoin.statut === 'transmis'" size="sm" variant="secondary" :disabled="busy" @click="valider">Valider</BaseButton>
            <BaseButton size="sm" variant="secondary" :disabled="busy" @click="refuser">Refuser</BaseButton>
          </template>
          <RouterLink
            v-else-if="besoin.statut === 'publie' && besoin.offreId"
            :to="{ name: 'rh.revueCandidats', params: { key: String(besoin.offreId) } }"
          >
            <BaseButton size="sm">Voir les candidatures</BaseButton>
          </RouterLink>
          <BaseButton size="sm" variant="secondary" :disabled="busy" @click="showContact = true">
            Contacter le manager
          </BaseButton>
          <BaseButton size="sm" variant="ghost" @click="router.push({ name: 'rh.besoins' })">Retour</BaseButton>
        </div>
      </BaseCard>
    </template>

    <BaseModal v-model="showContact" :title="`Contacter ${besoin?.managerNom || 'le manager'}`">
      <textarea
        v-model="contactMsg"
        rows="5"
        class="w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm text-ink outline-none focus:border-green-line"
        placeholder="Votre message au manager émetteur du besoin…"
      />
      <template #footer>
        <BaseButton variant="secondary" size="sm" @click="showContact = false">Annuler</BaseButton>
        <BaseButton size="sm" :disabled="busy || !contactMsg.trim()" @click="envoyerContact">Envoyer</BaseButton>
      </template>
    </BaseModal>
  </div>
</template>
