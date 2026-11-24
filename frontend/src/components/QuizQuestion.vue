<script setup lang="ts">
import { computed } from 'vue';

import type { Question } from '@/api/types';

const props = defineProps<{
  question: Question;
  position: number;
  total: number;
  chosenId: number | null;
  isBusy?: boolean;
}>();
const emit = defineEmits<{ choose: [choiceId: number | null]; back: []; next: [] }>();

const isFirst = computed(() => props.position === 1);
const isLast = computed(() => props.position === props.total);
const answeredWidth = computed(() => `${(100 * props.position) / props.total}%`);
</script>

<template>
  <section class="quiz-question" :aria-label="`Question ${position} of ${total}`">
    <div class="scoreboard progress">
      <p class="progress-count">
        <span class="scoreboard-digits">{{ position }}</span>
        <span class="progress-of">of</span>
        <span class="scoreboard-digits">{{ total }}</span>
      </p>
      <p class="progress-era">{{ question.era_name }}</p>
      <div class="progress-bar" aria-hidden="true"><span :style="{ width: answeredWidth }" /></div>
    </div>

    <fieldset class="choices">
      <legend class="question-text">{{ question.text }}</legend>
      <label v-for="choice in question.choices" :key="choice.id" class="choice">
        <input
          type="radio"
          :name="`question-${question.id}`"
          :checked="chosenId === choice.id"
          @change="emit('choose', choice.id)"
        />
        <span>{{ choice.text }}</span>
      </label>
    </fieldset>

    <div class="quiz-actions">
      <button type="button" class="button button-quiet" :disabled="isFirst || isBusy" @click="emit('back')">
        Back
      </button>
      <button
        v-if="chosenId !== null"
        type="button"
        class="button button-quiet"
        :disabled="isBusy"
        @click="emit('choose', null)"
      >
        Clear answer
      </button>
      <button type="button" class="button" :disabled="isBusy" @click="emit('next')">
        {{ isLast ? 'Finish and see score' : chosenId === null ? 'Skip' : 'Next question' }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.quiz-question {
  display: grid;
  gap: var(--space-5);
  max-width: 44rem;
}

.progress {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: end;
  gap: var(--space-2) var(--space-4);
}

.progress-count {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
}

.progress-count .scoreboard-digits {
  font-size: 2.75rem;
}

.progress-of {
  color: var(--touchline);
}

.progress-era {
  justify-self: end;
  font-family: var(--font-display);
  font-size: 1.15rem;
  color: var(--touchline);
}

.progress-bar {
  grid-column: 1 / -1;
  height: 4px;
  background: rgb(255 255 255 / 0.15);
}

.progress-bar span {
  display: block;
  height: 100%;
  background: var(--amber);
  transition: width 200ms ease-out;
}

.choices {
  display: grid;
  gap: var(--space-2);
  margin: 0;
  padding: 0;
  border: 0;
}

.question-text {
  margin-bottom: var(--space-4);
  font-family: var(--font-display);
  font-size: clamp(1.6rem, 4vw, 2.1rem);
  font-weight: 700;
  line-height: 1.15;
}

.choice input {
  position: absolute;
  opacity: 0;
}

.choice span {
  display: block;
  padding: var(--space-3) var(--space-4);
  border: 2px solid var(--touchline);
  border-radius: var(--radius);
  background: var(--surface);
  font-size: 1.05rem;
  cursor: pointer;
}

.choice span:hover {
  border-color: var(--pitch);
}

.choice input:checked + span {
  border-color: var(--pitch);
  background: var(--pitch);
  color: var(--surface);
  font-weight: 600;
}

.choice input:focus-visible + span {
  outline: 3px solid var(--amber);
  outline-offset: 2px;
}

.quiz-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.quiz-actions .button:last-child {
  margin-left: auto;
}
</style>
