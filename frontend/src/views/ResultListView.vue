<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink, useRoute } from 'vue-router';

import { listAttempts } from '@/api/resources';
import LoadState from '@/components/LoadState.vue';
import { useAsync } from '@/composables/useAsync';
import { formatDate, readPageNumber } from '@/format';

const route = useRoute();
const page = readPageNumber(route.query.page);
const attempts = useAsync(() => listAttempts(page));
const results = computed(() => attempts.data.value?.results ?? []);
</script>

<template>
  <section class="stack">
    <h1>My results</h1>
    <p class="lede">Every round you have played, newest first. Open one to see each answer again.</p>
    <LoadState :is-loading="attempts.isLoading.value" :error="attempts.error.value" @retry="attempts.reload">
      <p v-if="!results.length">
        You haven't played a round yet. <RouterLink to="/play">Play your first quiz</RouterLink>.
      </p>
      <template v-else>
        <ul class="ruled-list">
          <li v-for="attempt in results" :key="attempt.id" class="result-row">
            <RouterLink :to="{ name: 'result', params: { id: attempt.id } }" class="result-link">
              <span class="result-score">
                <span class="scoreboard-digits">{{ attempt.score }}</span>/{{ attempt.total }}
              </span>
              <span class="result-filter">
                {{ [attempt.era_name, attempt.topic_name].filter(Boolean).join(', ') || 'All of football history' }}
              </span>
              <span class="result-date">{{ formatDate(attempt.created_at) }}</span>
            </RouterLink>
          </li>
        </ul>
        <nav class="pager" aria-label="Pages">
          <RouterLink
            v-if="attempts.data.value?.previous"
            :to="{ query: { page: page - 1 } }"
            class="button button-quiet"
          >
            Newer results
          </RouterLink>
          <RouterLink v-if="attempts.data.value?.next" :to="{ query: { page: page + 1 } }" class="button button-quiet">
            Older results
          </RouterLink>
        </nav>
      </template>
    </LoadState>
  </section>
</template>

<style scoped>
.result-link {
  display: grid;
  grid-template-columns: 5.5rem minmax(0, 1fr) auto;
  align-items: baseline;
  gap: var(--space-4);
  color: var(--ink);
  text-decoration: none;
}

.result-link:hover .result-filter {
  color: var(--pitch);
  text-decoration: underline;
}

.result-score {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--muted);
}

.result-score .scoreboard-digits {
  padding: 0 var(--space-2);
  border-radius: var(--radius);
  background: var(--pitch-deep);
  font-size: 1.6rem;
}

.result-filter {
  font-weight: 600;
}

.result-date {
  color: var(--muted);
  font-size: 0.875rem;
}

.pager {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-5);
}

@media (max-width: 34rem) {
  .result-link {
    grid-template-columns: 5.5rem minmax(0, 1fr);
  }

  .result-date {
    grid-column: 2;
  }
}
</style>
