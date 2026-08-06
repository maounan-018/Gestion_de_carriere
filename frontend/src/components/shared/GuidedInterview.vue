<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { Check, MessageSquare, Sparkles, Send, Play, Download, FileText } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { formatCoachReply } from '@/services/coachFormat'
import { useSessionStore } from '@/stores/session'
import { useToast } from '@/composables/useToast'
import type { ChatMessage } from '@/types/domain'
import { downloadPdf, type PdfBlock } from '@/utils/pdf'
import BaseButton from '@/components/ui/BaseButton.vue'

/**
 * Préparation guidée de l'entretien annuel · l'IA en CO-PILOTE, section par section.
 *
 * Parcours : un écran d'INTRODUCTION cadre la SIMULATION, puis un échange guidé. Le
 * passage d'une section à la suivante est PILOTÉ PAR L'IA (backend `entretien_copilote`) :
 * elle fait le tour des points d'une section, PUIS enchaîne naturellement — aucun bouton
 * « Poursuivre », aucune annonce répétée. L'IA émet une balise technique [[SUIVANT]] en tête
 * de réponse au moment de la transition ; le front la détecte pour avancer l'étape (déroulé
 * + barre de progression) et la retire du texte. À la fin, la synthèse est persistée + PDF.
 */

const session = useSessionStore()
const { toast } = useToast()

// Doit rester ALIGNÉ (ordre + libellés) sur `_ENTRETIEN_PLAN` du backend (coach_service).
const STEPS: { label: string }[] = [
  { label: 'Introduction' },
  { label: 'Objectifs & missions' },
  { label: 'Réussites' },
  { label: 'Échecs & difficultés' },
  { label: 'Compétences' },
  { label: 'Aspirations & perspectives' },
  { label: "Conseils de l'agent" },
  { label: 'Synthèse finale' },
]

const phase = ref<'intro' | 'chat'>('intro')
const currentStep = ref(0)
const stepAnswers = ref(0) // réponses données dans la section courante (plancher anti-avance éclair)
const chat = ref<ChatMessage[]>([])
const input = ref('')
const busy = ref(false)
const streamingHtml = ref('')
const streamStatus = ref('')
const scroller = ref<HTMLElement>()
const synthesePlain = ref('') // synthèse finale en texte brut (persistée + PDF)
const savedAt = ref('')

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

/* ---- Balise technique de progression émise par l'IA ---- */
const MARKER = '[[SUIVANT]]'
function splitMarker(raw: string): { text: string; advance: boolean } {
  const advance = raw.includes(MARKER)
  let text = raw.split(MARKER).join('')
  // Masque un marqueur PARTIEL encore en cours de streaming (préfixe de la balise, en fin de flux).
  text = text.replace(/\[\[?S?U?I?V?A?N?T?\]?\]?$/, (m) => (m && MARKER.startsWith(m) ? '' : m))
  return { text, advance }
}

/* ---- Cœur : un tour streamé (mode natif backend `entretien_copilote`) ---- */
async function runTurn(ouverture: boolean, message: string) {
  if (busy.value) return
  busy.value = true
  streamStatus.value = ''
  streamingHtml.value = ''
  let raw = ''
  const fromStep = currentStep.value
  try {
    await apiService.streamCoachMessage(
      message,
      [...chat.value],
      {
        onTool: () => { streamStatus.value = 'Le coach consulte votre dossier…' },
        onToken: (tk) => {
          streamStatus.value = ''
          raw += tk
          streamingHtml.value = formatCoachReply(splitMarker(raw).text)
        },
        onReset: () => { raw = ''; streamingHtml.value = '' },
      },
      { mode: 'entretien_copilote', section_index: fromStep, section_turns: stepAnswers.value, ouverture },
    )
    const { text, advance } = splitMarker(raw)
    const clean = text.trim()
    chat.value.push({ from: 'bot', text: clean ? formatCoachReply(clean) : ERR })
    // L'IA signale la transition → on avance l'étape (visuel : déroulé + barre).
    if (advance && currentStep.value < STEPS.length - 1) {
      currentStep.value++
      stepAnswers.value = 0
    }
    // Arrivé à la synthèse finale : on la CONSERVE (persistée) pour l'export PDF.
    if (currentStep.value === STEPS.length - 1 && currentStep.value > fromStep && clean) {
      synthesePlain.value = htmlToText(formatCoachReply(clean))
      await persistSynthese()
    }
  } catch {
    chat.value.push({ from: 'bot', text: ERR })
  } finally {
    busy.value = false
    streamStatus.value = ''
    streamingHtml.value = ''
  }
}

function start() {
  phase.value = 'chat'
  currentStep.value = 0
  stepAnswers.value = 0
  runTurn(true, '')
}

async function answer(text?: string) {
  const t = (text ?? input.value).trim()
  if (!t || busy.value) return
  chat.value.push({ from: 'me', text: t })
  input.value = ''
  stepAnswers.value += 1
  await runTurn(false, t)
}

