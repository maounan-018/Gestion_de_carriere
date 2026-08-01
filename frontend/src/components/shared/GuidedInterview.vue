<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { Check, MessageSquare, Clock, Sparkles, Send, ArrowRight } from '@lucide/vue'
import { apiService } from '@/services/apiService'
import { formatCoachReply } from '@/services/coachFormat'
import type { ChatMessage } from '@/types/domain'
import BaseButton from '@/components/ui/BaseButton.vue'

/**
 * Préparation guidée de l'entretien annuel — l'IA en CO-PILOTE, section par section.
 *
 * Le RÔLE est NATIF côté backend (mode `entretien_copilote`) : le coach s'y
 * contextualise tout seul sur le profil du compte connecté et n'utilise aucun outil.
 * Le front ne déclare que `mode / section / focus / ouverture` — plus aucune consigne
 * ni contexte fabriqués ici. Réutilisé par les auto-entretiens (collab, manager « moi »,
 * RH « moi »), qui ne diffèrent que par le compte connecté (résolu côté backend).
 */

const STEPS: { label: string; focus: string }[] = [
  { label: 'Introduction', focus: '' },
  { label: 'Objectifs & missions', focus: "ses objectifs et missions de l'année écoulée" },
  { label: 'Réussites', focus: 'ses principales réussites (méthode STAR, résultats chiffrés)' },
  { label: 'Échecs & difficultés', focus: "ses difficultés ou échecs de l'année et ce qu'il en a appris" },
  { label: 'Compétences', focus: 'les compétences développées et ses axes de progression (savoir-être inclus)' },
  { label: 'Souhaits & perspectives', focus: "ses souhaits d'évolution, de mobilité et de formation" },
  { label: "Conseils de l'agent", focus: '' },
  { label: 'Synthèse finale', focus: 'objectifs, réussites, axes de progrès et formations souhaitées' },
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

/* ---- Contenu de section (la STRUCTURE d'entretien reste côté front ; le RÔLE est backend) ---- */
function isConseils(i: number): boolean {
  return i === STEPS.length - 2
}
function isLast(i: number): boolean {
  return i >= STEPS.length - 1
}
function openFocus(i: number): string {
  const s = STEPS[i]
  if (i === 0) {
    return (
      "Accueille le collaborateur et explique en 1-2 phrases que tu vas l'accompagner, section par " +
      'section, à préparer son entretien annuel. Invite-le à démarrer par ses objectifs et missions. ' +
      'Termine par UNE seule question ouverte.'
    )
  }
  if (isConseils(i)) {
    return (
      "Donne au collaborateur 2-3 conseils personnalisés pour réussir son entretien (posture, points à " +
      "valoriser, formulations), en t'appuyant sur ce qu'il a partagé. Termine en lui demandant s'il " +
      'souhaite ajuster un point.'
    )
  }
  if (isLast(i)) return `Fais la synthèse de la préparation : ${s.focus}.`
  return `Ouvre la section « ${s.label} » : invite le collaborateur à préparer ${s.focus}. Termine par UNE seule question ouverte.`
}

/* ---- Cœur : un tour streamé (mode natif backend `entretien_copilote`) ---- */
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
        onTool: () => { streamStatus.value = 'Le coach consulte votre dossier…' },
        onToken: (tk) => { streamStatus.value = ''; raw += tk; streamingHtml.value = formatCoachReply(raw) },
        onReset: () => { raw = ''; streamingHtml.value = '' },
      },
      { mode: 'entretien_copilote', section, focus, ouverture },
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

function openSection(i: number) {
  return runTurn(STEPS[i].label, openFocus(i), true, '')
}
async function answer(text?: string) {
  const t = (text ?? input.value).trim()
  if (!t || busy.value) return
  chat.value.push({ from: 'me', text: t })
  input.value = ''
  await runTurn(STEPS[currentStep.value].label, undefined, false, t)
}
async function nextStep() {
  if (busy.value || atLastStep.value) return
  currentStep.value++
  await openSection(currentStep.value)
}

// Démarrage : le coach ouvre l'introduction.
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
          Dernière étape — le coach rédige la synthèse.
        </p>
      </div>

      <div class="rounded-2xl border border-green-line bg-green-ghost p-4">
        <div class="mb-1 inline-flex items-center gap-1.5 text-xs font-bold text-green-deep">
          <Sparkles :size="13" /> Préparation guidée · IA
        </div>
        <p class="text-xs text-ink-2">
          Votre coach IA vous accompagne section par section pour préparer votre entretien annuel.
          Exprimez-vous : il réagit, vous conseille et vous aide à structurer, puis avancez avec
          « Passer à l'étape suivante ».
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
