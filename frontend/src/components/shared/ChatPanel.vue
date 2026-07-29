<script setup lang="ts">
import { ref } from 'vue'
import { Send, Sparkles } from '@lucide/vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import type { ChatMessage, ChatSuggestion } from '@/types/domain'

// `onSend` fourni -> chat LIVE (appel backend, avec indicateur d'attente).
// Sinon -> repli sur `botReply` statique (simulations d'entretien, démo).
const props = defineProps<{
  messages: ChatMessage[]
  suggestions?: ChatSuggestion[]
  placeholder?: string
  botReply?: string
  onSend?: (message: string, history: ChatMessage[]) => Promise<string>
}>()

const list = ref<ChatMessage[]>([...props.messages])
const input = ref('')
const busy = ref(false)

async function send(text?: string) {
  const t = (text ?? input.value).trim()
  if (!t || busy.value) return
  const history = [...list.value] // tours précédents (avant ce message)
  list.value.push({ from: 'me', text: t })
  input.value = ''

  if (props.onSend) {
    busy.value = true
    try {
      const reply = await props.onSend(t, history)
      list.value.push({ from: 'bot', text: reply })
    } catch {
      list.value.push({
        from: 'bot',
        text: "Désolé, je n'ai pas pu répondre à l'instant. Réessayez dans un moment.",
      })
    } finally {
      busy.value = false
    }
  } else {
    window.setTimeout(
      () => list.value.push({ from: 'bot', text: props.botReply || 'Je prépare une réponse…' }),
      300,
    )
  }
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
      <div v-if="busy" class="flex">
        <div class="rounded-2xl bg-green-soft px-3.5 py-2.5 text-sm text-ink-3">
          <span class="inline-flex items-center gap-1.5">
            <Sparkles :size="14" class="animate-pulse text-green-deep" /> Le Coach réfléchit…
          </span>
        </div>
      </div>
    </div>

    <div v-if="suggestions?.length" class="mt-3 flex flex-wrap gap-2">
      <button
        v-for="s in suggestions"
        :key="s.label"
        :disabled="busy"
        class="rounded-full border border-green-line bg-green-ghost px-3 py-1 text-xs font-semibold text-green-deep transition hover:bg-green-wash disabled:opacity-50"
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
        :disabled="busy"
        class="w-full bg-transparent text-sm outline-none placeholder:text-ink-3 disabled:opacity-60"
        @keydown.enter="send()"
      />
      <BaseButton size="sm" :disabled="busy" @click="send()"><Send :size="14" /> Envoyer</BaseButton>
    </div>
  </div>
</template>
