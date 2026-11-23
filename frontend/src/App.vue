<script setup lang="ts">
import { RouterView } from 'vue-router';

import AppHeader from '@/components/AppHeader.vue';
</script>

<template>
  <a class="skip-link" href="#main">Skip to content</a>
  <AppHeader />
  <main id="main" class="page">
    <RouterView :key="$route.fullPath" />
  </main>
  <footer class="colophon">
    <p>Extra Time is a homework project for KBTU Web Development, autumn 2026. Facts are checked against well-documented sources.</p>
  </footer>
</template>

<style scoped>
.page {
  flex: 1;
  width: 100%;
  padding: var(--space-6) var(--page-inset) var(--space-8);
}

.colophon {
  padding: var(--space-4) var(--page-inset);
  border-top: 1px solid var(--touchline);
  color: var(--muted);
  font-size: 0.875rem;
}

.skip-link {
  position: absolute;
  left: var(--space-2);
  top: -3rem;
  padding: var(--space-2) var(--space-3);
  background: var(--ink);
  color: var(--surface);
}

.skip-link:focus {
  top: var(--space-2);
}
</style>
