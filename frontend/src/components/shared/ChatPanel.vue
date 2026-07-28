<script setup lang="ts">
import { ref } from 'vue'
import { Send, Sparkles } from '@lucide/vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import type { ChatMessage, ChatSuggestion } from '@/types/domain'

const props = defineProps<{
  messages: ChatMessage[]
  suggestions?: ChatSuggestion[]
  placeholder?: string
  botReply?: string
}>()

const list = ref<ChatMessage[]>([...props.messages])
const input = ref('')

function send(text?: string) {
  const t = (text ?? input.value).trim()
  if (!t) return
  list.value.push({ from: 'me', text: t })
  input.value = ''
  window.setTimeout(
    () => list.value.push({ from: 'bot', text: props.botReply || "Je prépare une réponse à partir de votre profil et de vos données de carrière…" }),
    300,
  )
}
</script>

<template>
  <div class="flex min-h-[440px] flex-col rounded-2xl border border-border bg-paper p-4 shadow-card">
    <div class="flex-1 space-y-3 overflow-y-auto">
      <div v-for="(m, i) in list" :key="i" class="flex" :class="m.from === 'me' ? 'justify-end' : ''">
        <div
          class="max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed"
          :class="m.from === 'me' ? 'bg-green text-white' : 'bg-green-soft text-ink-2'"
        >
          <span v-if="m.from === 'bot'" v-html="m.text" />
          <span v-else>{{ m.text }}</span>
        </div>
      </div>
    </div>

    <div v-if="suggestions?.length" class="mt-3 flex flex-wrap gap-2">
      <button
        v-for="s in suggestions"
        :key="s.label"
        class="rounded-full border border-green-line bg-green-ghost px-3 py-1 text-xs font-semibold text-green-deep transition hover:bg-green-wash"
        @click="send(s.q)"
      >
        {{ s.label }}
      </button>
    </div>

    <div class="mt-3 flex items-center gap-2 rounded-xl border border-border bg-panel px-3 py-2">
      <Sparkles :size="16" class="shrink-0 text-green-deep" />
      <input
        v-model="input"
        :placeholder="placeholder || 'Écrivez votre message…'"
        class="w-full bg-transparent text-sm outline-none placeholder:text-ink-3"
        @keydown.enter="send()"
      />
      <BaseButton size="sm" @click="send()"><Send :size="14" /> Envoyer</BaseButton>
    </div>
  </div>
</template>
