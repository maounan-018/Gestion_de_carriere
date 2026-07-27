<script setup lang="ts">
import BaseButton from '@/components/ui/BaseButton.vue'
</script>

<template>
  <div class="min-h-screen bg-bg px-4 py-10">
    <div class="mx-auto max-w-2xl">
      <div class="mb-6 flex items-center gap-2.5">
        <div class="grid h-10 w-10 place-items-center rounded-xl bg-green font-display text-xl font-extrabold text-white">
          B
        </div>
        <div>
          <div class="text-sm font-bold text-ink">BMCI · Gestion de carrière</div>
          <div class="text-[11px] text-ink-3">Groupe BNP Paribas</div>
        </div>
      </div>

      <h1 class="font-display text-2xl font-extrabold text-ink">Mentions légales & crédits</h1>

      <div class="mt-6 space-y-6 text-sm leading-relaxed text-ink-2">
        <section>
          <h2 class="font-display text-base font-bold text-ink">Éditeur</h2>
          <p class="mt-1">
            Plateforme interne « La Courbe » — Groupe BMCI (BNP Paribas). Données de démonstration
            synthétiques : aucune donnée réelle de collaborateur n'est traitée dans cette maquette.
          </p>
        </section>

        <section>
          <h2 class="font-display text-base font-bold text-ink">Données personnelles</h2>
          <p class="mt-1">
            Le traitement des données de carrière est soumis au RGPD et à la politique de mobilité
            interne du Groupe. Chaque collaborateur dispose d'un droit d'accès, de rectification et
            de contrôle de la visibilité de son profil (voir Paramètres → Confidentialité).
          </p>
        </section>

        <section>
          <h2 class="font-display text-base font-bold text-ink">
            Référentiels de compétences · attributions
          </h2>
          <p class="mt-1">
            La cartographie et le matching de compétences s'appuient sur des référentiels ouverts,
            utilisés dans le respect de leurs licences :
          </p>
          <ul class="mt-2 space-y-2">
            <li class="rounded-xl border border-border bg-paper p-3">
              <b class="text-ink">ESCO</b> — European Skills, Competences, Qualifications and
              Occupations. © Union européenne, Commission européenne. Diffusé sous licence Creative
              Commons Attribution 4.0 (CC BY 4.0).
            </li>
            <li class="rounded-xl border border-border bg-paper p-3">
              <b class="text-ink">O*NET</b> — Occupational Information Network. © U.S. Department of
              Labor, Employment and Training Administration. Utilisé sous licence Creative Commons
              Attribution 4.0 (CC BY 4.0).
            </li>
            <li class="rounded-xl border border-border bg-paper p-3">
              <b class="text-ink">SFIA</b> — Skills Framework for the Information Age. © SFIA
              Foundation. Utilisé dans le cadre de la licence SFIA applicable.
            </li>
          </ul>
        </section>

        <section>
          <h2 class="font-display text-base font-bold text-ink">Technologies</h2>
          <p class="mt-1">
            Interface Vue 3 · Tailwind CSS · polices Bricolage Grotesque & Hanken Grotesk (SIL Open
            Font License) · icônes Lucide (licence ISC). Application 100 % locale — aucune donnée ne
            quitte l'infrastructure du Groupe.
          </p>
        </section>
      </div>

      <div class="mt-8">
        <BaseButton variant="secondary" @click="$router.back()">← Retour</BaseButton>
      </div>
    </div>
  </div>
</template>
