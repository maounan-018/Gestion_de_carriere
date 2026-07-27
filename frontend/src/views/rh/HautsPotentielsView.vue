<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { HautPotentiel, RhPerson } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const hps = ref<HautPotentiel[]>([])
const people = ref<RhPerson[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()

async function load() {
  loading.value = true
  error.value = ''
  try {
    ;[hps.value, people.value] = await Promise.all([
      apiService.getHautsPotentiels(),
      apiService.getRhPeople(),
    ])
  } catch {
    error.value = 'Impossible de charger les hauts potentiels.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

function person(id: string) {
  return people.value.find((p) => p.id === id)
}
</script>

<template>
  <div class="space-y-5">
    <LoadingState v-if="loading" label="Chargement…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <template v-else>
      <BaseCard title="Hauts potentiels identifiés">
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div v-for="h in hps" :key="h.personId" class="rounded-2xl border border-border bg-paper p-4 shadow-card">
            <div class="flex items-center gap-3">
              <BaseAvatar :initials="person(h.personId)?.initials || '?'" size="md" />
              <div class="min-w-0 flex-1">
                <h4 class="text-sm font-bold text-ink">{{ person(h.personId)?.name }}</h4>
                <p class="truncate text-xs text-ink-3">{{ person(h.personId)?.role }}</p>
              </div>
              <div class="font-display text-lg font-bold text-green-deep">{{ h.score }}</div>
            </div>
            <div class="mt-2"><BasePill tone="new">{{ h.readiness }}</BasePill></div>
            <p class="mt-2 text-xs text-ink-2">Cible : <b class="text-ink">{{ h.target }}</b></p>
            <RouterLink :to="{ name: 'rh.ficheCollabRh', params: { id: h.personId } }" class="mt-3 block">
              <BaseButton size="sm" block variant="secondary">Ouvrir le dossier</BaseButton>
            </RouterLink>
          </div>
        </div>
      </BaseCard>

      <BaseCard title="Postes critiques · succession">
        <div class="flex flex-wrap items-center gap-3 rounded-xl border border-warning/25 bg-warning-soft p-3">
          <AppIcon name="flag" :size="18" class="text-warning" />
          <div class="min-w-0 flex-1">
            <h4 class="text-sm font-bold text-ink">Directeur Asset Management</h4>
            <p class="text-xs text-ink-2">Poste clé sans successeur désigné · vivier à constituer.</p>
          </div>
          <BaseButton size="sm" @click="toast('Analyse de succession lancée', 'info')">
            Lancer une analyse
          </BaseButton>
        </div>
      </BaseCard>
    </template>
  </div>
</template>
