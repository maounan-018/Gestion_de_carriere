<script setup lang="ts">
import { Sparkles, BookOpen } from '@lucide/vue'
import { CARTO_SKILLS } from '@/data/rh'
import { useToast } from '@/composables/useToast'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'

const { toast } = useToast()

// Référentiels ouverts mobilisés (attributions détaillées dans les mentions légales).
const referentiels = [
  { code: 'ESCO', name: 'Skills, Competences & Occupations', role: 'Compétences & métiers', mapped: '1 240 compétences mappées', licence: 'CC BY 4.0' },
  { code: 'O*NET', name: 'Occupational Information Network', role: 'Aptitudes & activités', mapped: '620 aptitudes de référence', licence: 'CC BY 4.0' },
  { code: 'SFIA', name: 'Skills Framework for the Information Age', role: 'Niveaux de responsabilité (1→7)', mapped: 'Échelle appliquée au pôle IT & Digital', licence: 'Licence SFIA' },
]

// Familles du Groupe (colonnes de la cartographie) reliées à leur source.
const familleMeta: Record<string, { source: string; scale: string }> = {
  Analyse: { source: 'ESCO', scale: '1 → 5' },
  Risque: { source: 'ESCO · SFIA', scale: '1 → 5' },
  Digital: { source: 'SFIA', scale: '1 → 7' },
  Compliance: { source: 'ESCO · O*NET', scale: '1 → 5' },
  Leadership: { source: 'O*NET', scale: '1 → 5' },
  Data: { source: 'SFIA', scale: '1 → 7' },
}

// Structure type imposée à toute fiche de poste (source de la Fiche → Offre → Candidature).
const gabarit = [
  { n: 1, title: 'Intitulé & rattachement', desc: 'Libellé normalisé, pôle, ligne métier, niveau hiérarchique.' },
  { n: 2, title: 'Finalité de la fonction', desc: 'Mission en une phrase + principales responsabilités.' },
  { n: 3, title: 'Compétences requises', desc: 'Issues du référentiel ESCO, avec un niveau attendu sur l’échelle (SFIA).' },
  { n: 4, title: 'Prérequis', desc: 'Diplôme, séniorité, habilitations réglementaires.' },
  { n: 5, title: 'Passerelles & évolutions', desc: 'Postes amont/aval possibles — alimente les recommandations de mobilité.' },
  { n: 6, title: 'Critères de matching', desc: 'Compétences pondérées → score de compatibilité interprétable (jamais un filtre).' },
]
</script>

<template>
  <div>
    <BaseBreadcrumb
      :items="[{ label: 'Supervision', to: { name: 'rh.supervision' } }, { label: 'Référentiel & gabarit' }]"
    />

    <BaseCard class="mb-4">
      <div class="flex items-center gap-3">
        <div class="grid h-10 w-10 place-items-center rounded-xl bg-green-soft text-green-deep">
          <BookOpen :size="18" />
        </div>
        <div class="min-w-0">
          <h1 class="font-display text-lg font-bold text-ink">Référentiel de compétences & gabarit de fiche</h1>
          <p class="text-sm text-ink-3">
            Le socle qui structure les fiches de poste, la cartographie et le matching du Groupe.
          </p>
        </div>
      </div>
      <p class="mt-3 rounded-lg bg-gold-soft/50 px-3 py-2 text-[11px] text-gold">
        ⚠️ Données de démonstration synthétiques — les volumes affichés sont illustratifs.
      </p>
    </BaseCard>

    <h2 class="mb-2 font-display text-sm font-bold text-ink">Référentiels ouverts mobilisés</h2>
    <div class="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <BaseCard v-for="r in referentiels" :key="r.code" class="min-w-0">
        <div class="flex items-center gap-2">
          <h3 class="font-display text-base font-bold text-ink">{{ r.code }}</h3>
          <BasePill tone="ok">source ouverte</BasePill>
        </div>
        <p class="mt-0.5 text-xs text-ink-3">{{ r.name }}</p>
        <div class="mt-2 space-y-1 text-xs text-ink-2">
          <div><b class="text-ink-3">Apporte :</b> {{ r.role }}</div>
          <div><b class="text-ink-3">Couverture :</b> {{ r.mapped }}</div>
          <div><b class="text-ink-3">Licence :</b> {{ r.licence }}</div>
        </div>
      </BaseCard>
    </div>

    <div class="grid gap-5 lg:grid-cols-2">
      <BaseCard title="Familles de compétences du Groupe" class="min-w-0">
        <template #actions>
          <BaseButton size="sm" variant="ghost" @click="toast('Édition du référentiel — réservé à l’admin RH (à venir)', 'info')">
            Ajouter une famille
          </BaseButton>
        </template>
        <div class="divide-y divide-border">
          <div v-for="f in CARTO_SKILLS" :key="f" class="flex flex-wrap items-center gap-2 py-2.5">
            <b class="text-sm text-ink">{{ f }}</b>
            <BaseChip tone="green">{{ familleMeta[f]?.source }}</BaseChip>
            <span class="ml-auto text-xs text-ink-3">Échelle {{ familleMeta[f]?.scale }}</span>
          </div>
        </div>
      </BaseCard>

      <BaseCard title="Gabarit de fiche de poste" class="min-w-0">
        <template #actions><BasePill tone="ai"><Sparkles :size="12" /> Standard Groupe</BasePill></template>
        <p class="mb-3 text-xs text-ink-3">
          Toute fiche suit cette structure. C'est la <b>fiche de référence</b> dont dérivent les
          offres et missions (voir modèle Fiche → Offre → Candidature).
        </p>
        <ol class="space-y-2.5">
          <li v-for="s in gabarit" :key="s.n" class="flex gap-3">
            <span class="grid h-6 w-6 shrink-0 place-items-center rounded-lg bg-green-soft text-xs font-bold text-green-deep">
              {{ s.n }}
            </span>
            <div class="min-w-0">
              <div class="text-sm font-semibold text-ink">{{ s.title }}</div>
              <div class="text-xs text-ink-3">{{ s.desc }}</div>
            </div>
          </li>
        </ol>
      </BaseCard>
    </div>
  </div>
</template>
