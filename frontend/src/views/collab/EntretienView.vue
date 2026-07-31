<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Check, MessageSquare, Clock, Sparkles, Send, ArrowRight } from '@lucide/vue'
import { useSessionStore } from '@/stores/session'
import { apiService } from '@/services/apiService'
import { formatCoachReply } from '@/services/coachFormat'
import type { ChatMessage } from '@/types/domain'
import BaseButton from '@/components/ui/BaseButton.vue'

/**
 * Entretien annuel piloté par l'IA, étape par étape.
 *
 * Le Coach agentique n'a pas de « mode entretien » côté backend (system-prompt
 * fixe). On le pilote donc DEPUIS le front : chaque tour envoie une CONSIGNE
 * d'intervieweur (invisible à l'écran) + l'étape courante. Toute la logique de
 * framing est centralisée dans `frameOpen` / `frameAnswer` : le jour où le
 * backend expose un vrai mode « entretien » (mode + step), il suffira de
 * remplacer ces deux helpers par le passage du `step` au service.
 */

const session = useSessionStore()

const STEPS: { label: string; focus: string }[] = [
  { label: 'Introduction', focus: "accueille chaleureusement et rappelle en une phrase le cadre bienveillant de l'entretien annuel" },
  { label: 'Bilan des réussites', focus: "ses principales réussites de l'année (encourage la méthode STAR et les résultats chiffrés)" },
  { label: 'Objectifs 2026', focus: "ses objectifs et priorités pour l'année à venir" },
  { label: 'Compétences & soft skills', focus: "les compétences développées et ses axes de progression (savoir-être inclus)" },
  { label: 'Souhaits de formation', focus: "ses besoins et souhaits de formation / développement" },
  { label: 'Synthèse finale', focus: "récapitule l'entretien en 4-5 puces (réussites, objectifs, formations retenues) et conclus positivement" },
]

const currentStep = ref(0)
const chat = ref<ChatMessage[]>([])
const input = ref('')
const busy = ref(false)
const streamingHtml = ref('')
const streamStatus = ref('')
const scroller = ref<HTMLElement>()

const ERR = "Désolé, je n'ai pas pu répondre à l'instant. Réessayez dans un moment."
const atLastStep = computed(() => currentStep.value >= STEPS.length - 1)
const progressPct = computed(() => Math.round(((currentStep.value + 1) / STEPS.length) * 100))
function stepState(i: number): 'done' | 'current' | 'todo' {
  return i < currentStep.value ? 'done' : i === currentStep.value ? 'current' : 'todo'
}

watch([() => chat.value.length, streamingHtml, streamStatus, busy], async () => {
  await nextTick()
  if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
})

/* ---- Framing intervieweur (centralisé : point de bascule backend futur) ---- */
function persona(): string {
  const nom = session.user?.name || 'le collaborateur'
  const poste = session.user?.title ? ` (${session.user.title})` : ''
  return `${nom}${poste}`
}
function consigne(stepIdx: number): string {
  return (
    `[Tu es le MANAGER qui mène l'entretien annuel de ${persona()}. ` +
    `Étape en cours : « ${STEPS[stepIdx].label} ». Reste STRICTEMENT dans ce rôle d'intervieweur RH ` +
    `bienveillant. Ne parle ni d'offres internes ni du catalogue de formations. ` +
    `Réponds en français, 2 à 3 phrases maximum.]`
  )
}
function frameOpen(stepIdx: number): string {
  const s = STEPS[stepIdx]
  const consigneFin = atLastStepIdx(stepIdx)
    ? `Fais la synthèse : ${s.focus}.`
    : `Ouvre cette étape : ${s.focus}. Termine par UNE seule question ouverte.`
  return `${consigne(stepIdx)}\n\n${consigneFin}`
}
function frameAnswer(stepIdx: number, userText: string): string {
  return (
    `${consigne(stepIdx)}\n\n` +
    `Réagis brièvement à sa réponse (1 phrase), puis pose UNE seule question pour approfondir ` +
    `« ${STEPS[stepIdx].label} ».\n\nRéponse du collaborateur : ${userText}`
  )
}
function atLastStepIdx(i: number): boolean {
  return i >= STEPS.length - 1
}

