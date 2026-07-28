<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { Offer } from '@/types/domain'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { Sparkles } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const { toast } = useToast()

const offer = ref<Offer | null>(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    offer.value = (await apiService.getOffer(route.params.key as string)) ?? null
  } catch {
    error.value = "Impossible de charger le détail de l'offre."
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => route.params.key, load)

/* ---- Parcours de candidature (modale) ---- */
const showApply = ref(false)
const step = ref(0)
const motiv = ref('')
const consent = ref(false)
const totalSteps = computed(() => (offer.value?.managerInformed ? 3 : 2))

function openApply() {
  step.value = 0
  motiv.value = ''
  consent.value = false
  showApply.value = true
}
function next() {
  if (offer.value?.managerInformed && step.value === 1 && !consent.value) return
  step.value++
}
const sending = ref(false)
async function send() {
  if (!offer.value || sending.value) return
  sending.value = true
  try {
    await apiService.postuler(offer.value.key, motiv.value.trim() || undefined)
    showApply.value = false
    toast('Candidature envoyée')
    router.push({ name: 'collab.mesCandidatures' })
  } catch (e) {
    toast(e instanceof Error ? e.message : "Échec de l'envoi de la candidature", 'error')
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <LoadingState v-if="loading" label="Chargement de l'offre…" />
  <ErrorState v-else-if="error" :message="error">
    <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
  </ErrorState>
  <EmptyState
    v-else-if="!offer"
    title="Offre introuvable"
    text="Cette offre n'existe plus ou a été retirée."
  >
    <template #action>
      <RouterLink :to="{ name: 'collab.offres' }"><BaseButton size="sm">Retour aux offres</BaseButton></RouterLink>
    </template>
  </EmptyState>

  <div v-else>
    <BaseBreadcrumb
      :items="[
        { label: 'Offres internes', to: { name: 'collab.offres' } },
        { label: offer.title },
      ]"
    />

    <div class="grid gap-5 lg:grid-cols-[1fr_320px]">
      <!-- Colonne principale -->
      <BaseCard>
        <div class="flex flex-wrap items-center gap-2">
          <BasePill :tone="offer.tone">{{ offer.type }}</BasePill>
          <BasePill v-if="offer.tpill" tone="new">{{ offer.tpill }}</BasePill>
          <BasePill tone="mut" class="ml-auto">{{ offer.pct }} % · {{ offer.adq }}</BasePill>
        </div>
        <h2 class="mt-3 font-display text-2xl font-bold text-ink">{{ offer.title }}</h2>
        <p class="text-sm text-ink-3">{{ offer.ctx }}</p>

        <hr class="my-4 border-border" />
        <h3 class="mb-2 font-display text-[15px] font-bold text-ink">{{ offer.missionTitle }}</h3>
        <p v-for="(p, i) in offer.mission" :key="i" class="mt-2 text-sm leading-relaxed text-ink-2 first:mt-0">
          {{ p }}
        </p>

        <hr class="my-4 border-border" />
        <h3 class="mb-2.5 font-display text-[15px] font-bold text-ink">Compétences requises</h3>
        <div class="flex flex-wrap gap-2">
          <BaseChip v-for="s in offer.skills" :key="s">{{ s }}</BaseChip>
        </div>
      </BaseCard>

      <!-- Colonne latérale -->
      <div class="space-y-5">
        <BaseCard title="Informations">
          <div class="flex flex-col gap-3 text-sm text-ink-2">
            <span v-for="(f, i) in offer.infos" :key="i" class="inline-flex items-center gap-2.5">
              <AppIcon :name="f.icon" :size="15" /> {{ f.label }}
            </span>
          </div>
          <div
            class="mt-3.5 flex items-start gap-2 rounded-xl border px-3 py-2.5 text-xs"
            :class="offer.noteOk
              ? 'border-green-line bg-green-ghost text-green-deep'
              : 'border-warning/25 bg-warning-soft text-warning'"
          >
            <AppIcon :name="offer.noteIcon" :size="14" />
            <span>{{ offer.noteText }}</span>
          </div>
          <BaseButton block class="mt-3.5" @click="openApply">
            <AppIcon name="send" :size="15" /> {{ offer.ctaDetail }}
          </BaseButton>
        </BaseCard>

        <div class="flex gap-3 rounded-2xl border border-green-line bg-green-soft p-4">
          <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green text-white">
            <Sparkles :size="16" />
          </div>
          <div>
            <h4 class="text-sm font-bold text-green-deep">{{ offer.fitTitle }}</h4>
            <p class="mt-0.5 text-xs text-ink-2">{{ offer.fitText }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Modale de candidature -->
    <BaseModal v-model="showApply" :title="offer.ctaDetail">
      <p class="-mt-2 mb-3 text-xs text-ink-3">{{ offer.title }}</p>

      <!-- étapes -->
      <div class="mb-4 flex items-center gap-1.5">
        <template v-for="i in totalSteps" :key="i">
          <span
            class="grid h-6 w-6 place-items-center rounded-full text-[11px] font-bold"
            :class="step >= i - 1 ? 'bg-green text-white' : 'bg-panel-2 text-ink-3'"
          >{{ i }}</span>
          <span v-if="i < totalSteps" class="h-0.5 w-6 rounded" :class="step >= i ? 'bg-green' : 'bg-panel-2'" />
        </template>
      </div>

      <!-- Étape 0 : motivation -->
      <div v-if="step === 0">
        <label class="mb-1.5 block text-xs font-semibold text-ink-2">Votre motivation</label>
        <textarea
          v-model="motiv"
          rows="4"
          placeholder="En quoi cette opportunité correspond-elle à votre projet…"
          class="w-full rounded-xl border border-border bg-paper px-3 py-2 text-sm outline-none focus:border-green-line"
        />
        <div class="mt-2 flex items-start gap-2 rounded-xl border border-green-line bg-green-ghost px-3 py-2 text-xs text-green-deep">
          <Sparkles :size="14" /> Astuce : reliez cette opportunité à une compétence à développer.
        </div>
      </div>

      <!-- Étape 1 : consentement (missions/projets) -->
      <div v-else-if="offer.managerInformed && step === 1">
        <label class="flex cursor-pointer items-start gap-2.5 text-sm text-ink-2">
          <input v-model="consent" type="checkbox" class="mt-0.5 accent-green" />
          <span>J'accepte que mon manager ({{ offer.managerName }}) soit informé de ma candidature.</span>
        </label>
        <div class="mt-2 flex items-start gap-2 rounded-xl border border-warning/25 bg-warning-soft px-3 py-2 text-xs text-warning">
          <AppIcon name="bell" :size="14" />
          Conformément à la politique de mobilité BMCI, votre manager est notifié dès qu'un
          collaborateur postule à une mission ou un projet.
        </div>
      </div>

      <!-- Étape finale : récapitulatif -->
      <div v-else class="space-y-2 text-sm">
        <div class="flex justify-between gap-3 border-b border-border pb-2">
          <span class="text-ink-3">Opportunité</span><b class="text-right text-ink">{{ offer.title }}</b>
        </div>
        <div class="flex justify-between gap-3 border-b border-border pb-2">
          <span class="text-ink-3">Motivation</span>
          <span class="max-w-[60%] text-right text-ink-2">{{ motiv || '—' }}</span>
        </div>
        <div class="flex justify-between gap-3">
          <span class="text-ink-3">Manager informé</span>
          <b class="text-right" :class="offer.managerInformed ? 'text-green-deep' : 'text-ink'">
            {{ offer.managerInformed ? 'Oui · ' + offer.managerName : 'Non · confidentiel' }}
          </b>
        </div>
      </div>

      <template #footer>
        <BaseButton v-if="step > 0" variant="secondary" size="sm" @click="step--">← Précédent</BaseButton>
        <BaseButton
          v-if="step < totalSteps - 1"
          size="sm"
          :disabled="offer.managerInformed && step === 1 && !consent"
          @click="next"
        >Suivant →</BaseButton>
        <BaseButton v-else size="sm" :disabled="sending" @click="send">
          <AppIcon name="send" :size="14" /> {{ sending ? 'Envoi…' : 'Envoyer ma candidature' }}
        </BaseButton>
      </template>
    </BaseModal>
  </div>
</template>
