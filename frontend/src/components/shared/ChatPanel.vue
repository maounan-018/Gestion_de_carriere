<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { Send, Sparkles } from '@lucide/vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import type { ChatMessage, ChatSuggestion } from '@/types/domain'
import type { CoachStreamHandlers } from '@/services/apiService'
import { formatCoachReply } from '@/services/coachFormat'

// Priorité des modes de réponse :
//  1. `onStream` -> chat LIVE en STREAMING (tokens au fil de l'eau + statut d'outil).
//  2. `onSend`   -> chat LIVE bloquant (une réponse complète, avec indicateur d'attente).
//  3. `botReply` -> repli statique (simulations d'entretien, démo).
const props = defineProps<{
  messages: ChatMessage[]
  suggestions?: ChatSuggestion[]
  placeholder?: string
  botReply?: string
  onSend?: (message: string, history: ChatMessage[]) => Promise<string>
  onStream?: (
    message: string,
    history: ChatMessage[],
    handlers: CoachStreamHandlers,
  ) => Promise<void>
}>()

const list = ref<ChatMessage[]>([...props.messages])
const input = ref('')
const busy = ref(false)
const streamingHtml = ref('') // bulle bot en cours de streaming (HTML échappé)
const streamStatus = ref('') // libellé de l'outil interrogé ('' sinon)
const scroller = ref<HTMLElement>()

const ERR = "Désolé, je n'ai pas pu répondre à l'instant. Réessayez dans un moment."

// Libellés lisibles des outils du coach agentique (voir backend `_DISPATCH`).
const TOOL_LABELS: Record<string, string> = {
  chercher_offres_compatibles: 'Consultation des offres internes…',
  lister_formations: 'Consultation du catalogue de formations…',
}

// Auto-scroll en bas à chaque nouveau contenu (messages, tokens, statut).
watch([() => list.value.length, streamingHtml, streamStatus, busy], async () => {
  await nextTick()
  if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
})

async function streamSend(text: string, history: ChatMessage[]) {
  busy.value = true
  streamStatus.value = ''
  streamingHtml.value = ''
  let raw = ''
  try {
    await props.onStream!(text, history, {
      onTool: (name) => {
        streamStatus.value = TOOL_LABELS[name] ?? 'Consultation des données…'
      },
      onToken: (tk) => {
        streamStatus.value = ''
        raw += tk
        streamingHtml.value = formatCoachReply(raw)
      },
      onReset: () => {
        raw = ''
        streamingHtml.value = ''
      },
    })
    list.value.push({ from: 'bot', text: raw.trim() ? formatCoachReply(raw) : ERR })
  } catch {
    list.value.push({ from: 'bot', text: ERR })
  } finally {
    busy.value = false
    streamStatus.value = ''
    streamingHtml.value = ''
  }
}

async function send(text?: string) {
  const t = (text ?? input.value).trim()
  if (!t || busy.value) return
  const history = [...list.value] // tours précédents (avant ce message)
  list.value.push({ from: 'me', text: t })
  input.value = ''

  if (props.onStream) {
    await streamSend(t, history)
  } else if (props.onSend) {
    busy.value = true
    try {
      const reply = await props.onSend(t, history)
      list.value.push({ from: 'bot', text: reply })
    } catch {
      list.value.push({ from: 'bot', text: ERR })
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
    <div ref="scroller" class="flex-1 space-y-3 overflow-y-auto">
      <div v-for="(m, i) in list" :key="i" class="flex" :class="m.from === 'me' ? 'justify-end' : ''">
        <div
          class="max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed"
          :class="m.from === 'me' ? 'bg-green text-white' : 'bg-green-soft text-ink-2'"
        >
          <span v-if="m.from === 'bot'" v-html="m.text" />
          <span v-else>{{ m.text }}</span>
        </div>
      </div>

      <!-- Bulle vivante pendant le streaming : statut d'outil, puis tokens en direct. -->
      <div v-if="busy && onStream" class="flex">
        <div class="max-w-[80%] rounded-2xl bg-green-soft px-3.5 py-2.5 text-sm leading-relaxed text-ink-2">
          <template v-if="streamingHtml">
            <span v-html="streamingHtml" /><span
              class="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse rounded-sm bg-green-deep align-middle"
            />
          </template>
          <span v-else class="inline-flex items-center gap-1.5 text-ink-3">
            <Sparkles :size="14" class="animate-pulse text-green-deep" />
            {{ streamStatus || 'Le Coach réfléchit…' }}
          </span>
        </div>
      </div>

      <!-- Indicateur d'attente pour le mode bloquant (onSend). -->
      <div v-if="busy && !onStream" class="flex">
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