/* ---- Cœur : un tour streamé (la consigne n'est jamais affichée) ---- */
async function runTurn(framed: string) {
  if (busy.value) return
  busy.value = true
  streamStatus.value = ''
  streamingHtml.value = ''
  let raw = ''
  const history = [...chat.value] // messages affichés uniquement (sans consignes)
  try {
    await apiService.streamCoachMessage(framed, history, {
      onTool: () => { streamStatus.value = 'Le manager consulte votre dossier…' },
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

async function answer(text?: string) {
  const t = (text ?? input.value).trim()
  if (!t || busy.value) return
  chat.value.push({ from: 'me', text: t })
  input.value = ''
  await runTurn(frameAnswer(currentStep.value, t))
}

async function nextStep() {
  if (busy.value || atLastStep.value) return
  currentStep.value++
  await runTurn(frameOpen(currentStep.value))
}

// Démarrage : le manager ouvre l'introduction avec une vraie question.
onMounted(() => runTurn(frameOpen(0)))
</script>

<template>
  <div class="grid gap-5 lg:grid-cols-[240px_1fr]">
    <div class="space-y-5">
      <div class="rounded-2xl border border-border bg-paper p-4 shadow-card">
        <div class="mb-3 text-xs font-semibold uppercase tracking-wide text-green-deep">Étapes</div>
        <div class="space-y-1">
          <div
            v-for="(s, i) in STEPS"
            :key="s.label"
            class="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm"
            :class="stepState(i) === 'current' ? 'bg-green-soft font-semibold text-green-deep' : 'text-ink-2'"
          >
            <Check v-if="stepState(i) === 'done'" :size="15" class="text-green" />
            <MessageSquare v-else-if="stepState(i) === 'current'" :size="15" />
            <Clock v-else :size="15" class="text-ink-3" />
            <span>{{ s.label }}</span>
          </div>
        </div>
        <div class="mt-4">
          <div class="mb-1 flex justify-between text-xs">
            <span class="text-ink-3">Progression</span><b class="text-green-deep">{{ progressPct }} %</b>
          </div>
          <div class="h-2 overflow-hidden rounded-full bg-panel-2">
            <div class="h-full rounded-full bg-green transition-all" :style="{ width: progressPct + '%' }" />
          </div>
        </div>
        <BaseButton
          v-if="!atLastStep"
          block
          size="sm"
          class="mt-4"
          :disabled="busy"
          @click="nextStep"
        >
          Passer à l'étape suivante <ArrowRight :size="15" />
        </BaseButton>
        <p v-else class="mt-4 rounded-lg bg-green-soft px-3 py-2 text-xs font-semibold text-green-deep">
          Dernière étape — le manager rédige la synthèse.
        </p>
      </div>

      <div class="rounded-2xl border border-green-line bg-green-ghost p-4">
        <div class="mb-1 inline-flex items-center gap-1.5 text-xs font-bold text-green-deep">
          <Sparkles :size="13" /> Entretien IA en direct
        </div>
        <p class="text-xs text-ink-2">
          Votre manager (IA) mène l'entretien étape par étape et réagit à vos réponses réelles. Répondez
          naturellement, puis avancez avec « Passer à l'étape suivante ».
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

        <!-- Bulle vivante pendant le streaming -->
        <div v-if="busy" class="flex">
          <div class="max-w-[80%] rounded-2xl bg-green-soft px-3.5 py-2.5 text-sm leading-relaxed text-ink-2">
            <template v-if="streamingHtml">
              <span v-html="streamingHtml" /><span
                class="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse rounded-sm bg-green-deep align-middle"
              />
            </template>
            <span v-else class="inline-flex items-center gap-1.5 text-ink-3">
              <Sparkles :size="14" class="animate-pulse text-green-deep" />
              {{ streamStatus || 'Le manager prépare l’entretien…' }}
            </span>
          </div>
        </div>
      </div>

      <div class="mt-3 flex items-center gap-2 rounded-xl border border-border bg-panel px-3 py-2">
        <MessageSquare :size="16" class="shrink-0 text-green-deep" />
        <input
          v-model="input"
          :placeholder="atLastStep ? 'Un dernier mot avant de clôturer…' : 'Répondez au manager…'"
          :disabled="busy"
          class="w-full bg-transparent text-sm outline-none placeholder:text-ink-3 disabled:opacity-60"
          @keydown.enter="answer()"
        />
        <BaseButton size="sm" :disabled="busy || !input.trim()" @click="answer()">
          <Send :size="14" /> Répondre
        </BaseButton>
      </div>
    </div>
  </div>
</template>
