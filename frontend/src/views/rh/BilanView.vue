<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Sparkles } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { RhPerson } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import TeamInterview from '@/components/shared/TeamInterview.vue'

const route = useRoute()
const { toast } = useToast()
const p = ref<RhPerson | null>(null)
const loading = ref(true)
const error = ref('')

/* ---- Proposer un créneau d'entretien (notification ciblée au collaborateur) ---- */
const showSlot = ref(false)
const slotDate = ref('')
const slotNote = ref('')
const sendingSlot = ref(false)
/* Questions de préparation dérivées du profil réel du collaborateur. */
const prepQuestions = computed<string[]>(() => {
  const c = p.value
  if (!c) return []
  const q: string[] = []
  if (c.aspiration) q.push(`Comment vous projetez-vous vers « ${c.aspiration} » à horizon ${c.aspirationHorizon || 'moyen terme'} ?`)
  if (c.gaps.length) q.push(`Quelles missions ou formations vous aideraient à progresser sur ${c.gaps[0]} ?`)
  q.push('Qu\'est-ce qui vous motive le plus dans votre poste aujourd\'hui ?')
  q.push('De quel accompagnement auriez-vous besoin pour franchir un cap cette année ?')
  return q
})

async function proposeSlot() {
  if (!p.value || !slotDate.value || sendingSlot.value) return
  sendingSlot.value = true
  const quand = new Date(slotDate.value).toLocaleString('fr-FR', {
    dateStyle: 'full', timeStyle: 'short',
  })
  const message = `Un créneau d'entretien annuel vous est proposé le ${quand}.`
    + (slotNote.value.trim() ? ` ${slotNote.value.trim()}` : '')
  try {
    const { delivered } = await apiService.messageProfil(
      p.value.id, 'Créneau d\'entretien proposé', message, 'collab.entretien')
    toast(delivered
      ? `Créneau proposé à ${p.value.name} (notification envoyée)`
      : 'Créneau enregistré (ce collaborateur n\'a pas de compte actif)', 'ok')
    showSlot.value = false
    slotDate.value = ''
    slotNote.value = ''
  } catch (e) {
    toast(e instanceof Error ? e.message : 'Échec de la proposition', 'error')
  } finally {
    sendingSlot.value = false
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    p.value = (await apiService.getRhPerson(route.params.id as string)) ?? null
  } catch {
    error.value = 'Impossible de charger le bilan.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => route.params.id, load)
</script>

<template>
  <LoadingState v-if="loading" label="Préparation du bilan…" />
  <ErrorState v-else-if="error" :message="error">
    <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
  </ErrorState>
  <EmptyState v-else-if="!p" title="Introuvable" text="Ce collaborateur n'existe pas.">
    <template #action>
      <RouterLink :to="{ name: 'rh.annuaire' }"><BaseButton size="sm">Annuaire</BaseButton></RouterLink>
    </template>
  </EmptyState>

  <div v-else>
    <BaseBreadcrumb
      :items="[
        { label: 'Annuaire', to: { name: 'rh.annuaire' } },
        { label: p.name, to: { name: 'rh.ficheCollabRh', params: { id: p.id } } },
        { label: 'Préparer un entretien' },
      ]"
    />
    <div class="mb-4 flex items-center gap-3">
      <BaseAvatar :initials="p.initials" size="md" />
      <div>
        <h2 class="font-display text-xl font-bold text-ink">Entretien avec {{ p.name }}</h2>
        <p class="text-sm text-ink-3">{{ p.role }} · {{ p.pole }}</p>
      </div>
    </div>

    <div class="grid gap-5 lg:grid-cols-2">
      <BaseCard title="Bilan de l'année">
        <ul class="space-y-2 text-sm text-ink-2">
          <li class="flex gap-2"><AppIcon name="award" :size="14" class="mt-0.5 text-green-deep" /> Évaluation : {{ p.evalScore }} · profil {{ p.ring }}%</li>
          <li class="flex gap-2"><AppIcon name="check" :size="14" class="mt-0.5 text-green-deep" /> Points forts : {{ p.strengths.join(', ') }}</li>
          <li class="flex gap-2"><AppIcon name="flag" :size="14" class="mt-0.5 text-warning" /> À développer : {{ p.gaps.join(', ') }}</li>
        </ul>
      </BaseCard>

      <BaseCard title="Poste visé & aspirations">
        <div class="rounded-xl border border-green-line bg-green-ghost p-3">
          <div class="flex items-center gap-2 text-green-deep">
            <AppIcon name="route" :size="15" /><b class="text-sm">{{ p.aspiration }}</b>
          </div>
          <p class="mt-1 text-xs text-ink-2">Horizon {{ p.aspirationHorizon }}</p>
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <BaseChip v-for="s in p.skills.slice(0, 4)" :key="s.label">{{ s.label }}</BaseChip>
        </div>
      </BaseCard>

      <BaseCard title="Recommandation IA · préparation" class="lg:col-span-2">
        <div class="mb-3 flex gap-3">
          <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green text-white">
            <Sparkles :size="16" />
          </div>
          <p class="text-sm text-ink-2">
            Trame de préparation générée à partir du profil de <b class="text-ink">{{ p.name }}</b> :
            valoriser ses réussites, cadrer les axes de progrès et ouvrir sur son aspiration.
          </p>
        </div>
        <div class="grid gap-3 sm:grid-cols-3">
          <div class="rounded-xl border border-green-line bg-green-ghost p-3">
            <h4 class="mb-1.5 flex items-center gap-1.5 text-xs font-bold text-green-deep">
              <AppIcon name="check" :size="13" /> Points à valoriser
            </h4>
            <ul class="space-y-1 text-xs text-ink-2">
              <li v-for="s in p.strengths" :key="s">• {{ s }}</li>
              <li v-if="!p.strengths.length" class="text-ink-3">À explorer en entretien.</li>
            </ul>
          </div>
          <div class="rounded-xl border border-warning/25 bg-warning-soft/40 p-3">
            <h4 class="mb-1.5 flex items-center gap-1.5 text-xs font-bold text-warning">
              <AppIcon name="flag" :size="13" /> Axes de développement
            </h4>
            <ul class="space-y-1 text-xs text-ink-2">
              <li v-for="g in p.gaps" :key="g">• {{ g }}</li>
              <li v-if="!p.gaps.length" class="text-ink-3">Aucun écart majeur identifié.</li>
            </ul>
          </div>
          <div class="rounded-xl border border-border bg-panel p-3">
            <h4 class="mb-1.5 flex items-center gap-1.5 text-xs font-bold text-ink">
              <AppIcon name="chat" :size="13" /> Questions à poser
            </h4>
            <ul class="space-y-1 text-xs text-ink-2">
              <li v-for="q in prepQuestions" :key="q">• {{ q }}</li>
            </ul>
          </div>
        </div>
        <BaseButton class="mt-3" @click="showSlot = true">
          <AppIcon name="cal" :size="15" /> Proposer un créneau
        </BaseButton>
      </BaseCard>
    </div>

    <BaseModal v-model="showSlot" :title="`Proposer un créneau à ${p.name}`">
      <div class="space-y-4">
        <label class="block">
          <span class="mb-1 block text-xs font-semibold text-ink-2">Date et heure proposées</span>
          <input
            v-model="slotDate"
            type="datetime-local"
            class="w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-green"
          />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs font-semibold text-ink-2">Message (optionnel)</span>
          <textarea
            v-model="slotNote"
            rows="3"
            placeholder="Ex : Merci de confirmer votre disponibilité."
            class="w-full resize-none rounded-xl border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-green"
          />
        </label>
        <p class="text-[11px] text-ink-3">Le collaborateur reçoit une notification et retrouve la préparation dans son espace entretien.</p>
      </div>
      <template #footer>
        <BaseButton variant="secondary" size="sm" @click="showSlot = false">Annuler</BaseButton>
        <BaseButton size="sm" :disabled="sendingSlot || !slotDate" @click="proposeSlot">
          <AppIcon name="send" :size="14" /> {{ sendingSlot ? 'Envoi…' : 'Proposer le créneau' }}
        </BaseButton>
      </template>
    </BaseModal>

    <!-- Vrai entretien IA : le RH mène, l'IA incarne le collaborateur (ancré profil). -->
    <div class="mt-5">
      <h3 class="mb-3 font-display text-base font-bold text-ink">Simuler l'entretien</h3>
      <TeamInterview :key="p.id" :subject="p" />
    </div>
  </div>
</template>
