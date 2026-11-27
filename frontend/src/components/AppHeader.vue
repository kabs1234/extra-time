<script setup lang="ts">
import { computed, ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';

import { getErrorMessage } from '@/api/client';
import { logout, session } from '@/auth/session';

const router = useRouter();
const logoutError = ref<string>();
/** Only offer "Log in" once we know there's no session; until then the user might be logged in. */
const isKnownGuest = computed(() => session.isReady && !session.restoreError);

async function handleLogout(): Promise<void> {
  logoutError.value = undefined;
  try {
    await logout();
    await router.push({ name: 'home' });
  } catch (error: unknown) {
    logoutError.value = getErrorMessage(error);
  }
}
</script>

<template>
  <header class="masthead">
    <RouterLink to="/" class="wordmark">Extra Time</RouterLink>
    <nav class="masthead-nav" aria-label="Main">
      <RouterLink to="/questions" class="masthead-link" active-class="is-current">Questions</RouterLink>
      <RouterLink to="/leaderboard" class="masthead-link" active-class="is-current">Leaderboard</RouterLink>
      <RouterLink to="/play" class="masthead-link" active-class="is-current">Play</RouterLink>
      <template v-if="session.user">
        <RouterLink to="/results" class="masthead-link" active-class="is-current">My results</RouterLink>
        <RouterLink to="/my-questions" class="masthead-link" active-class="is-current">My questions</RouterLink>
        <RouterLink to="/profile" class="masthead-link masthead-user" active-class="is-current">
          {{ session.user.username }}
        </RouterLink>
        <button type="button" class="masthead-link masthead-button" @click="handleLogout">Log out</button>
      </template>
      <template v-else-if="isKnownGuest">
        <RouterLink to="/login" class="masthead-link" active-class="is-current">Log in</RouterLink>
        <RouterLink to="/signup" class="masthead-link masthead-signup">Sign up</RouterLink>
      </template>
    </nav>
    <p v-if="logoutError" class="masthead-error" role="alert">Couldn't log out: {{ logoutError }}</p>
  </header>
</template>

<style scoped>
.masthead {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3) var(--space-5);
  padding: var(--space-4) var(--page-inset);
  background: var(--pitch);
  color: var(--surface);
}

.wordmark {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  color: var(--surface);
  text-decoration: none;
}

.masthead-nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2) var(--space-4);
}

.masthead-link {
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--surface);
  text-decoration: none;
  padding-bottom: 2px;
  border-bottom: 3px solid transparent;
}

.masthead-link:hover,
.masthead-link.is-current {
  border-bottom-color: var(--amber);
}

.masthead-user {
  color: var(--amber);
}

.masthead-button {
  background: none;
  border-top: 0;
  border-left: 0;
  border-right: 0;
  padding: 0 0 2px;
  cursor: pointer;
}

.masthead-signup {
  padding: var(--space-1) var(--space-3);
  border: 2px solid var(--surface);
  border-radius: var(--radius);
}

.masthead-signup:hover {
  background: var(--surface);
  color: var(--pitch);
}

.masthead-error {
  flex-basis: 100%;
  color: var(--amber);
}
</style>
