<script setup lang="ts">
import { ref, onMounted } from 'vue'
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
const loading = ref(true)
const error = ref('')

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
        @click="((mode = 'equipe'), (selected = null))"
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
        <!-- Vrai entretien IA : le manager mène, l'IA incarne le collaborateur (ancré profil). -->
        <TeamInterview :key="selected.id" :member="selected" />
      </div>
    </template>
  </div>
</template>
