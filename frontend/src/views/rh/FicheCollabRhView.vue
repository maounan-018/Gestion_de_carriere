<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiService } from '@/services/apiService'
import type { RhPerson } from '@/types/rh'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const route = useRoute()
const p = ref<RhPerson | null>(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    p.value = (await apiService.getRhPerson(route.params.id as string)) ?? null
  } catch {
    error.value = 'Impossible de charger la fiche.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => route.params.id, load)
</script>

<template>
  <LoadingState v-if="loading" label="Chargement de la fiche…" />
  <ErrorState v-else-if="error" :message="error">
    <template #action><BaseButton size="sm" @click="load">Réessayer</BaseButton></template>
  </ErrorState>
  <EmptyState v-else-if="!p" title="Collaborateur introuvable" text="Cette fiche n'existe pas.">
    <template #action>
      <RouterLink :to="{ name: 'rh.annuaire' }"><BaseButton size="sm">Retour à l'annuaire</BaseButton></RouterLink>
    </template>
  </EmptyState>

  <div v-else>
    <BaseBreadcrumb :items="[{ label: 'Annuaire', to: { name: 'rh.annuaire' } }, { label: p.name }]" />

    <div class="grid gap-5 lg:grid-cols-[1fr_300px]">
      <div class="space-y-5">
        <BaseCard>
          <div class="flex flex-wrap items-center gap-4">
            <BaseAvatar :initials="p.initials" size="xl" />
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <h2 class="font-display text-2xl font-bold text-ink">{{ p.name }}</h2>
                <BasePill v-if="p.flag === 'top'" tone="new">Haut potentiel</BasePill>
                <BasePill v-else-if="p.riskDeparture" tone="hot">Risque de départ</BasePill>
              </div>
              <p class="text-sm text-ink-3">{{ p.role }} · {{ p.pole }} · {{ p.seniority }}</p>
            </div>
            <div class="text-center">
              <div class="font-display text-2xl font-extrabold text-green-deep">{{ p.ring }}%</div>
              <div class="text-[10px] text-ink-3">profil</div>
            </div>
          </div>
        </BaseCard>

        <BaseCard title="Compétences">
          <div class="space-y-3">
            <div v-for="s in p.skills" :key="s.label">
              <div class="mb-1 flex justify-between text-xs">
                <span class="font-medium text-ink-2">{{ s.label }}</span>
                <span class="text-ink-3">{{ s.pct }}%</span>
              </div>
              <div class="h-1.5 overflow-hidden rounded-full bg-panel-2">
                <div class="h-full rounded-full bg-green" :style="{ width: s.pct + '%' }" />
              </div>
            </div>
          </div>
        </BaseCard>

        <div class="grid gap-5 sm:grid-cols-2">
          <BaseCard title="Points forts">
            <div class="flex flex-wrap gap-2"><BaseChip v-for="s in p.strengths" :key="s" tone="green">{{ s }}</BaseChip></div>
          </BaseCard>
          <BaseCard title="À développer">
            <div class="flex flex-wrap gap-2"><BaseChip v-for="g in p.gaps" :key="g" tone="gap">{{ g }}</BaseChip></div>
          </BaseCard>
        </div>
      </div>

      <div class="space-y-5">
        <BaseCard title="Aspiration">
          <div class="rounded-xl border border-green-line bg-green-ghost p-3">
            <div class="flex items-center gap-2 text-green-deep">
              <AppIcon name="route" :size="15" /><b class="text-sm">{{ p.aspiration }}</b>
            </div>
            <p class="mt-1 text-xs text-ink-2">Horizon {{ p.aspirationHorizon }}</p>
          </div>
        </BaseCard>
        <BaseCard title="Suivi RH">
          <div class="flex items-center justify-between text-sm">
            <span class="text-ink-3">Dernier entretien RH</span>
            <b :class="p.riskDeparture ? 'text-danger' : 'text-ink'">{{ p.lastRh }}</b>
          </div>
          <RouterLink :to="{ name: 'rh.bilan', params: { id: p.id } }" class="mt-3 block">
            <BaseButton block><AppIcon name="chat" :size="15" /> Préparer un entretien</BaseButton>
          </RouterLink>
        </BaseCard>
      </div>
    </div>
  </div>
</template>
