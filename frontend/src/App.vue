<script setup lang="ts">
import { computed, ref } from 'vue';
import { RouterView, useRoute, useRouter } from 'vue-router';

import { isLoggedIn, retrySessionRestore, session } from '@/auth/session';
import AppHeader from '@/components/AppHeader.vue';

const route = useRoute();
const router = useRouter();
const isRetrying = ref(false);

/** A protected page can't load while we don't know who the user is, so the alert stands in for it. */
const isPageBlocked = computed(() => session.restoreError !== undefined && route.meta.requiresAuth === true);

async function handleRetry(): Promise<void> {
  isRetrying.value = true;
  try {
    await retrySessionRestore();
  } finally {
    isRetrying.value = false;
  }
  const isGuestOnProtectedPage = !isLoggedIn() && !session.restoreError && route.meta.requiresAuth;
  if (isGuestOnProtectedPage) {
    await router.replace({ name: 'login', query: { redirect: route.fullPath } });
  }
}
</script>

<template>
  <a class="skip-link" href="#main">Skip to content</a>
  <AppHeader />
  <main id="main" class="page">
    <div v-if="session.restoreError" class="form-alert session-alert" role="alert">
      <p>Couldn't check whether you're logged in: {{ session.restoreError }}</p>
      <div>
        <button type="button" class="button" :disabled="isRetrying" @click="handleRetry">
          {{ isRetrying ? 'Checking…' : 'Try again' }}
        </button>
      </div>
    </div>
    <p v-if="!session.isReady" class="session-loading" role="status">Loading…</p>
    <RouterView v-else-if="!isPageBlocked" :key="$route.fullPath" />
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

.session-alert {
  display: grid;
  gap: var(--space-3);
  max-width: 44rem;
  margin-bottom: var(--space-6);
}

.session-loading {
  padding: var(--space-6) 0;
  color: var(--muted);
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
