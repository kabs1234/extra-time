<script setup lang="ts">
import { computed } from 'vue';

import type { Attempt } from '@/api/types';
import { formatDate } from '@/format';

const props = defineProps<{ attempt: Attempt }>();

const filterLabel = computed(
  () => [props.attempt.era_name, props.attempt.topic_name].filter(Boolean).join(', ') || 'All of football history',
);
</script>

<template>
  <section class="review">
    <div class="scoreboard final-score">
      <p class="final-score-line">
        <span class="scoreboard-digits final-score-digits">{{ attempt.score }}</span>
        <span class="final-score-of">out of</span>
        <span class="scoreboard-digits final-score-digits">{{ attempt.total }}</span>
      </p>
      <p class="final-score-meta">
        {{ attempt.percent }}% correct in {{ filterLabel }}, played {{ formatDate(attempt.created_at) }}
      </p>
    </div>

    <slot />

    <ol class="answers">
      <li
        v-for="(answer, index) in attempt.answers"
        :key="index"
        class="answer"
        :class="answer.is_correct ? 'is-right' : 'is-wrong'"
      >
        <h3 class="answer-question">{{ answer.question_text }}</h3>
        <p v-if="answer.is_correct" class="answer-verdict">
          Right: <strong>{{ answer.correct_text }}</strong>
        </p>
        <p v-else class="answer-verdict">
          <template v-if="answer.chosen_text">You said <strong>{{ answer.chosen_text }}</strong>. </template>
          <template v-else>Skipped. </template>
          The answer is <strong>{{ answer.correct_text }}</strong>.
        </p>
        <p v-if="answer.explanation" class="answer-explanation">{{ answer.explanation }}</p>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.review {
  display: grid;
  gap: var(--space-5);
  max-width: 48rem;
}

.final-score {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-5) var(--space-6);
}

.final-score-line {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
}

.final-score-digits {
  font-size: clamp(4rem, 14vw, 6.5rem);
}

.final-score-of {
  font-family: var(--font-display);
  font-size: 1.5rem;
  color: var(--touchline);
}

.final-score-meta {
  color: var(--touchline);
}

.answers {
  display: grid;
  gap: var(--space-3);
  margin: 0;
  padding-left: var(--space-5);
}

.answer {
  display: grid;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-4);
  border-left: 6px solid;
  background: var(--surface);
}

.answer::marker {
  font-family: var(--font-display);
  font-weight: 700;
}

.answer.is-right {
  border-left-color: var(--right);
}

.answer.is-wrong {
  border-left-color: var(--red-card);
}

.answer-question {
  font-family: var(--font-body);
  font-size: 1.05rem;
  font-weight: 600;
  line-height: 1.4;
}

.is-right .answer-verdict {
  color: var(--right);
}

.is-wrong .answer-verdict strong:last-child {
  color: var(--right);
}

.answer-explanation {
  color: var(--muted);
}
</style>
