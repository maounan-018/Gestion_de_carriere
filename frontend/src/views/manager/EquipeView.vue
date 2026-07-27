<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { TeamMember } from '@/types/manager'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const team = ref<TeamMember[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()

async function load() {
  loading.value = true
  error.value = ''
  try {
    team.value = await apiService.getTeam()
  } catch {
    error.value = 'Impossible de charger votre équipe.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <p class="text-sm text-ink-3">
        <b class="text-ink-2">{{ team.length }} collaborateurs</b> · cliquez un membre pour ouvrir
        sa base de connaissance.
      </p>
      <div class="flex gap-2">
        <BaseButton variant="secondary" size="sm" @click="toast('Cartographie de l’équipe — bientôt', 'info')">
          Mapping complet
        </BaseButton>
        <BaseButton variant="secondary" size="sm" @click="toast('Message transmis aux RH', 'info')">
          Communiquer aux RH
        </BaseButton>
      </div>
    </div>

    <LoadingState v-if="loading" label="Chargement de l'équipe…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <RouterLink
        v-for="m in team"
        :key="m.id"
        :to="{ name: 'manager.ficheCollab', params: { id: m.id } }"
        class="rounded-2xl border border-border bg-paper p-4 shadow-card transition hover:-translate-y-0.5 hover:border-green-line hover:shadow-float"
      >
        <div class="flex items-center gap-3">
          <BaseAvatar :initials="m.initials" size="md" />
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-1.5">
              <h4 class="truncate text-sm font-bold text-ink">{{ m.name }}</h4>
              <BasePill v-if="m.flag === 'top'" tone="new">Haut potentiel</BasePill>
              <BasePill v-else-if="m.flag === 'watch'" tone="warn">À suivre</BasePill>
            </div>
            <p class="truncate text-xs text-ink-3">{{ m.role }} · {{ m.seniority }}</p>
          </div>
        </div>
        <div class="mt-3 flex items-center justify-between text-xs">
          <span class="text-ink-3">Éval : <b class="text-ink-2">{{ m.evalScore }}</b></span>
          <span class="font-display text-sm font-bold text-green-deep">{{ m.ring }}%</span>
        </div>
        <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-panel-2">
          <div class="h-full rounded-full bg-green" :style="{ width: m.ring + '%' }" />
        </div>
      </RouterLink>
    </div>
  </div>
</template>
