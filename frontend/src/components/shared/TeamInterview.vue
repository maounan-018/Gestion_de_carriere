<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { Sparkles, Send, MessageSquare, Check, Clock, FileText, Download } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { formatCoachReply } from '@/services/coachFormat'
import { useToast } from '@/composables/useToast'
import { downloadPdf, type PdfBlock } from '@/utils/pdf'
import type { ChatMessage } from '@/types/domain'
import BaseButton from '@/components/ui/BaseButton.vue'

const { toast } = useToast()

/**
 * Préparation GUIDÉE de l'entretien d'un COLLABORATEUR par son MANAGER.
 *
 * L'IA n'incarne PLUS le collaborateur : elle est le COPILOTE du manager. Elle
 * l'interroge section par section SUR son collaborateur (objectifs, réussites,
 * difficultés, compétences, souhaits) ; le manager répond à son propos ; l'IA lui
 * donne un retour puis des conseils pour conduire l'entretien. Mode backend natif
 * `entretien_copilote_equipe`, ancré sur le profil du collaborateur (sujet).
 */

export interface InterviewSubject {
  name: string
  role: string
  aspiration?: string
  gaps?: string[]
  pole?: string
}

const props = defineProps<{ subject: InterviewSubject }>()

const STEPS = computed<{ label: string; focus: string }[]>(() => {
  const n = props.subject.name
  return [
    { label: 'Introduction', focus: '' },
    { label: 'Objectifs & missions', focus: `le bilan des objectifs et missions de ${n} sur l'année écoulée` },
    { label: 'Réussites', focus: `les principales réussites de ${n} (faits concrets, résultats observés)` },
    { label: 'Difficultés', focus: `les difficultés rencontrées par ${n} et la façon de l'accompagner` },
    { label: 'Compétences', focus: `l'évaluation des compétences de ${n} et ses axes de progression` },
    { label: 'Aspirations & perspectives', focus: `les aspirations d'évolution, de mobilité ou de formation de ${n}` },
    { label: "Conseils de l'agent", focus: '' },
    { label: 'Synthèse finale', focus: '' },
  ]
})

const currentStep = ref(0)
const chat = ref<ChatMessage[]>([])
const input = ref('')
const busy = ref(false)
const streamingHtml = ref('')
const streamStatus = ref('')
const scroller = ref<HTMLElement>()
const synthesePlain = ref('')       // synthèse finale en texte brut (pour l'export PDF)
const ERR = "Désolé, je n'ai pas pu répondre à l'instant. Réessayez dans un moment."

const atLastStep = computed(() => currentStep.value >= STEPS.value.length - 1)
const progressPct = computed(() => Math.round((currentStep.value / (STEPS.value.length - 1)) * 100))
function stepState(i: number): 'done' | 'current' | 'todo' {
  return i < currentStep.value ? 'done' : i === currentStep.value ? 'current' : 'todo'
}

watch([() => chat.value.length, streamingHtml, streamStatus, busy], async () => {
  await nextTick()
  if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
})

/** Traduit le sujet (types front) vers le schéma backend `EntretienSujet`. */
function sujet() {
  const s = props.subject
  return { nom: s.name, poste: s.role, aspiration: s.aspiration, ecarts: s.gaps ?? [], pole: s.pole }
}

function isConseils(i: number): boolean {
  return i === STEPS.value.length - 2
}
function isLast(i: number): boolean {
  return i >= STEPS.value.length - 1
}
function openFocus(i: number): string {
  const s = STEPS.value[i]
  const n = props.subject.name
  if (i === 0) {
    return (
      `INTRODUCTION UNIQUEMENT. Présente-toi en une phrase comme le copilote du manager pour préparer `
      + `l'entretien annuel de ${n}. Explique en une phrase que vous allez parcourir ensemble, section par `
      + `section (objectifs, réussites, difficultés, compétences, souhaits), pour préparer cet entretien. `
      + `NE traite PAS encore le contenu. Termine en demandant au manager s'il est prêt à commencer.`
    )
  }
  if (isConseils(i)) {
    return (
      `En te fondant PRÉCISÉMENT sur ce que le manager a partagé, donne-lui 2 ou 3 conseils concrets pour `
      + `conduire l'entretien de ${n} (posture, points à valoriser, sujets à aborder avec tact). Termine en `
      + `lui demandant s'il souhaite ajuster un point.`
    )
  }
  if (isLast(i)) {
    return (
      `Fais une synthèse structurée de la préparation (bilan des objectifs, réussites, difficultés, axes de `
      + `progrès, souhaits) pour l'entretien de ${n}, en te fondant sur les réponses du manager. Termine en `
      + `l'encourageant pour l'entretien.`
    )
  }
  return `Ouvre la section « ${s.label} » : invite le manager à faire le point sur ${s.focus}. Termine par UNE seule question ouverte.`
}

