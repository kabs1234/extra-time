<script setup lang="ts">
import { computed, ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';

import { getErrorMessage } from '@/api/client';
import { getMe, listAttempts } from '@/api/resources';
import type { Me } from '@/api/types';
import { logout, setCurrentUser } from '@/auth/session';
import DeleteAccount from '@/components/DeleteAccount.vue';
import LoadState from '@/components/LoadState.vue';
import PasswordForm from '@/components/PasswordForm.vue';
import ProfileForm from '@/components/ProfileForm.vue';
import { useAsync } from '@/composables/useAsync';
import { formatDate } from '@/format';

const RECENT_ROUNDS = 3;

const router = useRouter();
const me = useAsync(loadMe);
const attempts = useAsync(() => listAttempts());
const recentAttempts = computed(() => (attempts.data.value?.results ?? []).slice(0, RECENT_ROUNDS));
const logoutError = ref<string>();

async function loadMe(): Promise<Me> {
  const freshMe = await getMe();
  setCurrentUser(freshMe);
  return freshMe;
}

function handleSaved(updated: Me): void {
  me.data.value = updated;
  setCurrentUser(updated);
}

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
  <LoadState :is-loading="me.isLoading.value" :error="me.error.value" @retry="me.reload">
    <div v-if="me.data.value" class="profile">
      <header class="profile-header">
        <div class="stack profile-identity">
          <h1>{{ me.data.value.username }}</h1>
          <p class="lede">
            Playing since {{ formatDate(me.data.value.date_joined) }}
            <template v-if="me.data.value.profile.favorite_club">
              and supporting {{ me.data.value.profile.favorite_club }}</template
            >.
          </p>
          <div>
            <button type="button" class="button button-quiet" @click="handleLogout">Log out</button>
          </div>
          <p v-if="logoutError" class="form-alert" role="alert">Couldn't log out: {{ logoutError }}</p>
        </div>
        <dl class="scoreboard stats">
          <div>
            <dt>Rounds</dt>
            <dd class="scoreboard-digits">{{ me.data.value.stats.attempts }}</dd>
          </div>
          <div>
            <dt>Correct</dt>
            <dd class="scoreboard-digits">{{ me.data.value.stats.total_correct }}</dd>
          </div>
          <div>
            <dt>Best round</dt>
            <dd class="scoreboard-digits">{{ me.data.value.stats.best_score_pct }}%</dd>
          </div>
        </dl>
      </header>
      <section class="recent" aria-labelledby="recent-heading">
        <h2 id="recent-heading">Recent rounds</h2>
        <LoadState :is-loading="attempts.isLoading.value" :error="attempts.error.value" @retry="attempts.reload">
          <p v-if="!recentAttempts.length">No rounds yet. <RouterLink to="/play">Play your first quiz</RouterLink>.</p>
          <ul v-else class="ruled-list">
            <li v-for="attempt in recentAttempts" :key="attempt.id">
              <RouterLink :to="{ name: 'result', params: { id: attempt.id } }">
                {{ attempt.score }} of {{ attempt.total }} in
                {{ [attempt.era_name, attempt.topic_name].filter(Boolean).join(', ') || 'all of football history' }}
              </RouterLink>
              <span class="recent-date">{{ formatDate(attempt.created_at) }}</span>
            </li>
          </ul>
          <p v-if="recentAttempts.length"><RouterLink to="/results">See all my results</RouterLink></p>
        </LoadState>
      </section>
      <div class="profile-forms">
        <ProfileForm :me="me.data.value" @saved="handleSaved" />
        <PasswordForm />
      </div>
      <DeleteAccount />
    </div>
  </LoadState>
</template>

<style scoped>
.profile {
  display: grid;
  gap: var(--space-7);
}

.profile-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: start;
  gap: var(--space-5);
}

.profile-identity {
  flex: 1 1 20rem;
}

.stats {
  display: flex;
  gap: var(--space-6);
  margin: 0;
}

.stats dt {
  font-size: 0.875rem;
  color: var(--touchline);
}

.stats dd {
  margin: var(--space-1) 0 0;
  font-size: 2.75rem;
}

.recent {
  display: grid;
  gap: var(--space-3);
  max-width: 44rem;
}

.recent li {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-2);
}

.recent-date {
  color: var(--muted);
  font-size: 0.875rem;
}

.profile-forms {
  display: grid;
  gap: var(--space-7);
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr));
}

@media (max-width: 34rem) {
  .stats {
    width: 100%;
    justify-content: space-between;
    gap: var(--space-3);
  }
}
</style>
