<script setup lang="ts">
import { computed } from 'vue'
import type { ProgressionStation } from '@/types/domain'

const props = defineProps<{ stations: ProgressionStation[]; pct: number }>()

const W = 700
const H = 168
const MX = 34

type Pt = { x: number; y: number }

const points = computed<Pt[]>(() => {
  const n = props.stations.length
  return props.stations.map((_, i) => ({
    x: MX + (i * (W - 2 * MX)) / Math.max(1, n - 1),
    y: 148 - (i / Math.max(1, n - 1)) * 118,
  }))
})

const currentIndex = computed(() => {
  const i = props.stations.findIndex((s) => s.state === 'current')
  return i === -1 ? props.stations.length - 1 : i
})

/** Courbe lissée (tangentes horizontales aux points) sur un sous-ensemble de points. */
function smooth(pts: Pt[]): string {
  if (pts.length < 2) return pts.length ? `M${pts[0].x},${pts[0].y}` : ''
  let d = `M${pts[0].x},${pts[0].y}`
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i]
    const b = pts[i + 1]
    const cx = (a.x + b.x) / 2
    d += ` C${cx},${a.y} ${cx},${b.y} ${b.x},${b.y}`
  }
  return d
}

const fullPath = computed(() => smooth(points.value))
const solidPath = computed(() => smooth(points.value.slice(0, currentIndex.value + 1)))
const dashedPath = computed(() => smooth(points.value.slice(currentIndex.value)))
</script>

<template>
  <div>
    <div class="mb-3 flex items-end justify-between gap-3">
      <div>
        <div class="font-display text-lg font-bold text-ink">Mon parcours</div>
        <div v-if="stations.find((s) => s.state === 'goal')"
          class="mt-0.5 text-sm font-semibold text-green-deep">
          Objectif : {{ stations.find((s) => s.state === 'goal')?.title }}
        </div>
      </div>
      <div class="text-right">
        <div class="font-display text-3xl font-bold leading-none text-green-deep">{{ pct }} %</div>
        <div class="text-[11px] text-ink-3">de compatibilité</div>
      </div>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" class="h-auto w-full" role="img"
      aria-label="Courbe de progression de carrière">
      <path :d="fullPath" fill="none" stroke="var(--color-green-line)" stroke-width="2.5"
        stroke-linecap="round" opacity="0.5" />
      <path :d="dashedPath" fill="none" stroke="var(--color-green-line)" stroke-width="2.5"
        stroke-linecap="round" stroke-dasharray="2 7" />
      <path :d="solidPath" fill="none" stroke="var(--color-green)" stroke-width="3.5"
        stroke-linecap="round" />
      <g v-for="(p, i) in points" :key="i">
        <circle :cx="p.x" :cy="p.y"
          :r="stations[i].state === 'current' ? 8 : stations[i].state === 'goal' ? 7 : 5"
          :fill="stations[i].state === 'goal' ? 'var(--color-gold)'
            : stations[i].state === 'current' ? 'var(--color-green)' : 'var(--color-green-line)'"
          stroke="white" stroke-width="3" />
        <text v-if="stations[i].state === 'current'" :x="p.x" :y="p.y - 15"
          text-anchor="middle" class="fill-green-deep text-[12px] font-bold">Vous</text>
      </g>
    </svg>

    <div class="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <div v-for="(s, i) in stations" :key="i"
        class="rounded-xl border p-3"
        :class="s.state === 'goal' ? 'border-dashed border-gold/50 bg-gold-soft/40'
          : s.state === 'current' ? 'border-green-line bg-green-soft' : 'border-border bg-panel'">
        <div class="text-[11px] font-semibold uppercase tracking-wide"
          :class="s.state === 'goal' ? 'text-gold' : 'text-green-deep'">{{ s.period }}</div>
        <div class="mt-0.5 text-sm font-bold text-ink">{{ s.title }}</div>
        <div v-if="s.desc" class="mt-0.5 text-xs text-ink-3">{{ s.desc }}</div>
      </div>
    </div>
  </div>
</template>
