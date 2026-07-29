<script setup lang="ts">
import { Shield } from '@lucide/vue'
import ChatPanel from '@/components/shared/ChatPanel.vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { ChatMessage, ChatSuggestion } from '@/types/domain'
import { apiService, type CoachStreamHandlers } from '@/services/apiService'

const askCoach = (message: string, history: ChatMessage[], h: CoachStreamHandlers) =>
  apiService.streamCoachMessage(message, history, h)

const messages: ChatMessage[] = [
  { from: 'bot', text: 'Bonjour Marc 👋 Je suis votre <b>Coach Carrière</b>. Je connais votre parcours, vos compétences et vos souhaits : posez-moi vos questions sur votre évolution, en toute confidentialité.' },
  { from: 'bot', text: "Par exemple : « Comment évoluer vers <b>Manager d'équipe Risques</b> ? » ou « Quelles formations suivre cette année ? »" },
]
const suggestions: ChatSuggestion[] = [
  { label: 'Évoluer vers Manager', q: "Comment évoluer vers Manager d'équipe Risques ?" },
  { label: 'Quelles formations ?', q: 'Quelles formations suivre cette année ?' },
  { label: 'Mes forces', q: 'Quelles sont mes principales forces ?' },
]

const topics = [
  { icon: 'route' as const, label: 'Votre trajectoire de carrière' },
  { icon: 'spark' as const, label: 'Compétences à développer' },
  { icon: 'brief' as const, label: 'Offres et mobilité interne' },
  { icon: 'book' as const, label: 'Formations recommandées' },
]
</script>

<template>
  <div class="grid gap-5 lg:grid-cols-[1fr_280px]">
    <div class="space-y-2">
      <ChatPanel
        :messages="messages"
        :suggestions="suggestions"
        placeholder="Posez votre question au Coach…"
        :on-stream="askCoach"
      />
      <p class="text-center text-[11px] text-ink-3">
        <Shield :size="12" class="inline" /> Échanges 100 % confidentiels · ni votre manager ni les RH n'y ont accès.
      </p>
    </div>

    <BaseCard title="Sujets fréquents">
      <div class="space-y-2">
        <div v-for="t in topics" :key="t.label" class="flex items-center gap-2.5 rounded-lg border border-border bg-panel px-3 py-2 text-sm text-ink-2">
          <div class="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-green-soft text-green-deep"><AppIcon :name="t.icon" :size="14" /></div>
          {{ t.label }}
        </div>
      </div>
    </BaseCard>
  </div>
</template>
