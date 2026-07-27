<script setup lang="ts"></script>

<template>
  <div class="grid min-h-screen place-items-center bg-bg px-4 py-10">
    <div class="w-full max-w-md">
      <div class="mb-6 flex items-center gap-2.5">
        <div
          class="grid h-10 w-10 place-items-center rounded-xl bg-green font-display text-xl font-extrabold text-white"
        >
          B
        </div>
        <div>
          <div class="text-sm font-bold text-ink">BMCI · Gestion de carrière</div>
          <div class="text-[11px] text-ink-3">Groupe BNP Paribas</div>
        </div>
      </div>
      <div class="rounded-2xl border border-border bg-paper p-6 shadow-card sm:p-7">
        <slot />
      </div>
      <slot name="below" />
    </div>
  </div>
</template>
