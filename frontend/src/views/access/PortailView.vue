<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Lock, ShieldCheck, TrendingUp, Flag } from '@lucide/vue'
import BaseButton from '@/components/ui/BaseButton.vue'

const router = useRouter()
</script>

<template>
  <div class="min-h-screen bg-bg">
    <div class="mx-auto grid max-w-6xl gap-10 px-6 py-12 lg:grid-cols-2 lg:items-center">
      <div>
        <div
          class="mb-5 inline-flex items-center gap-2 rounded-full bg-gold-soft px-3 py-1 text-xs font-extrabold text-gold"
        >
          <Flag :size="13" /> Démo · données synthétiques (aucune donnée réelle BMCI)
        </div>
        <div class="mb-6 flex items-center gap-2.5">
          <div
            class="grid h-10 w-10 place-items-center rounded-xl bg-green font-display text-xl font-extrabold text-white"
          >
            B
          </div>
          <div>
            <div class="text-sm font-bold text-ink">BMCI · Gestion de carrière</div>
            <div class="text-[11px] text-ink-3">Groupe BNP Paribas</div>
          </div>
        </div>

        <h1 class="font-display text-4xl font-extrabold leading-tight tracking-tight text-ink">
          Votre carrière suit une <span class="text-green">courbe</span>. Donnez-lui de l'élan.
        </h1>
        <p class="mt-4 max-w-lg text-ink-2">
          Une plateforme qui relie vos entretiens, vos compétences et les opportunités internes du
          Groupe — pour tracer, avec vous, la suite du parcours.
        </p>

        <div class="mt-6 flex flex-wrap gap-3">
          <BaseButton @click="router.push({ name: 'connexion' })">
            <Lock :size="16" /> Se connecter
          </BaseButton>
          <BaseButton variant="secondary" @click="router.push({ name: 'inscription' })">
            Première visite ? Créer un compte
          </BaseButton>
        </div>

        <div class="mt-8 flex gap-8">
          <div>
            <div class="font-display text-2xl font-extrabold text-ink">2 850</div>
            <div class="text-xs text-ink-3">Collaborateurs</div>
          </div>
          <div>
            <div class="font-display text-2xl font-extrabold text-ink">450</div>
            <div class="text-xs text-ink-3">Formations</div>
          </div>
          <div>
            <div class="font-display text-2xl font-extrabold text-ink">92 %</div>
            <div class="text-xs text-ink-3">Satisfaction</div>
          </div>
        </div>

        <div class="mt-6 flex flex-wrap gap-4 text-xs text-ink-3">
          <span class="inline-flex items-center gap-1"><ShieldCheck :size="14" /> Connexion sécurisée</span>
          <span class="inline-flex items-center gap-1"><TrendingUp :size="14" /> 100 % interne au Groupe</span>
        </div>
      </div>

      <div class="hidden lg:block">
        <div class="rounded-3xl border border-border bg-paper p-8 shadow-float">
          <div class="text-xs font-bold uppercase tracking-wide text-green-deep">
            Prochaine station
          </div>
          <div class="mt-1 flex items-baseline justify-between">
            <span class="font-display text-xl font-extrabold text-ink">Manager de Pôle</span>
            <span class="font-display text-2xl font-extrabold text-green-deep">92 %</span>
          </div>
          <div class="mt-3 h-2 overflow-hidden rounded-full bg-panel-2">
            <div class="h-full rounded-full bg-green" style="width: 78%" />
          </div>
          <p class="mt-4 text-sm text-ink-2">
            « La Courbe » relie compétences, aspirations et opportunités pour éclairer chaque
            prochaine étape.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
