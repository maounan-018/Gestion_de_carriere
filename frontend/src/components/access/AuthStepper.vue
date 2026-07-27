<script setup lang="ts">
defineProps<{ active: number }>()
const steps = ['Compte', 'Vérification', 'Profil']
</script>

<template>
  <div class="mb-5 flex items-center justify-center gap-1.5">
    <template v-for="(s, i) in steps" :key="i">
      <div class="flex items-center gap-1.5">
        <span
          class="grid h-6 w-6 place-items-center rounded-full text-[11px] font-bold"
          :class="
            i < active
              ? 'bg-green text-white'
              : i === active
                ? 'border border-green-line bg-green-soft text-green-deep'
                : 'border border-border bg-panel-2 text-ink-3'
          "
        >
          {{ i < active ? '✓' : i + 1 }}
        </span>
        <span
          class="text-[11px] font-semibold"
          :class="i <= active ? 'text-ink-2' : 'text-ink-3'"
          >{{ s }}</span
        >
      </div>
      <span v-if="i < 2" class="h-px w-5" :class="i < active ? 'bg-green' : 'bg-border'" />
    </template>
  </div>
</template>
