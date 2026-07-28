<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
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
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const route = useRoute()
const { toast } = useToast()
const p = ref<RhPerson | null>(null)
const loading = ref(true)
const error = ref('')

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
        <div class="flex gap-3">
          <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-green text-white">
            <Sparkles :size="16" />
          </div>
          <p class="text-sm text-ink-2">
            Aborder l'aspiration « {{ p.aspiration }} », valoriser les points forts et proposer un
            plan de développement sur {{ p.gaps.join(' et ') }}. Un créneau peut être proposé au
            collaborateur.
          </p>
        </div>
        <BaseButton class="mt-3" @click="toast('Créneau proposé au collaborateur')">
          <AppIcon name="cal" :size="15" /> Proposer un créneau
        </BaseButton>
      </BaseCard>
    </div>
  </div>
</template>
