<script setup lang="ts">
import { Sparkles, TrendingUp, Flag, ShieldCheck } from '@lucide/vue'

const palette: Array<[string, string]> = [
  ['green', '#00915A'],
  ['green-deep', '#00784B'],
  ['green-soft', '#E4F2EA'],
  ['ink', '#0E1A14'],
  ['ink-2', '#41504A'],
  ['ink-3', '#6E7C75'],
  ['gold', '#B8892E'],
  ['warning', '#8A5C12'],
  ['danger', '#C23A32'],
  ['bg', '#F4F8F5'],
  ['panel-2', '#EDF4EF'],
  ['border', '#E1EAE4'],
]

const heat: Array<[number, string, boolean]> = [
  [0, '#EDF1EE', false],
  [1, '#D3EBDC', false],
  [2, '#8CD0A6', false],
  [3, '#34A469', true],
  [4, '#0B7A4B', true],
]
</script>

<template>
  <div class="min-h-screen bg-bg text-ink px-6 py-10">
    <div class="mx-auto max-w-4xl">
      <div
        class="mb-6 inline-flex items-center gap-2 rounded-full bg-gold-soft px-3 py-1 text-xs font-extrabold text-gold"
      >
        <Flag :size="13" /> Données de démonstration synthétiques — M0 · fondations
      </div>

      <h1 class="font-display text-4xl font-extrabold tracking-tight text-ink">
        BMCI Carrière — <span class="text-green">La Courbe</span>
      </h1>
      <p class="mt-3 max-w-2xl leading-relaxed text-ink-2">
        Fondations du frontend <strong>Vue 3 + TypeScript</strong>. Cette page vérifie que la
        palette, les polices (Bricolage Grotesque + Hanken Grotesk, self-hostées) et Tailwind sont
        bien câblés — avant de construire le design system (M1).
      </p>

      <!-- Typographie -->
      <section class="mt-10">
        <h2 class="font-display text-lg font-bold text-ink-2">Typographie</h2>
        <div class="mt-3 rounded-2xl border border-border bg-paper p-6 shadow-card">
          <p class="font-display text-2xl font-extrabold text-ink">
            Bricolage Grotesque — titres &amp; chiffres clés
          </p>
          <p class="mt-2 text-ink-2">
            Hanken Grotesk — corps de texte, interface, tableaux et libellés. Votre carrière suit
            une <em class="text-green not-italic font-semibold">courbe</em>.
          </p>
        </div>
      </section>

      <!-- Primitives -->
      <section class="mt-8">
        <h2 class="font-display text-lg font-bold text-ink-2">Aperçu composants (bruts)</h2>
        <div class="mt-3 flex flex-wrap items-center gap-3">
          <button
            class="inline-flex items-center gap-2 rounded-xl bg-green px-4 py-2.5 text-sm font-semibold text-white shadow-green transition hover:brightness-105"
          >
            <Sparkles :size="16" /> Bouton principal
          </button>
          <button
            class="inline-flex items-center gap-2 rounded-xl border border-border-strong bg-paper px-4 py-2.5 text-sm font-semibold text-ink-2 transition hover:text-ink"
          >
            Bouton secondaire
          </button>
          <span
            class="inline-flex items-center gap-1 rounded-full bg-green-soft px-3 py-1 text-xs font-bold text-green-deep"
          >
            <TrendingUp :size="13" /> 88 % · Très adapté
          </span>
          <span
            class="inline-flex items-center gap-1 rounded-full bg-gold-soft px-3 py-1 text-xs font-bold text-gold"
          >
            <ShieldCheck :size="13" /> Objectif
          </span>
        </div>
      </section>

      <!-- Palette -->
      <section class="mt-10">
        <h2 class="font-display text-lg font-bold text-ink-2">Palette « La Courbe »</h2>
        <div class="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div
            v-for="[name, hex] in palette"
            :key="name"
            class="overflow-hidden rounded-xl border border-border bg-paper shadow-card"
          >
            <div class="h-14" :style="{ background: hex }" />
            <div class="px-3 py-2">
              <div class="text-xs font-semibold text-ink">{{ name }}</div>
              <div class="text-[11px] text-ink-3">{{ hex }}</div>
            </div>
          </div>
        </div>

        <div class="mt-5 flex items-center gap-2">
          <span class="mr-1 text-xs text-ink-3">Cartographie (niveau 1→5) :</span>
          <div
            v-for="[lvl, hex, light] in heat"
            :key="lvl"
            class="grid h-9 w-9 place-items-center rounded-md text-[11px] font-bold"
            :style="{ background: hex, color: light ? '#fff' : '#0E1A14' }"
          >
            {{ lvl + 1 }}
          </div>
        </div>
      </section>

      <p class="mt-12 text-xs text-ink-3">
        © 2026 BMCI · Groupe BNP Paribas — plateforme locale « La Courbe ». Maquette de
        démonstration, données synthétiques.
      </p>
    </div>
  </div>
</template>
