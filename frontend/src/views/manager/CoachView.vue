<script setup lang="ts">
import { Sparkles } from '@lucide/vue'
import { useSessionStore } from '@/stores/session'
import ChatPanel from '@/components/shared/ChatPanel.vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import type { ChatMessage, ChatSuggestion } from '@/types/domain'
import { apiService, type CoachStreamHandlers } from '@/services/apiService'

const askCoach = (message: string, history: ChatMessage[], h: CoachStreamHandlers) =>
  apiService.streamCoachMessage(message, history, h)
const session = useSessionStore()
const messages: ChatMessage[] = [
  {
    from: 'bot',
    text: `Bonjour ${session.user?.firstName || 'Jean-Marc'} 👋 Je suis votre <b>Coach Carrière</b>. Je connais votre parcours, votre équipe et vos objectifs.`,
  },
  {
    from: 'bot',
    text: 'Par exemple : « Comment évoluer vers <b>Directeur Exécutif</b> ? » ou « Comment développer Aya vers un rôle de manager ? »',
  },
]
const suggestions: ChatSuggestion[] = [
  { label: 'Évoluer vers Directeur Exécutif', q: 'Comment évoluer vers Directeur Exécutif ?' },
  { label: 'Développer un talent', q: 'Comment développer Aya vers un rôle de manager ?' },
  { label: 'Préparer un entretien', q: 'Aide-moi à préparer un entretien annuel.' },
]
</script>

<template>
  <div class="grid gap-5 lg:grid-cols-[1fr_300px]">
    <ChatPanel
      :messages="messages"
      :suggestions="suggestions"
      placeholder="Posez votre question au Coach…"
      :on-stream="askCoach"
    />
    <div class="space-y-4">
      <BaseCard>
        <div class="mb-2 inline-flex items-center gap-1.5 rounded-full border border-green-line bg-green-ghost px-2.5 py-0.5 text-[11px] font-bold text-green-deep">
          <Sparkles :size="13" /> Confidentiel
        </div>
        <p class="text-sm text-ink-3">
          Vos échanges avec le Coach restent strictement privés · ni votre hiérarchie ni la RH n'y
          ont accès.
        </p>
      </BaseCard>
      <BaseCard title="Ce que je sais de vous">
        <ul class="space-y-2 text-sm text-ink-2">
          <li class="flex gap-2"><span class="text-green-deep">•</span> Directeur de Pôle Risques · 8 collaborateurs</li>
          <li class="flex gap-2"><span class="text-green-deep">•</span> Objectif : Directeur Exécutif (horizon 2 ans)</li>
          <li class="flex gap-2"><span class="text-green-deep">•</span> À développer : vision stratégique, influence COMEX</li>
        </ul>
      </BaseCard>
    </div>
  </div>
</template>
