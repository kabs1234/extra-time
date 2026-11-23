<script setup lang="ts">
import type { LeaderboardRow } from '@/api/types';

defineProps<{ rows: ReadonlyArray<LeaderboardRow>; caption: string; isCompact?: boolean }>();
</script>

<template>
  <div class="scoreboard board" :class="{ 'is-compact': isCompact }">
    <table>
      <caption class="board-caption">{{ caption }}</caption>
      <thead>
        <tr>
          <th scope="col" class="board-rank">#</th>
          <th scope="col">Player</th>
          <th scope="col" class="board-optional">Club</th>
          <th scope="col" class="board-number board-optional">Rounds</th>
          <th scope="col" class="board-number">Correct</th>
          <th scope="col" class="board-number">Best</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.username">
          <td class="board-rank scoreboard-digits">{{ row.rank }}</td>
          <td class="board-player">{{ row.username }}</td>
          <td class="board-optional board-club">{{ row.favorite_club || '—' }}</td>
          <td class="board-number board-optional">{{ row.attempts }}</td>
          <td class="board-number scoreboard-digits">{{ row.total_correct }}</td>
          <td class="board-number">{{ row.best_score_pct }}%</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.board {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

.board-caption {
  text-align: left;
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  padding-bottom: var(--space-3);
}

th {
  text-align: left;
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--touchline);
  padding: var(--space-2) var(--space-2);
  border-bottom: 1px solid rgb(255 255 255 / 0.25);
}

td {
  padding: var(--space-2);
  border-bottom: 1px solid rgb(255 255 255 / 0.12);
}

tbody tr:last-child td {
  border-bottom: 0;
}

.board-rank {
  width: 2.5rem;
}

td.board-rank,
td.scoreboard-digits {
  font-size: 1.6rem;
}

.board-player {
  font-weight: 600;
}

.board-club {
  color: var(--touchline);
}

.board-number {
  text-align: right;
}

.is-compact .board-optional {
  display: none;
}

@media (max-width: 34rem) {
  .board-optional {
    display: none;
  }
}
</style>
