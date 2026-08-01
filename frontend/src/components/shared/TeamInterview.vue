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
 * L'humain est le vrai intervieweur (manager ou RH) : il pose ses questions, et
 * l'IA joue le rôle du collaborateur `subject` (ancrée sur son profil : rôle,
 * aspiration, écarts) et répond de façon réaliste, à la première personne. Le
 * framing est centralisé dans `persona`/`frame` (point de bascule si un mode
 * backend dédié arrive). Générique : sert manager↔équipe et RH↔collaborateur.
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

function persona(): string {
  const m = props.subject
  const poste = `${m.role}${m.pole ? ` · ${m.pole}` : ''}`
  const asp = m.aspiration ? `Ton aspiration : « ${m.aspiration} ». ` : ''
  const gaps = m.gaps?.length ? `Points à développer : ${m.gaps.join(', ')}. ` : ''
  return (
    `[Tu INCARNES ${m.name}, ${poste}, reçu(e) pour ton entretien annuel. ${asp}${gaps}Réponds aux ` +
    `questions de ton intervieweur de façon réaliste et cohérente avec ce profil, à la PREMIÈRE ` +
    `PERSONNE, en 2 à 3 phrases. Reste STRICTEMENT dans le personnage : ne joue pas l'intervieweur, ` +
    `ne donne pas de méta-commentaire, ne parle pas d'offres ni de catalogue de formations. Français.]`
  )
}
function frameOpen(): string {
  return `${persona()}\n\nSalue brièvement ton intervieweur en début d'entretien annuel (1 phrase) et dis que tu es prêt(e).`
}
function frame(question: string): string {
  return `${persona()}\n\nQuestion de l'intervieweur : ${question}`
}

async function runTurn(framed: string) {
  if (busy.value) return
  busy.value = true
  streamStatus.value = ''
  streamingHtml.value = ''
  let raw = ''
  const history = [...chat.value]
  try {
    await apiService.streamCoachMessage(framed, history, {
      onTool: () => { streamStatus.value = `${props.subject.name} réfléchit…` },
      onToken: (tk) => { streamStatus.value = ''; raw += tk; streamingHtml.value = formatCoachReply(raw) },
      onReset: () => { raw = ''; streamingHtml.value = '' },
    })
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
  await runTurn(frame(t))
}

onMounted(() => runTurn(frameOpen()))
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
