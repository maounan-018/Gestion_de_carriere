<script setup lang="ts">
import { CARTO_SKILLS } from '@/data/rh'
import type { CartoPole } from '@/types/rh'

withDefaults(defineProps<{ poles: CartoPole[]; big?: boolean }>(), { big: false })
const emit = defineEmits<{ pole: [string] }>()

function cls(l: number): string {
  if (l === 0) return 'bg-heat-0 text-ink-3'
  if (l <= 2) return 'bg-heat-1 text-ink'
  if (l === 3) return 'bg-heat-2 text-ink'
  if (l === 4) return 'bg-heat-3 text-white'
  return 'bg-heat-4 text-white'
}
</script>

<template>
  <div class="overflow-x-auto">
    <div
      class="grid gap-1"
      :style="{
        gridTemplateColumns: `${big ? '180px' : '120px'} repeat(${CARTO_SKILLS.length}, minmax(${big ? '64px' : '44px'}, 1fr))`,
        minWidth: big ? '760px' : '520px',
      }"
    >
      <div />
      <div
        v-for="s in CARTO_SKILLS"
        :key="s"
        class="grid place-items-center px-1 text-center text-[10.5px] font-bold text-ink-3"
      >
        {{ s }}
      </div>

      <template v-for="p in poles" :key="p.name">
        <button
          class="flex items-center pr-1.5 text-left text-[11.5px] font-semibold text-ink-2 transition hover:text-green-deep"
          @click="emit('pole', p.name)"
        >
          {{ p.name }}
        </button>
        <div
          v-for="(l, i) in p.levels"
          :key="i"
          class="grid place-items-center rounded-md font-display font-bold"
          :class="[cls(l), big ? 'h-12 text-base' : 'aspect-[1.7/1] text-xs']"
          :title="`${p.name} · ${l}/5`"
        >
          {{ l || '·' }}
        </div>
      </template>
    </div>
  </div>
</template>
