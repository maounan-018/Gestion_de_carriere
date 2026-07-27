<script setup lang="ts">
import { Settings, Check, BookOpen, ChevronRight } from 'lucide-vue-next'
import BaseCard from '@/components/ui/BaseCard.vue'
import BasePill from '@/components/ui/BasePill.vue'

const reviews = [
  { title: 'Fiches sans compétence ancrée', found: 3, fixed: 3 },
  { title: 'Profils incomplets détectés', found: 8, fixed: 0 },
  { title: 'Doublons de compétences fusionnés', found: 5, fixed: 5 },
]
</script>

<template>
  <div class="space-y-5">
    <BaseCard>
      <div class="flex items-center gap-3">
        <div class="grid h-10 w-10 place-items-center rounded-xl bg-green-soft text-green-deep">
          <Settings :size="18" />
        </div>
        <div>
          <h3 class="font-display text-base font-bold text-ink">Supervision de la plateforme</h3>
          <p class="text-sm text-ink-3">
            Revues automatiques nocturnes de la qualité des données talents.
          </p>
        </div>
      </div>
    </BaseCard>

    <BaseCard title="Dernière revue automatique">
      <template #actions><BasePill tone="new">Terminée · cette nuit</BasePill></template>
      <div class="divide-y divide-border">
        <div v-for="r in reviews" :key="r.title" class="flex items-center gap-3 py-3">
          <div
            class="grid h-8 w-8 place-items-center rounded-lg"
            :class="r.fixed === r.found ? 'bg-green-soft text-green-deep' : 'bg-warning-soft text-warning'"
          >
            <Check :size="15" />
          </div>
          <div class="flex-1">
            <h4 class="text-sm font-bold text-ink">{{ r.title }}</h4>
            <p class="text-xs text-ink-3">
              {{ r.found }} détecté(s) · {{ r.fixed }} corrigé(s) automatiquement
            </p>
          </div>
          <BasePill :tone="r.fixed === r.found ? 'new' : 'warn'">
            {{ r.fixed === r.found ? 'Résolu' : 'À traiter' }}
          </BasePill>
        </div>
      </div>
    </BaseCard>

    <RouterLink
      :to="{ name: 'rh.referentiel' }"
      class="flex items-center gap-3 rounded-2xl border border-border bg-paper p-4 shadow-card transition hover:border-green-line"
    >
      <div class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-green-soft text-green-deep">
        <BookOpen :size="18" />
      </div>
      <div class="min-w-0 flex-1">
        <h4 class="text-sm font-bold text-ink">Référentiel de compétences & gabarit de fiche</h4>
        <p class="text-xs text-ink-3">
          Référentiels ESCO · O*NET · SFIA, familles de compétences et structure type des fiches.
        </p>
      </div>
      <ChevronRight :size="18" class="shrink-0 text-ink-3" />
    </RouterLink>
  </div>
</template>
