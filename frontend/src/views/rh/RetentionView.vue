<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiService } from '@/services/apiService'
import { useToast } from '@/composables/useToast'
import type { RhPerson } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

const people = ref<RhPerson[]>([])
const loading = ref(true)
const error = ref('')
const { toast } = useToast()

async function load() {
  loading.value = true
  error.value = ''
  try {
    people.value = (await apiService.getRhPeople()).filter((p) => p.riskDeparture)
  } catch {
    error.value = 'Impossible de charger l’analyse.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const causes = [
  "Faible engagement lors des derniers entretiens",
  "Absence d'évolution récente",
  'Rémunération sous le marché',
  'Charge / équilibre pro-perso',
]
const plan = [
  'Programmer un entretien RH sous 2 semaines',
  'Proposer une mission valorisante',
  'Étudier une revalorisation salariale',
  "Clarifier les perspectives d'évolution",
]
</script>

<template>
  <div>
    <BaseBreadcrumb
      :items="[{ label: 'Alertes & actions', to: { name: 'rh.alertes' } }, { label: 'Risque de départ' }]"
    />
    <LoadingState v-if="loading" label="Analyse en cours…" />
    <ErrorState v-else-if="error" :message="error">
      <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
    </ErrorState>

    <div v-else class="grid gap-5 lg:grid-cols-2">
      <BaseCard class="min-w-0" title="Personnes concernées">
        <div class="space-y-2">
          <RouterLink
            v-for="p in people"
            :key="p.id"
            :to="{ name: 'rh.ficheCollabRh', params: { id: p.id } }"
            class="flex items-center gap-3 rounded-xl border border-border bg-panel p-2.5 transition hover:border-green-line"
          >
            <BaseAvatar :initials="p.initials" size="md" />
            <div class="min-w-0 flex-1">
              <h4 class="truncate text-sm font-bold text-ink">{{ p.name }}</h4>
              <p class="truncate text-xs text-ink-3">{{ p.role }} · {{ p.pole }} · dernier RH {{ p.lastRh }}</p>
            </div>
          </RouterLink>
        </div>
      </BaseCard>

      <div class="min-w-0 space-y-5">
        <BaseCard title="Causes probables">
          <ul class="space-y-1.5 text-sm text-ink-2">
            <li v-for="c in causes" :key="c" class="flex gap-2">
              <AppIcon name="flag" :size="14" class="mt-0.5 text-warning" /> {{ c }}
            </li>
          </ul>
        </BaseCard>
        <BaseCard title="Plan de rétention">
          <ul class="space-y-1.5 text-sm text-ink-2">
            <li v-for="a in plan" :key="a" class="flex gap-2">
              <AppIcon name="check" :size="14" class="mt-0.5 text-green-deep" /> {{ a }}
            </li>
          </ul>
          <BaseButton block class="mt-3" @click="toast('Plan de rétention transmis à la direction du pôle', 'info')">
            <AppIcon name="send" :size="15" /> Transmettre le plan
          </BaseButton>
        </BaseCard>
      </div>
    </div>
  </div>
</template>
