<script setup lang="ts">
import { computed } from 'vue'

/**
 * Avatar : photo réelle si fournie (`photo`, cf. upload profil), sinon un
 * dégradé GÉNÉRÉ déterministe (image d'identité par personne) portant le
 * monogramme. Palette strictement dans la charte (verts / teal / or) —
 * jamais de noir ni de sombre. La couleur est stable par personne (hash du
 * monogramme + `seed` optionnel pour désambiguïser des initiales identiques).
 */
const props = defineProps<{
  initials: string
  size?: 'sm' | 'md' | 'xl'
  photo?: string
  seed?: string
}>()

const GRADIENTS: [string, string][] = [
  ['#34D399', '#059669'], // mint → emerald
  ['#2DD4BF', '#0D9488'], // aqua → teal
  ['#4ADE80', '#16A34A'], // vert clair → vert
  ['#A3E635', '#4D7C0F'], // lime → olive
  ['#5EEAD4', '#0F766E'], // menthe → teal profond
  ['#FBBF24', '#B45309'], // or (accent chaud)
]

function hash(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0
  return h
}

const grad = computed(() => {
  const [a, b] = GRADIENTS[hash((props.seed ?? '') + props.initials) % GRADIENTS.length]
  return `linear-gradient(135deg, ${a}, ${b})`
})
</script>

<template>
  <div
    class="grid shrink-0 place-items-center overflow-hidden rounded-full bg-cover bg-center font-bold text-white shadow-card ring-2 ring-white"
    :class="{
      'h-8 w-8 text-xs': !size || size === 'sm',
      'h-11 w-11 text-sm': size === 'md',
      'h-16 w-16 text-lg': size === 'xl',
    }"
    :style="photo
      ? { backgroundImage: `url(${photo})`, color: 'transparent' }
      : { backgroundImage: grad }"
  >
    {{ initials }}
  </div>
</template>