/* ---- Synthèse : persistance + export PDF ---- */
async function persistSynthese() {
  const res = await apiService.enregistrerMaSynthese(synthesePlain.value)
  if (res) savedAt.value = res.enregistre_le
}

function htmlToText(html: string): string {
  const d = document.createElement('div')
  d.innerHTML = html
  return (d.textContent || '').replace(/\n{3,}/g, '\n\n').trim()
}

function exportPdf() {
  const who = session.user?.name || 'Collaborateur'
  const when = new Date().toLocaleDateString('fr-FR', { dateStyle: 'long' })
  const blocks: PdfBlock[] = [
    { type: 'h1', text: 'Synthèse de préparation · entretien annuel' },
    { type: 'p', text: `${who} · ${when} · Simulation BMCI (préparation, non contractuelle)` },
    { type: 'spacer' },
    { type: 'h2', text: 'Synthèse' },
    { type: 'p', text: synthesePlain.value || 'Synthèse non disponible.' },
    { type: 'spacer' },
    { type: 'h2', text: 'Déroulé de la préparation' },
  ]
  for (const m of chat.value) {
    const txt = htmlToText(m.text)
    if (!txt) continue
    blocks.push({ type: 'p', text: `${m.from === 'me' ? 'Vous' : 'Coach'} : ${txt}` })
  }
  downloadPdf(`synthese-entretien-${when.replace(/\s+/g, '-')}`, blocks)
  toast('Synthèse exportée en PDF', 'ok')
}
</script>

<template>
  <!-- ÉCRAN D'INTRODUCTION (transition) : cadre la simulation avant de démarrer. -->
  <div v-if="phase === 'intro'" class="mx-auto max-w-2xl">
    <div class="rounded-2xl border border-border bg-paper p-6 shadow-card">
      <div class="mb-4 inline-flex items-center gap-2 rounded-full bg-green-soft px-3 py-1 text-xs font-bold text-green-deep">
        <Sparkles :size="14" /> Simulation guidée par l'IA
      </div>
      <h2 class="font-display text-2xl font-bold text-ink">Préparez votre entretien annuel</h2>
      <p class="mt-2 text-sm leading-relaxed text-ink-2">
        Cet espace est une <b>simulation</b> : un entraînement pour préparer votre véritable entretien
        annuel et l'évaluation de l'année. Votre copilote IA vous guide, section par section, pour
        structurer vos objectifs, vos réussites, vos difficultés et vos aspirations. Rien n'est transmis
        à votre manager : vous repartez avec une <b>synthèse personnelle</b>, exportable en PDF.
      </p>

      <div class="mt-5 rounded-xl border border-green-line bg-green-ghost p-4">
        <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-green-deep">Les étapes</p>
        <ol class="space-y-1.5">
          <li v-for="(s, i) in STEPS" :key="s.label" class="flex items-center gap-2.5 text-sm text-ink-2">
            <span class="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-green text-[11px] font-bold text-white">{{ i + 1 }}</span>
            {{ s.label }}
          </li>
        </ol>
      </div>

      <BaseButton class="mt-5" @click="start">
        <Play :size="16" /> Commencer la simulation
      </BaseButton>
    </div>
  </div>

  <!-- ÉCHANGE GUIDÉ -->
  <div v-else class="grid gap-5 lg:grid-cols-[240px_1fr]">
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
            <span
              v-else
              class="grid h-5 w-5 shrink-0 place-items-center rounded-full text-[11px] font-bold"
              :class="stepState(i) === 'current' ? 'bg-green text-white' : 'bg-panel-2 text-ink-3'"
            >{{ i + 1 }}</span>
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
          Répondez au fil de l'échange. Le coach avance de lui-même d'une section à l'autre quand vous
          en avez fait le tour — suivez votre progression ci-dessus. À la fin, votre synthèse est
          enregistrée et exportable en PDF.
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
              {{ streamStatus || 'Le coach prépare la section…' }}
            </span>
          </div>
        </div>

        <!-- Étape finale : synthèse conservée + export PDF. -->
        <div v-if="atLastStep && synthesePlain && !busy" class="rounded-xl border border-green-line bg-green-ghost p-4">
          <div class="flex items-center gap-2 text-green-deep">
            <FileText :size="16" /><b class="text-sm">Votre synthèse est prête</b>
          </div>
          <p class="mt-1 text-xs text-ink-2">
            Elle est enregistrée dans votre espace<span v-if="savedAt"> · {{ new Date(savedAt).toLocaleDateString('fr-FR') }}</span>.
            Emportez-la à votre entretien.
          </p>
          <BaseButton class="mt-3" size="sm" @click="exportPdf">
            <Download :size="15" /> Télécharger la synthèse (PDF)
          </BaseButton>
        </div>
      </div>

      <div class="mt-3 flex items-center gap-2 rounded-xl border border-border bg-panel px-3 py-2">
        <MessageSquare :size="16" class="shrink-0 text-green-deep" />
        <input
          v-model="input"
          :placeholder="atLastStep ? 'Un dernier mot avant de clôturer…' : 'Écrivez votre réponse…'"
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
