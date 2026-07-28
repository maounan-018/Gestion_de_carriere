<script setup lang="ts">
import { Check, MessageSquare, Clock, Sparkles } from '@lucide/vue'
import ChatPanel from '@/components/shared/ChatPanel.vue'
import type { ChatMessage, ChatSuggestion } from '@/types/domain'

const messages: ChatMessage[] = [
  { from: 'bot', text: 'Bonjour Marc 👋 Préparons votre <b>entretien annuel</b>. Commençons par le bilan : quelles ont été vos <b>trois principales réussites</b> cette année ?' },
  { from: 'bot', text: 'Astuce : structurez avec la méthode <b>STAR</b> (Situation, Tâche, Action, Résultat chiffré).' },
]
const suggestions: ChatSuggestion[] = [
  { label: 'Mes réussites', q: 'Mes principales réussites cette année' },
  { label: 'Objectifs 2026', q: 'Quels objectifs pour 2026 ?' },
  { label: 'Mes souhaits', q: 'Je souhaite évoluer vers un rôle de manager' },
]

const steps = [
  { label: 'Introduction', state: 'done' },
  { label: 'Bilan des réussites', state: 'current' },
  { label: 'Objectifs 2026', state: 'todo' },
  { label: 'Compétences & soft skills', state: 'todo' },
  { label: 'Souhaits de formation', state: 'todo' },
  { label: 'Synthèse finale', state: 'todo' },
]
</script>

<template>
  <div class="grid gap-5 lg:grid-cols-[240px_1fr]">
    <div class="space-y-5">
      <div class="rounded-2xl border border-border bg-paper p-4 shadow-card">
        <div class="mb-3 text-xs font-semibold uppercase tracking-wide text-green-deep">Étapes</div>
        <div class="space-y-1">
          <div
            v-for="s in steps"
            :key="s.label"
            class="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm"
            :class="s.state === 'current' ? 'bg-green-soft font-semibold text-green-deep' : 'text-ink-2'"
          >
            <Check v-if="s.state === 'done'" :size="15" class="text-green" />
            <MessageSquare v-else-if="s.state === 'current'" :size="15" />
            <Clock v-else :size="15" class="text-ink-3" />
            <span>{{ s.label }}</span>
          </div>
        </div>
        <div class="mt-4">
          <div class="mb-1 flex justify-between text-xs"><span class="text-ink-3">Progression</span><b class="text-green-deep">25 %</b></div>
          <div class="h-2 overflow-hidden rounded-full bg-panel-2"><div class="h-full w-1/4 rounded-full bg-green" /></div>
        </div>
      </div>

      <div class="rounded-2xl border border-green-line bg-green-ghost p-4">
        <div class="mb-1 inline-flex items-center gap-1.5 text-xs font-bold text-green-deep"><Sparkles :size="13" /> Coach en ligne</div>
        <p class="text-xs text-ink-2">Le Coach analyse vos réponses en temps réel et vous suggère des relances et des mots-clés valorisants.</p>
      </div>
    </div>

    <ChatPanel
      :messages="messages"
      :suggestions="suggestions"
      placeholder="Décrivez votre réussite…"
      bot-reply="Bien noté. Pouvez-vous chiffrer l'impact (gain, %, délai) ? Cela renforcera votre bilan."
    />
  </div>
</template>
