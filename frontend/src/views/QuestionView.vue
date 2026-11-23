<script setup lang="ts">
import { RouterLink } from 'vue-router';

import { getQuestion } from '@/api/resources';
import LoadState from '@/components/LoadState.vue';
import { useAsync } from '@/composables/useAsync';
import { formatDifficulty } from '@/format';

const props = defineProps<{ id: number }>();
const question = useAsync(() => getQuestion(props.id));
</script>

<template>
  <LoadState :is-loading="question.isLoading.value" :error="question.error.value" @retry="question.reload">
    <article v-if="question.data.value" class="stack">
      <p><RouterLink to="/questions">Back to the question bank</RouterLink></p>
      <h1 class="question-text">{{ question.data.value.text }}</h1>
      <dl class="question-facts">
        <div>
          <dt>Era</dt>
          <dd>{{ question.data.value.era_name }}</dd>
        </div>
        <div v-if="question.data.value.topic_names.length">
          <dt>Topics</dt>
          <dd>{{ question.data.value.topic_names.join(', ') }}</dd>
        </div>
        <div>
          <dt>Difficulty</dt>
          <dd>{{ formatDifficulty(question.data.value.difficulty) }}</dd>
        </div>
        <div>
          <dt>Written by</dt>
          <dd>{{ question.data.value.author }}</dd>
        </div>
      </dl>
      <ol class="choices" type="A">
        <li
          v-for="choice in question.data.value.choices"
          :key="choice.id"
          :class="{ 'is-correct': choice.is_correct }"
        >
          {{ choice.text }}
          <span v-if="choice.is_correct" class="choice-flag">correct answer</span>
        </li>
      </ol>
      <p v-if="question.data.value.explanation" class="explanation">{{ question.data.value.explanation }}</p>
      <p v-else class="hint">The answer is revealed after you play a quiz that includes this question.</p>
      <div>
        <RouterLink :to="{ path: '/play', query: { era: question.data.value.era } }" class="button">
          Play {{ question.data.value.era_name }}
        </RouterLink>
      </div>
    </article>
  </LoadState>
</template>

<style scoped>
.question-text {
  max-width: 28ch;
}

.question-facts {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3) var(--space-6);
  margin: 0;
}

.question-facts dt {
  font-size: 0.875rem;
  color: var(--muted);
}

.question-facts dd {
  margin: 0;
  font-weight: 600;
}

.choices {
  display: grid;
  gap: var(--space-2);
  margin: 0;
  padding-left: var(--space-5);
  max-width: 40rem;
}

.choices li {
  padding: var(--space-3) var(--space-4);
  border: 2px solid var(--touchline);
  border-radius: var(--radius);
  background: var(--surface);
}

.choices li.is-correct {
  border-color: var(--right);
}

.choice-flag {
  margin-left: var(--space-2);
  color: var(--right);
  font-weight: 600;
  font-size: 0.875rem;
}

.explanation {
  padding-left: var(--space-4);
  border-left: 4px solid var(--right);
}

.hint {
  color: var(--muted);
}
</style>
