<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { Sparkles, Send, MessageSquare, Check, Clock, FileText, Download, RefreshCw } from '@lucide/vue'
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
 * L'IA est le COPILOTE du manager : elle l'interroge section par section SUR son
 * collaborateur ; le manager répond ; elle lui donne un retour puis des conseils.
 * Le passage d'une section à l'autre est PILOTÉ PAR L'IA (backend
 * `entretien_copilote_equipe`, balise [[SUIVANT]]) — aucun bouton, aucune annonce
 * répétée : la progression n'apparaît que dans le déroulé + la barre. Synthèse → PDF.
 */

export interface InterviewSubject {
  name: string
  role: string
  aspiration?: string
  gaps?: string[]
  pole?: string
}

const props = defineProps<{ subject: InterviewSubject }>()

// Aligné (ordre + index) sur `_ENTRETIEN_PLAN` du backend ; libellés orientés manager.
const STEPS: { label: string }[] = [
  { label: 'Introduction' },
  { label: 'Objectifs & missions' },
  { label: 'Réussites' },
  { label: 'Difficultés' },
  { label: 'Compétences' },
  { label: 'Aspirations & perspectives' },
  { label: "Conseils de l'agent" },
  { label: 'Synthèse finale' },
]

const currentStep = ref(0)
const stepAnswers = ref(0) // réponses données dans la section courante (plancher anti-avance éclair)
const chat = ref<ChatMessage[]>([])
const input = ref('')
const busy = ref(false)
const streamingHtml = ref('')
const streamStatus = ref('')
const scroller = ref<HTMLElement>()
const synthesePlain = ref('') // synthèse finale en texte brut (export PDF)
const ERR = "Désolé, je n'ai pas pu répondre à l'instant. Réessayez dans un moment."

const atLastStep = computed(() => currentStep.value >= STEPS.length - 1)
const progressPct = computed(() => Math.round((currentStep.value / (STEPS.length - 1)) * 100))
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

/* ---- Balise technique de progression émise par l'IA ---- */
const MARKER = '[[SUIVANT]]'
function splitMarker(raw: string): { text: string; advance: boolean } {
  const advance = raw.includes(MARKER)
  let text = raw.split(MARKER).join('')
  text = text.replace(/\[\[?S?U?I?V?A?N?T?\]?\]?$/, (m) => (m && MARKER.startsWith(m) ? '' : m))
  return { text, advance }
}

async function runTurn(ouverture: boolean, message: string) {
  if (busy.value) return
  busy.value = true
  streamStatus.value = ''
  streamingHtml.value = ''
  let raw = ''
  const fromStep = currentStep.value
  let reachedSyntheseNow = false
  try {
    await apiService.streamCoachMessage(
      message,
      [...chat.value],
      {
        onTool: () => { streamStatus.value = 'Le coach consulte le profil…' },
        onToken: (tk) => {
          streamStatus.value = ''
          raw += tk
          streamingHtml.value = formatCoachReply(splitMarker(raw).text)
        },
        onReset: () => { raw = ''; streamingHtml.value = '' },
      },
      {
        mode: 'entretien_copilote_equipe', section_index: fromStep,
        section_turns: stepAnswers.value, ouverture, sujet: sujet(),
      },
    )
    const { text, advance } = splitMarker(raw)
    const clean = text.trim()
    chat.value.push({ from: 'bot', text: clean ? formatCoachReply(clean) : ERR })
    if (advance && currentStep.value < STEPS.length - 1) {
      currentStep.value++
      stepAnswers.value = 0
      if (currentStep.value === STEPS.length - 1) reachedSyntheseNow = true
    }
    // Synthèse produite par le tour DÉDIÉ (ouverture sur la dernière section) : capture ce
    // tour-là uniquement (1re génération auto OU bouton), jamais après un simple message.
    const isRegen = ouverture && fromStep === STEPS.length - 1
    if (isRegen && clean) {
      synthesePlain.value = htmlToText(formatCoachReply(clean))
    }
  } catch {
    chat.value.push({ from: 'bot', text: ERR })
  } finally {
    busy.value = false
    streamStatus.value = ''
    streamingHtml.value = ''
  }
  if (reachedSyntheseNow) await runTurn(true, '')
}

async function answer(text?: string) {
  const t = (text ?? input.value).trim()
  if (!t || busy.value) return
  chat.value.push({ from: 'me', text: t })
  input.value = ''
  stepAnswers.value += 1
  await runTurn(false, t)
}

/** Régénère la synthèse À LA DEMANDE (bouton), en tenant compte des messages récents. */
function regenSynthese() {
  if (busy.value || !atLastStep.value) return
  runTurn(true, '')
}

onMounted(() => runTurn(true, ''))

/* ---- Synthèse finale : export PDF (livrable pour conduire l'entretien) ---- */
function htmlToText(html: string): string {
  const d = document.createElement('div')
  // Conserve les sauts de ligne (les <br> → \n) pour une synthèse AÉRÉE (paragraphes).
  d.innerHTML = (html || '').replace(/<br\s*\/?>/gi, '\n')
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
  ]
  const parts = (synthesePlain.value || 'Synthèse non disponible.')
    .split(/\n{2,}/)
    .map((p) => p.replace(/\s*\n\s*/g, ' ').trim())
    .filter(Boolean)
  for (const p of parts) {
    blocks.push({ type: 'p', text: p })
    blocks.push({ type: 'spacer' })
  }
  blocks.push({ type: 'h2', text: 'Déroulé de la préparation' })
  for (const m of chat.value) {
    const txt = htmlToText(m.text)
    if (!txt) continue
    blocks.push({ type: 'p', text: `${m.from === 'me' ? 'Manager' : 'Copilote'} : ${txt}` })
  }
  downloadPdf(`synthese-entretien-${who.replace(/\s+/g, '-')}-${when.replace(/\s+/g, '-')}`, blocks)
  toast('Synthèse exportée en PDF', 'ok')
}
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
            class="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm transition-colors"
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
          L'IA vous <b>interroge sur {{ subject.name }}</b>, section par section, et avance d'elle-même
          quand vous avez fait le tour. Elle vous donne un retour et des conseils pour
          <b>conduire l'entretien</b>.
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
          Vous pouvez le régénérer si vous avez ajouté des éléments depuis.
        </p>
        <div class="mt-3 flex flex-wrap gap-2">
          <BaseButton size="sm" @click="exportPdf">
            <Download :size="15" /> Télécharger la synthèse (PDF)
          </BaseButton>
          <BaseButton variant="secondary" size="sm" :disabled="busy" @click="regenSynthese">
            <RefreshCw :size="15" /> Régénérer la synthèse
          </BaseButton>
        </div>
      </div>

      <div class="mt-3 flex items-center gap-2 rounded-xl border border-border bg-panel px-3 py-2">
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
    </div>
  </div>
</template>
