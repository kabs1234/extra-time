<script setup lang="ts">
import { reactive, ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';

import { getFieldErrors, getFormMessage, MissingResourceError, type FieldErrors } from '@/api/client';
import { createQuestion, getQuestion, listEras, listTopics, updateQuestion } from '@/api/resources';
import { Difficulty, type Era, type Question, type QuestionInput, type Topic } from '@/api/types';
import { session } from '@/auth/session';
import ChoiceEditor, { type ChoiceDraft } from '@/components/ChoiceEditor.vue';
import FormField from '@/components/FormField.vue';
import LoadState from '@/components/LoadState.vue';
import { useAsync } from '@/composables/useAsync';
import { formatDifficulty, formatYears } from '@/format';

type QuestionDraft = {
  text: string;
  era: number | '';
  topics: number[];
  difficulty: Difficulty;
  explanation: string;
  choices: ReadonlyArray<ChoiceDraft>;
};

type FormOptions = {
  readonly eras: ReadonlyArray<Era>;
  readonly topics: ReadonlyArray<Topic>;
};

const NOT_YOUR_QUESTION = 'You can only edit questions you wrote.';
const MISSING_ANSWER_TEXT = 'Every answer needs some text.';
const MISSING_ERA = 'Choose the era this question belongs to.';
const BLANK_CHOICES: ReadonlyArray<ChoiceDraft> = [
  { key: 1, text: '', is_correct: true },
  { key: 2, text: '', is_correct: false },
  { key: 3, text: '', is_correct: false },
  { key: 4, text: '', is_correct: false },
];

const props = defineProps<{ id?: number }>();
const router = useRouter();
const isEditing = props.id !== undefined;

const draft = reactive<QuestionDraft>({
  text: '',
  era: '',
  topics: [],
  difficulty: Difficulty.Medium,
  explanation: '',
  choices: BLANK_CHOICES,
});
const fieldErrors = ref<FieldErrors>({});
const formMessage = ref<string>();
const isSaving = ref(false);

const options = useAsync(loadFormOptions);

async function loadFormOptions(): Promise<FormOptions> {
  const [eras, topics] = await Promise.all([listEras(), listTopics(), loadExistingQuestion()]);
  return { eras, topics };
}

async function loadExistingQuestion(): Promise<void> {
  if (props.id === undefined) {
    return;
  }
  const question = await getQuestion(props.id);
  if (question.author !== session.user?.username) {
    throw new MissingResourceError(NOT_YOUR_QUESTION);
  }
  fillDraft(question);
}

function fillDraft(question: Question): void {
  draft.text = question.text;
  draft.era = question.era;
  draft.topics = [...question.topics];
  draft.difficulty = question.difficulty;
  draft.explanation = question.explanation ?? '';
  draft.choices = question.choices.map((choice, index) => ({
    key: index + 1,
    text: choice.text,
    is_correct: choice.is_correct === true,
  }));
}

function findDraftProblems(): FieldErrors {
  const hasBlankAnswer = draft.choices.some((choice) => choice.text.trim() === '');
  return {
    ...(draft.era === '' ? { era: [MISSING_ERA] } : {}),
    ...(hasBlankAnswer ? { choices: [MISSING_ANSWER_TEXT] } : {}),
  };
}

function buildInput(): QuestionInput {
  return {
    text: draft.text,
    era: draft.era === '' ? null : draft.era,
    topics: draft.topics,
    difficulty: draft.difficulty,
    explanation: draft.explanation,
    choices: draft.choices.map(({ text, is_correct }) => ({ text: text.trim(), is_correct })),
  };
}

function saveDraft(input: QuestionInput): Promise<Question> {
  return props.id === undefined ? createQuestion(input) : updateQuestion(props.id, input);
}

async function handleSubmit(): Promise<void> {
  fieldErrors.value = {};
  formMessage.value = undefined;
  const problems = findDraftProblems();
  if (Object.keys(problems).length > 0) {
    fieldErrors.value = problems;
    return;
  }
  isSaving.value = true;
  try {
    await saveDraft(buildInput());
    await router.push({ name: 'my-questions' });
  } catch (error: unknown) {
    fieldErrors.value = getFieldErrors(error);
    formMessage.value = getFormMessage(error);
  } finally {
    isSaving.value = false;
  }
}
</script>

<template>
  <section class="stack">
    <p><RouterLink :to="{ name: 'my-questions' }">Back to my questions</RouterLink></p>
    <h1>{{ isEditing ? 'Edit your question' : 'Write a question' }}</h1>
    <LoadState
      :is-loading="options.isLoading.value"
      :error="options.error.value"
      :is-missing="options.isMissing.value"
      @retry="options.reload"
    >
      <template #missing>
        <p>
          This question doesn't exist or someone else wrote it. Pick one from
          <RouterLink :to="{ name: 'my-questions' }">your list</RouterLink> instead.
        </p>
      </template>
      <form v-if="options.data.value" class="form question-form" novalidate @submit.prevent="handleSubmit">
        <p v-if="formMessage" class="form-alert" role="alert">{{ formMessage }}</p>
        <FormField id="question-text" label="Question" :errors="fieldErrors.text">
          <textarea id="question-text" v-model.trim="draft.text" rows="3" required />
        </FormField>
        <FormField id="question-era" label="Era" :errors="fieldErrors.era">
          <select id="question-era" v-model="draft.era" required>
            <option value="" disabled>Choose the era it belongs to</option>
            <option v-for="era in options.data.value.eras" :key="era.id" :value="era.id">
              {{ era.name }} ({{ formatYears(era) }})
            </option>
          </select>
        </FormField>
        <fieldset class="topic-picker">
          <legend>Topics</legend>
          <label v-for="topic in options.data.value.topics" :key="topic.id" class="topic-option">
            <input v-model="draft.topics" type="checkbox" :value="topic.id" />
            {{ topic.name }}
          </label>
          <p v-if="fieldErrors.topics" class="topic-error">{{ fieldErrors.topics.join(' ') }}</p>
        </fieldset>
        <FormField id="question-difficulty" label="Difficulty" :errors="fieldErrors.difficulty">
          <select id="question-difficulty" v-model="draft.difficulty">
            <option v-for="level in Object.values(Difficulty)" :key="level" :value="level">
              {{ formatDifficulty(level) }}
            </option>
          </select>
        </FormField>
        <ChoiceEditor v-model="draft.choices" :errors="fieldErrors.choices" />
        <FormField
          id="question-explanation"
          label="Explanation"
          hint="Shown to players after they answer. Say why the answer is right and where the fact comes from."
          :errors="fieldErrors.explanation"
        >
          <textarea
            id="question-explanation"
            v-model.trim="draft.explanation"
            rows="3"
            aria-describedby="question-explanation-hint"
          />
        </FormField>
        <div>
          <button type="submit" class="button" :disabled="isSaving">
            {{ isSaving ? 'Saving…' : isEditing ? 'Save changes' : 'Publish question' }}
          </button>
        </div>
      </form>
    </LoadState>
  </section>
</template>

<style scoped>
.question-form {
  max-width: 40rem;
}

.topic-picker {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-4);
  margin: 0;
  padding: 0;
  border: 0;
}

.topic-picker legend {
  margin-bottom: var(--space-1);
  font-weight: 700;
}

.topic-option {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.topic-option input {
  accent-color: var(--pitch);
}

.topic-error {
  flex-basis: 100%;
  color: var(--red-card);
  font-size: 0.875rem;
  font-weight: 600;
}
</style>
