<script setup lang="ts">
import { computed, ref, shallowRef } from 'vue';
import { RouterLink, useRoute } from 'vue-router';

import { getErrorMessage, getFieldErrors } from '@/api/client';
import { listEras, listTopics, startQuiz, submitAttempt } from '@/api/resources';
import type { Attempt, AttemptInput, Question, QuizFilters } from '@/api/types';
import AttemptReview from '@/components/AttemptReview.vue';
import LoadState from '@/components/LoadState.vue';
import QuizQuestion from '@/components/QuizQuestion.vue';
import QuizSetup from '@/components/QuizSetup.vue';
import { useAsync } from '@/composables/useAsync';

const Phase = {
  Setup: 'setup',
  Loading: 'loading',
  Empty: 'empty',
  Playing: 'playing',
  Result: 'result',
} as const;
type Phase = (typeof Phase)[keyof typeof Phase];

const route = useRoute();
const options = useAsync(() => Promise.all([listEras(), listTopics()]));

const phase = ref<Phase>(Phase.Setup);
const filters = shallowRef<QuizFilters>({ count: 10 });
const questions = shallowRef<ReadonlyArray<Question>>([]);
const answers = shallowRef<ReadonlyMap<number, number | null>>(new Map());
const currentIndex = ref(0);
const attempt = shallowRef<Attempt>();
const startError = ref<string>();
const submitError = ref<string>();
const isSubmitting = ref(false);

const currentQuestion = computed(() => questions.value[currentIndex.value]);
const answeredCount = computed(() => [...answers.value.values()].filter((choiceId) => choiceId !== null).length);

function readNumberQuery(value: unknown): number | undefined {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : undefined;
}

async function handleStart(chosenFilters: QuizFilters): Promise<void> {
  filters.value = chosenFilters;
  startError.value = undefined;
  phase.value = Phase.Loading;
  try {
    questions.value = await startQuiz(chosenFilters);
    answers.value = new Map();
    currentIndex.value = 0;
    phase.value = questions.value.length ? Phase.Playing : Phase.Empty;
  } catch (error: unknown) {
    startError.value = getErrorMessage(error);
    phase.value = Phase.Setup;
  }
}

function handleChoose(choiceId: number | null): void {
  const question = currentQuestion.value;
  if (question) {
    answers.value = new Map([...answers.value, [question.id, choiceId]]);
  }
}

function handleBack(): void {
  currentIndex.value = Math.max(0, currentIndex.value - 1);
}

async function handleNext(): Promise<void> {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value += 1;
    return;
  }
  await handleSubmit();
}

async function handleSubmit(): Promise<void> {
  if (isSubmitting.value) {
    return;
  }
  isSubmitting.value = true;
  submitError.value = undefined;
  try {
    attempt.value = await submitAttempt(buildAttemptInput());
    phase.value = Phase.Result;
  } catch (error: unknown) {
    submitError.value = describeSubmitFailure(error);
  } finally {
    isSubmitting.value = false;
  }
}

function describeSubmitFailure(error: unknown): string {
  const messages = Object.values(getFieldErrors(error)).flat();
  return messages.length > 0 ? messages.join(' ') : getErrorMessage(error);
}

function buildAttemptInput(): AttemptInput {
  return {
    era: filters.value.era,
    topic: filters.value.topic,
    answers: questions.value.map((question) => ({
      question: question.id,
      choice: answers.value.get(question.id) ?? null,
    })),
  };
}

function handlePlayAgain(): void {
  attempt.value = undefined;
  phase.value = Phase.Setup;
}
</script>

<template>
  <div class="stack">
    <template v-if="phase === Phase.Setup">
      <h1>Set up a round</h1>
      <p class="lede">Choose an era, a topic, or neither for questions from all of football history.</p>
      <p v-if="startError" class="form-alert" role="alert">Couldn't start the quiz: {{ startError }}</p>
      <LoadState :is-loading="options.isLoading.value" :error="options.error.value" @retry="options.reload">
        <QuizSetup
          v-if="options.data.value"
          :eras="options.data.value[0]"
          :topics="options.data.value[1]"
          :initial-era="readNumberQuery(route.query.era)"
          :initial-topic="readNumberQuery(route.query.topic)"
          @start="handleStart"
        />
      </LoadState>
    </template>

    <p v-else-if="phase === Phase.Loading" role="status">Picking your questions…</p>

    <template v-else-if="phase === Phase.Empty">
      <h1>No questions for that pick</h1>
      <p class="lede">
        There are no questions you can play for this era and topic together. Questions you wrote yourself are left out.
        Try a different era or topic, or play all of history.
      </p>
      <div>
        <button type="button" class="button" @click="phase = Phase.Setup">Change the filters</button>
      </div>
    </template>

    <template v-else-if="phase === Phase.Playing && currentQuestion">
      <QuizQuestion
        :key="currentQuestion.id"
        :question="currentQuestion"
        :position="currentIndex + 1"
        :total="questions.length"
        :chosen-id="answers.get(currentQuestion.id) ?? null"
        :is-busy="isSubmitting"
        @choose="handleChoose"
        @back="handleBack"
        @next="handleNext"
      />
      <p v-if="isSubmitting" role="status">Saving your answers…</p>
      <div v-if="submitError" class="form-alert submit-error" role="alert">
        <p>Your answers weren't saved: {{ submitError }}</p>
        <p>They are still here. You answered {{ answeredCount }} of {{ questions.length }}.</p>
        <div>
          <button type="button" class="button" :disabled="isSubmitting" @click="handleSubmit">Try saving again</button>
        </div>
      </div>
    </template>

    <template v-else-if="phase === Phase.Result && attempt">
      <h1>Full time</h1>
      <AttemptReview :attempt="attempt">
        <div class="result-actions">
          <button type="button" class="button" @click="handlePlayAgain">Play again</button>
          <RouterLink to="/results" class="button button-quiet">See all my results</RouterLink>
        </div>
      </AttemptReview>
    </template>
  </div>
</template>

<style scoped>
.submit-error {
  display: grid;
  gap: var(--space-2);
  max-width: 44rem;
}

.result-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}
</style>
