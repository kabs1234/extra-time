<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink } from 'vue-router';

import { getLeaderboard, listEras } from '@/api/resources';
import LeaderboardTable from '@/components/LeaderboardTable.vue';
import LoadState from '@/components/LoadState.vue';
import { useAsync } from '@/composables/useAsync';
import { formatYears } from '@/format';

const TOP_PLAYERS = 5;

const eras = useAsync(listEras);
const leaderboard = useAsync(getLeaderboard);
const topRows = computed(() => (leaderboard.data.value ?? []).slice(0, TOP_PLAYERS));
</script>

<template>
  <div class="home">
    <section class="home-intro stack">
      <h1>Football history, from the first FA rules to the 48-team World Cup</h1>
      <p class="lede">
        Ten questions a round. Pick an era or a topic, answer, then read why each answer is right.
      </p>
      <div class="home-actions">
        <RouterLink to="/play" class="button">Start a quiz</RouterLink>
        <RouterLink to="/questions" class="button button-quiet">Browse the questions</RouterLink>
      </div>
    </section>

    <section class="home-eras" aria-labelledby="eras-heading">
      <h2 id="eras-heading">Play one era</h2>
      <LoadState :is-loading="eras.isLoading.value" :error="eras.error.value" @retry="eras.reload">
        <p v-if="!eras.data.value?.length">No eras yet.</p>
        <ol v-else class="timeline">
          <li v-for="era in eras.data.value" :key="era.id" class="timeline-stop">
            <span class="timeline-years">{{ formatYears(era) }}</span>
            <div class="timeline-body">
              <h3>
                <RouterLink :to="{ path: '/play', query: { era: era.id } }">{{ era.name }}</RouterLink>
              </h3>
              <p>{{ era.summary }}</p>
            </div>
          </li>
        </ol>
      </LoadState>
    </section>

    <section class="home-board" aria-label="Top of the leaderboard">
      <LoadState
        :is-loading="leaderboard.isLoading.value"
        :error="leaderboard.error.value"
        @retry="leaderboard.reload"
      >
        <p v-if="!topRows.length">Nobody has played yet. Be the first on the board.</p>
        <template v-else>
          <LeaderboardTable :rows="topRows" caption="Top of the table" is-compact />
          <p class="home-board-more"><RouterLink to="/leaderboard">See the full leaderboard</RouterLink></p>
        </template>
      </LoadState>
    </section>
  </div>
</template>

<style scoped>
.home {
  display: grid;
  gap: var(--space-7) var(--space-6);
  grid-template-columns: minmax(0, 1fr);
}

.home-intro h1 {
  max-width: 24ch;
}

.home-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.home-eras {
  display: grid;
  gap: var(--space-4);
}

.timeline {
  margin: 0;
  padding: 0;
  list-style: none;
}

.timeline-stop {
  display: grid;
  grid-template-columns: 6.5rem minmax(0, 1fr);
  gap: var(--space-4);
}

.timeline-years {
  padding-top: 0.1rem;
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--pitch);
}

.timeline-body {
  position: relative;
  display: grid;
  gap: var(--space-1);
  padding: 0 0 var(--space-5) var(--space-5);
  border-left: 2px solid var(--touchline);
}

.timeline-stop:last-child .timeline-body {
  border-left-color: transparent;
}

.timeline-body::before {
  content: '';
  position: absolute;
  left: -0.5rem;
  top: 0.35rem;
  width: 0.875rem;
  height: 0.875rem;
  border-radius: 50%;
  background: var(--chalk);
  border: 2px solid var(--pitch);
}

.timeline-body h3 a {
  color: var(--ink);
}

.timeline-body h3 a:hover {
  color: var(--pitch);
}

.timeline-body p {
  color: var(--muted);
}

.home-board-more {
  margin-top: var(--space-3);
}

@media (min-width: 60rem) {
  .home {
    grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
  }

  .home-intro {
    grid-column: 1 / -1;
  }

  .home-board {
    position: sticky;
    top: var(--space-4);
    align-self: start;
  }
}

@media (max-width: 34rem) {
  .timeline-stop {
    grid-template-columns: minmax(0, 1fr);
    gap: 0;
  }

  .timeline-years {
    padding-left: var(--space-5);
    border-left: 2px solid var(--touchline);
  }

  .timeline-stop:first-child .timeline-years {
    border-left-color: var(--touchline);
  }
}
</style>
