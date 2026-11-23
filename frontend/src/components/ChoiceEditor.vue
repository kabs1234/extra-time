<script setup lang="ts">
import { computed } from 'vue';

export type ChoiceDraft = {
  readonly key: number;
  readonly text: string;
  readonly is_correct: boolean;
};

const MIN_CHOICES = 2;
const MAX_CHOICES = 4;

const choices = defineModel<ReadonlyArray<ChoiceDraft>>({ required: true });
defineProps<{ errors?: ReadonlyArray<string> }>();

const canAdd = computed(() => choices.value.length < MAX_CHOICES);
const canRemove = computed(() => choices.value.length > MIN_CHOICES);

function handleTextInput(key: number, event: Event): void {
  if (event.target instanceof HTMLInputElement) {
    const text = event.target.value;
    choices.value = choices.value.map((choice) => (choice.key === key ? { ...choice, text } : choice));
  }
}

function markCorrect(key: number): void {
  choices.value = choices.value.map((choice) => ({ ...choice, is_correct: choice.key === key }));
}

function addChoice(): void {
  const nextKey = Math.max(0, ...choices.value.map((choice) => choice.key)) + 1;
  choices.value = [...choices.value, { key: nextKey, text: '', is_correct: false }];
}

function removeChoice(key: number): void {
  choices.value = choices.value.filter((choice) => choice.key !== key);
}
</script>

<template>
  <fieldset class="choice-editor" :class="{ 'has-error': errors?.length }">
    <legend>Answers</legend>
    <p class="choice-editor-hint">Write 2 to 4 answers and mark the one that is correct.</p>
    <ul v-if="errors?.length" class="choice-editor-errors" role="alert">
      <li v-for="message in errors" :key="message">{{ message }}</li>
    </ul>
    <div v-for="(choice, index) in choices" :key="choice.key" class="choice-row">
      <label class="choice-correct">
        <input
          type="radio"
          name="correct-choice"
          :checked="choice.is_correct"
          @change="markCorrect(choice.key)"
        />
        <span>Correct</span>
      </label>
      <label class="visually-hidden" :for="`choice-${choice.key}`">Answer {{ index + 1 }}</label>
      <input
        :id="`choice-${choice.key}`"
        class="choice-text"
        :value="choice.text"
        maxlength="200"
        :placeholder="`Answer ${index + 1}`"
        @input="handleTextInput(choice.key, $event)"
      />
      <button
        type="button"
        class="choice-remove"
        :disabled="!canRemove"
        :aria-label="`Remove answer ${index + 1}`"
        @click="removeChoice(choice.key)"
      >
        Remove
      </button>
    </div>
    <div>
      <button type="button" class="button button-quiet" :disabled="!canAdd" @click="addChoice">Add an answer</button>
    </div>
  </fieldset>
</template>

<style scoped>
.choice-editor {
  display: grid;
  gap: var(--space-3);
  margin: 0;
  padding: 0;
  border: 0;
}

.choice-editor legend {
  margin-bottom: var(--space-1);
  font-weight: 700;
}

.choice-editor-hint {
  color: var(--muted);
  font-size: 0.875rem;
}

.choice-editor-errors {
  margin: 0;
  padding: 0;
  list-style: none;
  color: var(--red-card);
  font-size: 0.875rem;
  font-weight: 600;
}

.choice-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);
}

.choice-correct {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: 0.875rem;
}

.choice-correct input {
  width: 1.15rem;
  height: 1.15rem;
  accent-color: var(--pitch);
}

.choice-text {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: 2px solid var(--ink);
  border-radius: var(--radius);
  background: var(--surface);
}

.has-error .choice-text {
  border-color: var(--red-card);
}

.choice-remove {
  padding: var(--space-1) var(--space-2);
  border: 0;
  background: none;
  color: var(--red-card);
  text-decoration: underline;
  cursor: pointer;
}

.choice-remove:disabled {
  color: var(--muted);
  text-decoration: none;
  cursor: not-allowed;
}
</style>
