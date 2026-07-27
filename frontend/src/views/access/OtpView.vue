<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Mail } from 'lucide-vue-next'
import { useToast } from '@/composables/useToast'
import { PERSONAS } from '@/data/personas'
import AuthCard from '@/components/access/AuthCard.vue'
import AuthStepper from '@/components/access/AuthStepper.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

const router = useRouter()
const { toast } = useToast()
const digits = ref<string[]>(['', '', '', '', '', ''])
const inputs = ref<HTMLInputElement[]>([])

function onInput(i: number, e: Event) {
  const v = (e.target as HTMLInputElement).value.replace(/\D/g, '').slice(0, 1)
  digits.value[i] = v
  if (v && i < 5) inputs.value[i + 1]?.focus()
}
function onKey(i: number, e: KeyboardEvent) {
  if (e.key === 'Backspace' && !digits.value[i] && i > 0) inputs.value[i - 1]?.focus()
}
function validate() {
  if (!digits.value.every((d) => d !== '')) {
    toast('Saisissez les 6 chiffres du code.', 'error')
    return
  }
  router.push({ name: 'onboarding' })
}
</script>

<template>
  <AuthCard>
    <AuthStepper :active="1" />
    <div class="mb-2 grid place-items-center text-green-deep"><Mail :size="26" /></div>
    <h1 class="text-center font-display text-xl font-bold text-ink">Vérifiez votre e-mail</h1>
    <p class="mt-1 text-center text-sm text-ink-3">
      Code à 6 chiffres envoyé à <b>{{ PERSONAS.collab.email }}</b>
    </p>

    <div class="mt-5 flex justify-center gap-2">
      <input
        v-for="(d, i) in digits"
        :key="i"
        ref="inputs"
        :value="d"
        :aria-label="`Chiffre ${i + 1} sur 6 du code de vérification`"
        inputmode="numeric"
        maxlength="1"
        class="h-12 w-11 rounded-xl border border-border bg-paper text-center font-display text-lg font-bold text-ink outline-none focus:border-green-line"
        @input="onInput(i, $event)"
        @keydown="onKey(i, $event)"
      />
    </div>

    <BaseButton block class="mt-5" @click="validate">Valider</BaseButton>
    <p class="mt-4 text-center text-xs text-ink-3">
      Pas reçu ?
      <button
        class="font-semibold text-green-deep hover:underline"
        @click="toast('Nouveau code envoyé', 'info')"
      >
        Renvoyer le code
      </button>
    </p>
  </AuthCard>
</template>
