<script setup lang="ts">
import { ref } from 'vue'
import { Sparkles, Send, Search, Plus, TrendingUp } from '@lucide/vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseChip from '@/components/ui/BaseChip.vue'
import BasePill from '@/components/ui/BasePill.vue'
import BaseBadge from '@/components/ui/BaseBadge.vue'
import BaseAvatar from '@/components/ui/BaseAvatar.vue'
import BaseBreadcrumb from '@/components/ui/BaseBreadcrumb.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import { useToast } from '@/composables/useToast'

const { toast } = useToast()
const modalOpen = ref(false)
</script>

<template>
  <BaseBreadcrumb :items="[{ label: 'Accueil', to: '/' }, { label: 'Design system' }]" />

  <div class="mb-6">
    <div
      class="inline-flex items-center gap-2 rounded-full bg-gold-soft px-3 py-1 text-xs font-extrabold text-gold"
    >
      M1 · Design system + shell · données de démonstration synthétiques
    </div>
    <h1 class="mt-3 font-display text-2xl font-extrabold text-ink">
      Bibliothèque de composants « La Courbe »
    </h1>
    <p class="mt-1 max-w-2xl text-sm text-ink-2">
      Primitives réutilisables + états (chargement / vide / erreur, le manque G5–G7). Le shell
      autour de cette page (sidebar + barre du haut) est celui qui accueillera tous les écrans.
    </p>
  </div>

  <div class="grid gap-5 lg:grid-cols-2">
    <!-- Boutons -->
    <BaseCard title="Boutons">
      <div class="flex flex-wrap items-center gap-2">
        <BaseButton><Sparkles :size="16" /> Principal</BaseButton>
        <BaseButton variant="secondary">Secondaire</BaseButton>
        <BaseButton variant="ai"><Sparkles :size="15" /> IA</BaseButton>
        <BaseButton variant="ghost">Ghost</BaseButton>
        <BaseButton variant="danger">Danger</BaseButton>
      </div>
      <div class="mt-3 flex flex-wrap items-center gap-2">
        <BaseButton size="sm"><Send :size="14" /> Petit</BaseButton>
        <BaseButton size="sm" variant="secondary">Petit sec.</BaseButton>
        <BaseButton disabled>Désactivé</BaseButton>
      </div>
      <BaseButton block class="mt-3"><Search :size="16" /> Pleine largeur</BaseButton>
    </BaseCard>

    <!-- Pills / Badges / Chips -->
    <BaseCard title="Pastilles, badges & chips">
      <div class="mb-2 text-xs font-semibold text-ink-3">Pills (statuts)</div>
      <div class="flex flex-wrap gap-2">
        <BasePill tone="new">Nouveau</BasePill>
        <BasePill tone="ai"><Sparkles :size="12" /> IA</BasePill>
        <BasePill tone="warn">À vérifier</BasePill>
        <BasePill tone="hot">Refusée</BasePill>
        <BasePill tone="mut">Neutre</BasePill>
      </div>
      <div class="mb-2 mt-4 text-xs font-semibold text-ink-3">Badges</div>
      <div class="flex flex-wrap gap-2">
        <BaseBadge tone="role">Collaborateur</BaseBadge>
        <BaseBadge tone="gold">Top évaluation</BaseBadge>
        <BaseBadge tone="mut">Muted</BaseBadge>
      </div>
      <div class="mb-2 mt-4 text-xs font-semibold text-ink-3">Chips (compétences)</div>
      <div class="flex flex-wrap gap-2">
        <BaseChip tone="green">Analyse financière</BaseChip>
        <BaseChip>Python · SQL</BaseChip>
        <BaseChip tone="gap">Diriger une équipe</BaseChip>
        <BaseChip tone="add"><Plus :size="12" /> Ajouter</BaseChip>
      </div>
    </BaseCard>

    <!-- Avatars + en-tête custom -->
    <BaseCard>
      <template #header>
        <h3 class="font-display text-base font-bold text-ink">Avatars & en-tête de carte</h3>
      </template>
      <template #actions>
        <BasePill tone="ai">exemple</BasePill>
      </template>
      <div class="flex items-center gap-4">
        <BaseAvatar initials="YE" size="sm" />
        <BaseAvatar initials="YE" size="md" />
        <BaseAvatar initials="YE" size="xl" />
        <div class="text-sm text-ink-2">
          <div class="font-semibold text-ink">Youssef El Amrani</div>
          <div class="text-xs text-ink-3">Analyste Risque Senior</div>
        </div>
      </div>
    </BaseCard>

    <!-- Interactions -->
    <BaseCard title="Interactions (toast + modale)">
      <div class="flex flex-wrap gap-2">
        <BaseButton @click="toast('Candidature envoyée')">Toast succès</BaseButton>
        <BaseButton variant="secondary" @click="toast('Nouveau code envoyé', 'info')">
          Toast info
        </BaseButton>
        <BaseButton variant="danger" @click="toast('Échec du réseau', 'error')">Toast erreur</BaseButton>
        <BaseButton variant="ai" @click="modalOpen = true"><Sparkles :size="15" /> Modale</BaseButton>
      </div>
    </BaseCard>

    <!-- États -->
    <BaseCard title="État · chargement">
      <LoadingState label="Analyse IA en cours…" />
      <div class="mt-2 space-y-2">
        <SkeletonBlock height="0.9rem" width="70%" />
        <SkeletonBlock height="0.9rem" width="90%" />
        <SkeletonBlock height="0.9rem" width="55%" />
      </div>
    </BaseCard>

    <BaseCard title="État · vide">
      <EmptyState
        :icon="Search"
        title="Aucun résultat"
        text="Aucune offre ne correspond à ce filtre pour le moment."
      >
        <template #action>
          <BaseButton size="sm" variant="secondary">Réinitialiser les filtres</BaseButton>
        </template>
      </EmptyState>
    </BaseCard>

    <BaseCard title="État · erreur" class="lg:col-span-2">
      <ErrorState
        message="Impossible de charger les recommandations. Vérifiez votre connexion et réessayez."
      >
        <template #action>
          <BaseButton size="sm" @click="toast('Nouvelle tentative…', 'info')">
            <TrendingUp :size="14" /> Réessayer
          </BaseButton>
        </template>
      </ErrorState>
    </BaseCard>
  </div>

  <BaseModal v-model="modalOpen" title="Exemple de modale">
    <p class="text-sm text-ink-2">
      Les modales multi-étapes (candidature, souhait, évaluation) s'appuieront sur ce composant :
      fond flouté, fermeture par Échap ou clic extérieur, en-tête et pied optionnels.
    </p>
    <div class="mt-3 rounded-xl border border-green-line bg-green-ghost p-3 text-sm text-green-deep">
      <Sparkles :size="14" class="mr-1 inline" /> Le contenu est un simple slot.
    </div>
    <template #footer>
      <BaseButton variant="secondary" size="sm" @click="modalOpen = false">Annuler</BaseButton>
      <BaseButton size="sm" @click="((modalOpen = false), toast('Confirmé'))">Confirmer</BaseButton>
    </template>
  </BaseModal>
</template>
