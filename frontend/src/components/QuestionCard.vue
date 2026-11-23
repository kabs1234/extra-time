<script setup lang="ts">
import { RouterLink, type RouteLocationRaw } from 'vue-router';

import type { Question } from '@/api/types';
import { formatDifficulty } from '@/format';

defineProps<{ question: Question; to: RouteLocationRaw }>();
</script>

<template>
  <article class="question-card">
    <h3 class="question-card-title">
      <RouterLink :to="to">{{ question.text }}</RouterLink>
    </h3>
    <p class="question-card-facts">
      <span class="question-card-era">{{ question.era_name }}</span>
      <span v-for="topic in question.topic_names" :key="topic" class="question-card-topic">{{ topic }}</span>
      <span class="question-card-difficulty">{{ formatDifficulty(question.difficulty) }}</span>
    </p>
    <slot />
  </article>
</template>

<style scoped>
.question-card {
  display: grid;
  gap: var(--space-2);
}

.question-card-title {
  font-family: var(--font-body);
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1.4;
}

.question-card-title a {
  color: var(--ink);
  text-decoration: none;
}

.question-card-title a:hover {
  color: var(--pitch);
  text-decoration: underline;
}

.question-card-facts {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  font-size: 0.875rem;
}

.question-card-facts span {
  padding: 0 var(--space-2);
  border: 1px solid var(--touchline);
  border-radius: var(--radius);
  background: var(--surface);
}

.question-card-facts .question-card-era {
  border-color: var(--pitch);
  color: var(--pitch);
  font-weight: 600;
}

.question-card-difficulty {
  color: var(--muted);
}
</style>
