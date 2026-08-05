<script setup lang="ts">
/**
 * ScoringInfo · disclosure expliquant COMMENT une compétence est évaluée/scorée.
 * Répond à la demande « expliquer comment les compétences sont évaluées ». Modèle :
 * évaluation du manager (poids prépondérant) + mini-jeux d'évaluation (à venir) +
 * avis des pairs (savoir-être) ; les compétences seulement déclarées restent en
 * attente d'évaluation. Accessible (élément <details> natif, sans JS).
 */
import { HelpCircle } from '@lucide/vue'
</script>

<template>
  <details class="group rounded-xl border border-border bg-panel-2/60 px-3.5 py-2.5">
    <summary
      class="flex cursor-pointer list-none items-center gap-2 text-xs font-semibold text-ink-2 marker:hidden"
    >
      <HelpCircle :size="14" class="text-green-deep" />
      Comment ces scores sont-ils calculés ?
      <span class="ml-auto text-ink-3 transition group-open:rotate-180">▾</span>
    </summary>
    <div class="mt-2.5 space-y-2 text-xs leading-relaxed text-ink-2">
      <p>
        Le <b>pourcentage d'acquisition</b> d'une compétence combine plusieurs sources, l'évaluation
        du manager pesant le plus :
      </p>
      <ul class="space-y-1.5">
        <li class="flex gap-2">
          <span class="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-green" />
          <span><b>Évaluation du manager</b> (poids prépondérant) : chaque compétence, savoir-être compris,
            est évaluée sur une échelle de maîtrise (1 à 10).</span>
        </li>
        <li class="flex gap-2">
          <span class="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-gold" />
          <span><b>Mini-jeux d'évaluation</b> (à venir) : quiz et mises en situation par thème, répartis
            sur plusieurs semaines, qui viennent compléter le score.</span>
        </li>
        <li class="flex gap-2">
          <span class="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-teal" />
          <span><b>Avis des pairs</b> : surtout pour les compétences comportementales (savoir-être).</span>
        </li>
        <li class="flex gap-2">
          <span class="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-panel-2 ring-1 ring-border" />
          <span><b>Compétences déclarées</b> (CV ou fiche de poste) : listées mais <b>en attente
            d'évaluation</b> — elles n'ont pas encore de score.</span>
        </li>
      </ul>
    </div>
  </details>
</template>
