<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import { Sparkles, Send, MessageSquare } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { formatCoachReply } from '@/services/coachFormat'
import type { ChatMessage } from '@/types/domain'
import BaseButton from '@/components/ui/BaseButton.vue'

/**
 * Entretien annuel MENÉ par l'utilisateur, où l'IA INCARNE la personne interrogée.
 *
 * Le RÔLE est NATIF côté backend (mode `entretien_roleplay`) : le backend construit
 * le personnage à partir du `sujet` envoyé (nom/poste/aspiration/écarts/pôle) et
 * n'utilise aucun outil. Le front ne fait que déclarer le mode + le sujet + le tour.
 * Générique : sert manager↔équipe et RH↔collaborateur.
 */

export interface InterviewSubject {
  name: string
  role: string
  aspiration?: string
  gaps?: string[]
  pole?: string
}

const props = defineProps<{ subject: InterviewSubject }>()

// Trame indicative pour guider l'intervieweur (non contraignante).
const TRAME = [
  'Objectifs & missions',
  'Réussites',
  'Échecs & difficultés',
  'Compétences',
  'Souhaits & perspectives',
  'Synthèse',
]

const chat = ref<ChatMessage[]>([])
const input = ref('')
const busy = ref(false)
const streamingHtml = ref('')
const streamStatus = ref('')
const scroller = ref<HTMLElement>()
const ERR = "Désolé, je n'ai pas pu répondre à l'instant. Réessayez dans un moment."

watch([() => chat.value.length, streamingHtml, streamStatus, busy], async () => {
  await nextTick()
  if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
})

/** Traduit le sujet (types front) vers le schéma backend `EntretienSujet`. */
function sujet() {
  const s = props.subject
  return { nom: s.name, poste: s.role, aspiration: s.aspiration, ecarts: s.gaps ?? [], pole: s.pole }
}

async function runTurn(message: string, ouverture: boolean) {
  if (busy.value) return
  busy.value = true
  streamStatus.value = ''
  streamingHtml.value = ''
  let raw = ''
  const history = [...chat.value]
  try {
    await apiService.streamCoachMessage(
      message,
      history,
      {
        onTool: () => { streamStatus.value = `${props.subject.name} réfléchit…` },
        onToken: (tk) => { streamStatus.value = ''; raw += tk; streamingHtml.value = formatCoachReply(raw) },
        onReset: () => { raw = ''; streamingHtml.value = '' },
      },
      { mode: 'entretien_roleplay', sujet: sujet(), ouverture },
    )
    chat.value.push({ from: 'bot', text: raw.trim() ? formatCoachReply(raw) : ERR })
  } catch {
    chat.value.push({ from: 'bot', text: ERR })
  } finally {
    busy.value = false
    streamStatus.value = ''
    streamingHtml.value = ''
  }
}

async function ask(text?: string) {
  const t = (text ?? input.value).trim()
  if (!t || busy.value) return
  chat.value.push({ from: 'me', text: t })
  input.value = ''
  await runTurn(t, false)
}

onMounted(() => runTurn('', true))
</script>

<template>
  <div class="grid gap-5 lg:grid-cols-[240px_1fr]">
    <div class="space-y-5">
      <div class="rounded-2xl border border-border bg-paper p-4 shadow-card">
        <div class="mb-3 text-xs font-semibold uppercase tracking-wide text-green-deep">Trame d'entretien</div>
        <div class="space-y-1">
          <div v-for="t in TRAME" :key="t" class="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm text-ink-2">
            <MessageSquare :size="15" class="text-ink-3" />
            <span>{{ t }}</span>
          </div>
        </div>
      </div>
      <div class="rounded-2xl border border-green-line bg-green-ghost p-4">
        <div class="mb-1 inline-flex items-center gap-1.5 text-xs font-bold text-green-deep">
          <Sparkles :size="13" /> Simulation d'entretien · IA
        </div>
        <p class="text-xs text-ink-2">
          Vous <b>menez</b> l'entretien : posez vos questions. <b>{{ subject.name }}</b> (IA) répond
          dans son rôle, selon son profil. Idéal pour vous entraîner à conduire l'échange.
        </p>
      </div>
    </div>

    <div class="flex min-h-[480px] flex-col rounded-2xl border border-border bg-paper p-4 shadow-card">
      <div ref="scroller" class="flex-1 space-y-3 overflow-y-auto">
        <div v-for="(m, i) in chat" :key="i" class="flex" :class="m.from === 'me' ? 'justify-end' : ''">
          <div
            class="max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed"
            :class="m.from === 'me' ? 'bg-green text-white' : 'bg-green-soft text-ink-2'"
          >
            <span v-if="m.from === 'bot'" v-html="m.text" />
            <span v-else>{{ m.text }}</span>
          </div>
        </div>

        <div v-if="busy" class="flex">
          <div class="max-w-[80%] rounded-2xl bg-green-soft px-3.5 py-2.5 text-sm leading-relaxed text-ink-2">
            <template v-if="streamingHtml">
              <span v-html="streamingHtml" /><span
                class="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse rounded-sm bg-green-deep align-middle"
              />
            </template>
            <span v-else class="inline-flex items-center gap-1.5 text-ink-3">
              <Sparkles :size="14" class="animate-pulse text-green-deep" />
              {{ streamStatus || `${subject.name} prépare sa réponse…` }}
            </span>
          </div>
        </div>
      </div>

      <div class="mt-3 flex items-center gap-2 rounded-xl border border-border bg-panel px-3 py-2">
        <MessageSquare :size="16" class="shrink-0 text-green-deep" />
        <input
          v-model="input"
          placeholder="Posez votre question au collaborateur…"
          :disabled="busy"
          class="w-full bg-transparent text-sm outline-none placeholder:text-ink-3 disabled:opacity-60"
          @keydown.enter="ask()"
        />
        <BaseButton size="sm" :disabled="busy || !input.trim()" @click="ask()">
          <Send :size="14" /> Demander
        </BaseButton>
      </div>
    </div>
  </div>
</template>
