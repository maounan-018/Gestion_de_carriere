<script setup lang="ts">
import { computed } from 'vue'
import {
  MapPin, Briefcase, Calendar, Clock, Users, BookOpen, Sparkles, Route,
  Award, Shield, Bell, Send, Check, User, Mail, LayoutGrid, Search,
  MessageSquare, Zap, Filter, Lock, Flag,
} from 'lucide-vue-next'
import type { IconKey } from '@/types/domain'
import type { Component } from 'vue'

const MAP: Record<IconKey, Component> = {
  pin: MapPin, brief: Briefcase, cal: Calendar, clock: Clock, team: Users,
  book: BookOpen, spark: Sparkles, route: Route, award: Award, shield: Shield,
  bell: Bell, send: Send, check: Check, user: User, mail: Mail, grid: LayoutGrid,
  search: Search, chat: MessageSquare, bolt: Zap, filter: Filter, lock: Lock, flag: Flag,
}

const props = withDefaults(defineProps<{ name: IconKey; size?: number }>(), { size: 16 })
const cmp = computed(() => MAP[props.name])
</script>

<template>
  <component :is="cmp" :size="size" />
</template>
