<script setup lang="ts">
import { RouterLink } from 'vue-router';

import { getLeaderboard } from '@/api/resources';
import LeaderboardTable from '@/components/LeaderboardTable.vue';
import LoadState from '@/components/LoadState.vue';
import { useAsync } from '@/composables/useAsync';

const leaderboard = useAsync(getLeaderboard);
</script>

<template>
  <section class="stack">
    <h1>Leaderboard</h1>
    <p class="lede">
      Ranked by correct answers across every round. Ties go to the better single round, then to whoever played
      first.
    </p>
    <LoadState :is-loading="leaderboard.isLoading.value" :error="leaderboard.error.value" @retry="leaderboard.reload">
      <p v-if="!leaderboard.data.value?.length">
        Nobody has played yet. <RouterLink to="/play">Play a round</RouterLink> to open the table.
      </p>
      <LeaderboardTable v-else :rows="leaderboard.data.value" caption="Top 20 players" />
    </LoadState>
  </section>
</template>
