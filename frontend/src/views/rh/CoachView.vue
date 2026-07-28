<script setup lang="ts">
import { Sparkles } from '@lucide/vue'
import { useSessionStore } from '@/stores/session'
import ChatPanel from '@/components/shared/ChatPanel.vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import type { ChatMessage, ChatSuggestion } from '@/types/domain'

const session = useSessionStore()
const messages: ChatMessage[] = [
  {
    from: 'bot',
    text: `Bonjour ${session.user?.firstName || 'Nadia'} 👋 Je suis votre <b>Coach Carrière</b>. Je connais votre parcours RH et vos objectifs.`,
  },
  {
    from: 'bot',
    text: 'Par exemple : « Comment évoluer vers <b>Directrice des Talents</b> ? » ou « Quelles compétences développer en people analytics ? »',
  },
]
const suggestions: ChatSuggestion[] = [
  { label: 'Évoluer vers Directrice des Talents', q: 'Comment évoluer vers Directrice des Talents ?' },
  { label: 'Renforcer le people analytics', q: 'Quelles compétences développer en people analytics ?' },
]
</script>

<template>
  <div class="grid gap-5 lg:grid-cols-[1fr_300px]">
    <ChatPanel
      :messages="messages"
      :suggestions="suggestions"
      placeholder="Posez votre question au Coach…"
      bot-reply="Je m'appuie sur votre profil pour vous répondre. Précisez l'objectif et je vous propose un plan."
    />
    <BaseCard>
      <div class="mb-2 inline-flex items-center gap-1.5 rounded-full border border-green-line bg-green-ghost px-2.5 py-0.5 text-[11px] font-bold text-green-deep">
        <Sparkles :size="13" /> Confidentiel
      </div>
      <p class="text-sm text-ink-3">Vos échanges avec le Coach restent strictement privés.</p>
    </BaseCard>
  </div>
</template>
