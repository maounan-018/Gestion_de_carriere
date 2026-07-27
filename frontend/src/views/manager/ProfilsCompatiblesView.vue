<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { Vacancy, TeamMember } from '@/types/manager'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const route = useRoute()
const { toast } = useToast()
const vacancy = ref<Vacancy | null>(null)
const team = ref<TeamMember[]>([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [v, t] = await Promise.all([
      apiService.getVacancy(route.params.key as string),
      apiService.getTeam(),
    ])
    vacancy.value = v ?? null
    team.value = t
  } catch {
    error.value = 'Impossible de charger les profils.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => route.params.key, load)

function member(id: string) {
  return team.value.find((t) => t.id === id)
}
</script>

<template>
  <LoadingState v-if="loading" label="Chargement des profils…" />
  <ErrorState v-else-if="error" :message="error">
    <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
  </ErrorState>
  <EmptyState v-else-if="!vacancy" title="Poste introuvable" text="Ce poste n'existe plus.">
    <template #action>
      <RouterLink :to="{ name: 'manager.offres' }"><BaseButton size="sm">Retour aux offres</BaseButton></RouterLink>
    </template>
  </EmptyState>

  <div v-else>
    <BaseBreadcrumb
      :items="[{ label: 'Offres internes', to: { name: 'manager.offres' } }, { label: 'Profils recommandés' }]"
    />
    <BaseCard class="mb-4">
      <h2 class="font-display text-xl font-bold text-ink">{{ vacancy.title }}</h2>
      <p class="text-sm text-ink-3">{{ vacancy.sub }}</p>
    </BaseCard>

    <EmptyState
      v-if="!vacancy.recos.length"
      title="Aucun profil interne aligné"
      text="Aucun collaborateur de votre équipe ne correspond suffisamment à ce poste pour le moment."
    >
      <template #action>
        <BaseButton size="sm" @click="toast('Poste diffusé au Groupe', 'info')">Diffuser au Groupe</BaseButton>
      </template>
    </EmptyState>

    <div v-else class="grid gap-4 sm:grid-cols-2">
      <BaseCard v-for="r in vacancy.recos" :key="r.memberId">
        <div class="flex items-center gap-3">
          <BaseAvatar :initials="member(r.memberId)?.initials || '?'" size="md" />
          <div class="min-w-0 flex-1">
            <h4 class="text-sm font-bold text-ink">{{ member(r.memberId)?.name }}</h4>
            <p class="truncate text-xs text-ink-3">{{ member(r.memberId)?.role }}</p>
          </div>
          <div class="font-display text-lg font-bold text-green-deep">{{ r.score }}%</div>
        </div>
        <div class="mt-2"><BasePill :tone="r.tone">{{ r.score }}% · {{ r.label }}</BasePill></div>
        <p class="mt-2 text-xs text-ink-2">{{ r.why }}</p>
        <div class="mt-3 flex flex-wrap gap-1.5">
          <BaseChip v-for="s in (member(r.memberId)?.skills || []).slice(0, 3)" :key="s.label">
            {{ s.label }}
          </BaseChip>
        </div>
        <div class="mt-3 flex gap-2 border-t border-border pt-3">
          <RouterLink :to="{ name: 'manager.ficheCollab', params: { id: r.memberId } }">
            <BaseButton size="sm" variant="secondary">Voir le profil</BaseButton>
          </RouterLink>
          <BaseButton size="sm" @click="toast('Invitation à postuler envoyée')">
            <AppIcon name="send" :size="14" /> Inviter à postuler
          </BaseButton>
        </div>
      </BaseCard>
    </div>
  </div>
</template>