async function runTurn(section: string, focus: string | undefined, ouverture: boolean, message: string) {
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
        onTool: () => { streamStatus.value = 'Le coach consulte le profil…' },
        onToken: (tk) => { streamStatus.value = ''; raw += tk; streamingHtml.value = formatCoachReply(raw) },
        onReset: () => { raw = ''; streamingHtml.value = '' },
      },
      { mode: 'entretien_copilote_equipe', section, focus, ouverture, sujet: sujet() },
    )
    chat.value.push({ from: 'bot', text: raw.trim() ? formatCoachReply(raw) : ERR })
    // Étape finale : la synthèse est produite → on la capture pour l'export PDF.
    if (isLast(currentStep.value) && ouverture && raw.trim()) {
      synthesePlain.value = htmlToText(formatCoachReply(raw))
    }
  } catch {
    chat.value.push({ from: 'bot', text: ERR })
  } finally {
    busy.value = false
    streamStatus.value = ''
    streamingHtml.value = ''
  }
}

/* ---- Synthèse finale : export PDF (livrable pour conduire l'entretien) ---- */
function htmlToText(html: string): string {
  const d = document.createElement('div')
  d.innerHTML = html
  return (d.textContent || '').replace(/\n{3,}/g, '\n\n').trim()
}

function exportPdf() {
  const who = props.subject.name
  const meta = [props.subject.role, props.subject.pole].filter(Boolean).join(' · ')
  const when = new Date().toLocaleDateString('fr-FR', { dateStyle: 'long' })
  const blocks: PdfBlock[] = [
    { type: 'h1', text: `Synthèse de préparation · entretien de ${who}` },
    { type: 'p', text: `${meta ? meta + ' · ' : ''}${when} · Préparation manager BMCI (non contractuelle)` },
    { type: 'spacer' },
    { type: 'h2', text: 'Synthèse' },
    { type: 'p', text: synthesePlain.value || 'Synthèse non disponible.' },
    { type: 'spacer' },
    { type: 'h2', text: 'Déroulé de la préparation' },
  ]
  for (const m of chat.value) {
    const txt = htmlToText(m.text)
    if (!txt) continue
    blocks.push({ type: 'p', text: `${m.from === 'me' ? 'Manager' : 'Copilote'} : ${txt}` })
  }
  downloadPdf(`synthese-entretien-${who.replace(/\s+/g, '-')}-${when.replace(/\s+/g, '-')}`, blocks)
  toast('Synthèse exportée en PDF', 'ok')
}

function openSection(i: number) {
  return runTurn(STEPS.value[i].label, openFocus(i), true, '')
}
async function answer(text?: string) {
  const t = (text ?? input.value).trim()
  if (!t || busy.value) return
  chat.value.push({ from: 'me', text: t })
  input.value = ''
  await runTurn(STEPS.value[currentStep.value].label, undefined, false, t)
}
async function nextStep() {
  if (busy.value || atLastStep.value) return
  currentStep.value++
  await openSection(currentStep.value)
}

onMounted(() => openSection(0))
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
      </div>
      <div class="rounded-2xl border border-green-line bg-green-ghost p-4">
        <div class="mb-1 inline-flex items-center gap-1.5 text-xs font-bold text-green-deep">
          <Sparkles :size="13" /> Préparation guidée · IA
        </div>
        <p class="text-xs text-ink-2">
          L'IA vous <b>interroge sur {{ subject.name }}</b>, section par section. Vous répondez ;
          elle vous donne un retour et des conseils pour <b>conduire l'entretien</b>.
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
              {{ streamStatus || 'Le coach prépare la suite…' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Étape finale : synthèse prête → export PDF (livrable de l'entretien). -->
      <div v-if="atLastStep && synthesePlain && !busy" class="mt-3 rounded-xl border border-green-line bg-green-ghost p-4">
        <div class="flex items-center gap-2 text-green-deep">
          <FileText :size="16" /><b class="text-sm">Synthèse de préparation prête</b>
        </div>
        <p class="mt-1 text-xs text-ink-2">
          Le bilan de la préparation de l'entretien de {{ subject.name }}. Emportez-le pour conduire l'entretien.
        </p>
        <BaseButton class="mt-3" size="sm" @click="exportPdf">
          <Download :size="15" /> Télécharger la synthèse (PDF)
        </BaseButton>
      </div>

      <div class="mt-3 flex items-center gap-2">
        <div class="flex flex-1 items-center gap-2 rounded-xl border border-border bg-panel px-3 py-2">
          <MessageSquare :size="16" class="shrink-0 text-green-deep" />
          <input
            v-model="input"
            :placeholder="`Votre réponse au sujet de ${subject.name}…`"
            :disabled="busy"
            class="w-full bg-transparent text-sm outline-none placeholder:text-ink-3 disabled:opacity-60"
            @keydown.enter="answer()"
          />
          <BaseButton size="sm" :disabled="busy || !input.trim()" @click="answer()">
            <Send :size="14" /> Répondre
          </BaseButton>
        </div>
        <BaseButton
          v-if="!atLastStep"
          variant="secondary"
          size="sm"
          :disabled="busy"
          @click="nextStep"
        >
          Section suivante →
        </BaseButton>
      </div>
    </div>
  </div>
</template>
