<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink, useRoute } from 'vue-router';

import { listQuestions } from '@/api/resources';
import LoadState from '@/components/LoadState.vue';
import QuestionCard from '@/components/QuestionCard.vue';
import { useAsync } from '@/composables/useAsync';
import { readPageNumber } from '@/format';

const route = useRoute();
const page = readPageNumber(route.query.page);
const questions = useAsync(() => listQuestions(page));
const results = computed(() => questions.data.value?.results ?? []);
</script>

<template>
  <section class="stack">
    <h1>Question bank</h1>
    <p class="lede">
      Every question in the game, written by our curator and by players. Answers stay hidden until you play.
    </p>
    <LoadState :is-loading="questions.isLoading.value" :error="questions.error.value" @retry="questions.reload">
      <p v-if="!results.length">
        There are no questions on this page. <RouterLink to="/questions">Go to the first page</RouterLink>.
      </p>
      <template v-else>
        <p class="count">{{ questions.data.value?.count }} questions</p>
        <ul class="ruled-list">
          <li v-for="question in results" :key="question.id">
            <QuestionCard :question="question" :to="{ name: 'question', params: { id: question.id } }" />
          </li>
        </ul>
        <nav class="pager" aria-label="Pages">
          <RouterLink
            v-if="questions.data.value?.previous"
            :to="{ query: { page: page - 1 } }"
            class="button button-quiet"
          >
            Previous page
          </RouterLink>
          <span>Page {{ page }}</span>
          <RouterLink v-if="questions.data.value?.next" :to="{ query: { page: page + 1 } }" class="button button-quiet">
            Next page
          </RouterLink>
        </nav>
      </template>
    </LoadState>
  </section>
</template>

<style scoped>
.count {
  color: var(--muted);
}

.pager {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4);
  margin-top: var(--space-5);
}
</style>
