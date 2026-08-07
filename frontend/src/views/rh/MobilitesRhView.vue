<script setup lang="ts">
/**
 * Demandes de mobilité (HRBP) — les demandes d'évolution TRANSMISES par les
 * collaborateurs/managers. Écran dédié (atteint depuis l'alerte « X demandes de
 * mobilité exprimées »), consultable ; mène à la fiche du collaborateur.
 */
import { ref, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import type { SouhaitRecu } from '@/types/manager'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const items = ref<SouhaitRecu[]>([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await apiService.getSouhaitsRecus()
  } catch {
    error.value = 'Impossible de charger les demandes de mobilité.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const statusTone: Record<string, 'new' | 'ai' | 'warn' | 'mut'> = {
  'à traiter': 'warn', accordé: 'new', 'transmis HRBP': 'ai', refusé: 'mut',
}
</script>

<template>
  <div class="space-y-5">
    <div>
      <h2 class="font-display text-2xl font-bold text-ink">Demandes de mobilité</h2>
      <p class="text-sm text-ink-3">
        Demandes d'évolution transmises par les collaborateurs · opportunité de rétention.
      </p>
    </div>

    <LoadingState v-if="loading" label="Chargement des demandes…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>
    <EmptyState
      v-else-if="!items.length"
      title="Aucune demande de mobilité"
      text="Les demandes d'évolution transmises par les collaborateurs apparaîtront ici."
    />

    <div v-else class="space-y-3">
      <div
        v-for="s in items"
        :key="s.id"
        class="flex flex-wrap items-start gap-3 rounded-2xl border border-border bg-paper p-4 shadow-card"
      >
        <BaseAvatar :initials="s.memberInitials" size="md" />
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <h4 class="text-sm font-bold text-ink">{{ s.memberName }}</h4>
            <BasePill :tone="s.kind === 'mission' ? 'ai' : 'new'">
              {{ s.kind === 'mission' ? 'Mobilité' : 'Évolution' }}
            </BasePill>
            <BasePill :tone="statusTone[s.status] ?? 'mut'">{{ s.status }}</BasePill>
          </div>
          <p class="mt-1 text-sm text-ink-2">{{ s.title }}</p>
          <p v-if="s.desc" class="mt-0.5 text-xs text-ink-3">{{ s.desc }}</p>
          <p class="mt-1 text-[11px] text-ink-3">Horizon : {{ s.horizon || '—' }}</p>
        </div>
        <RouterLink v-if="s.memberId" :to="{ name: 'rh.ficheCollabRh', params: { id: s.memberId } }">
          <BaseButton size="sm" variant="secondary">Voir la fiche</BaseButton>
        </RouterLink>
      </div>
    </div>
  </div>
</template>
