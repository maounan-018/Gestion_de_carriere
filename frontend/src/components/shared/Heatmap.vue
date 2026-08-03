<script setup lang="ts">
import { computed } from 'vue'
import type { CartoLigne } from '@/types/rh'

// Heatmap DATA-DRIVEN : les colonnes (`familles`) et les lignes (départements) viennent
// du backend — aucune taxonomie figée. Une cellule `null` = pas de compétence de cette
// famille dans ce département. Les lignes sont regroupées par PÔLE macro (intertitres).
const props = withDefaults(
  defineProps<{ familles: string[]; lignes: CartoLigne[]; big?: boolean }>(),
  { big: false },
)
const emit = defineEmits<{ pole: [string] }>()

// Annote chaque ligne : `firstOfPole` déclenche un intertitre de pôle (les lignes
// arrivent déjà groupées par pôle depuis le backend).
const rows = computed(() =>
  props.lignes.map((l, i) => ({
    ...l,
    firstOfPole: !!l.pole && l.pole !== props.lignes[i - 1]?.pole,
  })),
)

function cls(l: number | null): string {
  const v = l ?? 0
  if (v === 0) return 'bg-heat-0 text-ink-3'
  if (v <= 2) return 'bg-heat-1 text-ink'
  if (v < 3.5) return 'bg-heat-2 text-ink'
  if (v < 4.5) return 'bg-heat-3 text-white'
  return 'bg-heat-4 text-white'
}
function fmt(l: number | null): string {
  return l == null ? '·' : Number.isInteger(l) ? String(l) : l.toFixed(1)
}
</script>

<template>
  <div class="overflow-x-auto">
    <div
      class="grid gap-1"
      :style="{
        gridTemplateColumns: `${big ? '180px' : '120px'} repeat(${familles.length}, minmax(${big ? '64px' : '44px'}, 1fr))`,
        minWidth: big ? '760px' : '520px',
      }"
    >
      <div />
      <div
        v-for="f in familles"
        :key="f"
        class="grid place-items-center px-1 text-center text-[10.5px] font-bold text-ink-3"
      >
        {{ f }}
      </div>

      <template v-for="p in rows" :key="p.departementKey">
        <div
          v-if="p.firstOfPole"
          class="mt-2 border-t border-green-line pt-1.5 text-[10px] font-bold uppercase tracking-wide text-green-deep"
          style="grid-column: 1 / -1"
        >
          {{ p.pole }}
        </div>
        <button
          class="flex items-center pr-1.5 text-left text-[11.5px] font-semibold text-ink-2 transition hover:text-green-deep"
          @click="emit('pole', p.departementKey)"
        >
          {{ p.label }}
        </button>
        <div
          v-for="(l, i) in p.niveaux"
          :key="i"
          class="grid place-items-center rounded-md font-display font-bold"
          :class="[cls(l), big ? 'h-12 text-base' : 'aspect-[1.7/1] text-xs']"
          :title="`${p.label} · ${familles[i]} · ${fmt(l)}/5`"
        >
          {{ fmt(l) }}
        </div>
      </template>
    </div>
  </div>
</template>
