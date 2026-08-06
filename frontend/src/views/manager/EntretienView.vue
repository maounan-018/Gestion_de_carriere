<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Sparkles, Play } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import type { TeamMember } from '@/types/manager'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import GuidedInterview from '@/components/shared/GuidedInterview.vue'
import TeamInterview from '@/components/shared/TeamInterview.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const mode = ref<'moi' | 'equipe'>('moi')
const team = ref<TeamMember[]>([])
const selected = ref<TeamMember | null>(null)
const equipeStarted = ref(false)   // écran d'accueil explicatif avant la liste d'équipe
const loading = ref(true)
const error = ref('')

// Étapes présentées sur l'écran d'accueil « Entretiens de l'équipe ».
const ETAPES_EQUIPE = [
  'Choisissez un collaborateur de votre équipe',
  'L’IA vous interroge sur son travail, ancrée sur son profil (parcours, compétences, aspirations)',
  'Vous recevez des conseils concrets pour conduire un entretien juste et utile',
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    team.value = await apiService.getTeam()
  } catch {
    error.value = 'Impossible de charger l’équipe.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<template>
  <div class="space-y-4">
    <div class="inline-flex rounded-xl border border-border bg-paper p-1">
      <button
        class="rounded-lg px-4 py-1.5 text-sm font-semibold transition"
        :class="mode === 'moi' ? 'bg-green text-white' : 'text-ink-2 hover:text-ink'"
        @click="mode = 'moi'"
      >
        Mon entretien
      </button>
      <button
        class="rounded-lg px-4 py-1.5 text-sm font-semibold transition"
        :class="mode === 'equipe' ? 'bg-green text-white' : 'text-ink-2 hover:text-ink'"
        @click="((mode = 'equipe'), (selected = null), (equipeStarted = false))"
      >
        Entretiens de l'équipe
      </button>
    </div>

    <!-- Mon entretien : moteur co-pilote partagé (persona = manager connecté). -->
    <GuidedInterview v-if="mode === 'moi'" />

    <template v-else>
      <LoadingState v-if="loading" label="Chargement de l'équipe…" />
      <ErrorState v-else-if="error" :message="error">
        <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
      </ErrorState>

      <!-- ÉCRAN D'ACCUEIL explicatif (pendant de la simulation « Mon entretien »). -->
      <div v-else-if="!equipeStarted" class="mx-auto max-w-2xl">
        <div class="rounded-2xl border border-border bg-paper p-6 shadow-card">
          <div class="mb-4 inline-flex items-center gap-2 rounded-full bg-green-soft px-3 py-1 text-xs font-bold text-green-deep">
            <Sparkles :size="14" /> Préparation guidée par l'IA
          </div>
          <h2 class="font-display text-2xl font-bold text-ink">Préparez les entretiens de votre équipe</h2>
          <p class="mt-2 text-sm leading-relaxed text-ink-2">
            Cet espace vous aide à préparer l'entretien annuel de chaque membre de votre équipe. Votre
            copilote IA, <b>ancré sur le profil du collaborateur</b>, vous interroge sur son travail et vous
            conseille pour conduire un entretien juste et utile. Rien n'est transmis au collaborateur : vous
            repartez avec une trame de préparation.
          </p>

          <div class="mt-5 rounded-xl border border-green-line bg-green-ghost p-4">
            <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-green-deep">Comment ça marche</p>
            <ol class="space-y-1.5">
              <li v-for="(s, i) in ETAPES_EQUIPE" :key="i" class="flex items-center gap-2.5 text-sm text-ink-2">
                <span class="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-green text-[11px] font-bold text-white">{{ i + 1 }}</span>
                {{ s }}
              </li>
            </ol>
          </div>

          <BaseButton class="mt-5" @click="equipeStarted = true">
            <Play :size="16" /> Voir mon équipe
          </BaseButton>
        </div>
      </div>

      <div v-else-if="!selected" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <div
          v-for="m in team"
          :key="m.id"
          class="flex items-center gap-3 rounded-2xl border border-border bg-paper p-3 shadow-card"
        >
          <BaseAvatar :initials="m.initials" size="md" />
          <div class="min-w-0 flex-1">
            <h4 class="truncate text-sm font-bold text-ink">{{ m.name }}</h4>
            <p class="truncate text-xs text-ink-3">Dernier entretien : {{ m.lastEntretien }}</p>
          </div>
          <BaseButton size="sm" @click="selected = m">Préparer</BaseButton>
        </div>
      </div>

      <div v-else class="space-y-3">
        <button class="text-sm font-semibold text-green-deep hover:underline" @click="selected = null">
          ← Retour à l'équipe
        </button>
        <!-- Préparation guidée : l'IA interroge le manager SUR son collaborateur (ancré profil),
             il répond, l'IA le conseille pour conduire l'entretien. -->
        <TeamInterview :key="selected.id" :subject="selected" />
      </div>
    </template>
  </div>
</template>
