<script setup lang="ts">
import { reactive } from 'vue';

import type { Era, QuizFilters, Topic } from '@/api/types';
import FormField from '@/components/FormField.vue';
import { formatYears } from '@/format';

const QUIZ_LENGTHS = [5, 10, 15, 20] as const;
const DEFAULT_LENGTH = 10;

const props = defineProps<{
  eras: ReadonlyArray<Era>;
  topics: ReadonlyArray<Topic>;
  initialEra?: number;
  initialTopic?: number;
}>();
const emit = defineEmits<{ start: [filters: QuizFilters] }>();

const choice = reactive<{ era: number | ''; topic: number | ''; count: number }>({
  era: props.initialEra ?? '',
  topic: props.initialTopic ?? '',
  count: DEFAULT_LENGTH,
});

function handleSubmit(): void {
  emit('start', {
    era: choice.era === '' ? undefined : choice.era,
    topic: choice.topic === '' ? undefined : choice.topic,
    count: choice.count,
  });
}
</script>

<template>
  <form class="form setup" @submit.prevent="handleSubmit">
    <FormField id="setup-era" label="Era">
      <select id="setup-era" v-model="choice.era">
        <option value="">All of football history</option>
        <option v-for="era in eras" :key="era.id" :value="era.id">
          {{ era.name }} ({{ formatYears(era) }})
        </option>
      </select>
    </FormField>
    <FormField id="setup-topic" label="Topic">
      <select id="setup-topic" v-model="choice.topic">
        <option value="">Any topic</option>
        <option v-for="topic in topics" :key="topic.id" :value="topic.id">{{ topic.name }}</option>
      </select>
    </FormField>
    <fieldset class="setup-length">
      <legend>Questions in this round</legend>
      <label v-for="length in QUIZ_LENGTHS" :key="length" class="setup-length-option">
        <input v-model="choice.count" type="radio" name="count" :value="length" />
        <span>{{ length }}</span>
      </label>
    </fieldset>
    <div>
      <button type="submit" class="button">Kick off</button>
    </div>
  </form>
</template>

<style scoped>
.setup-length {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin: 0;
  padding: 0;
  border: 0;
}

.setup-length legend {
  margin-bottom: var(--space-1);
  font-weight: 700;
}

.setup-length-option input {
  position: absolute;
  opacity: 0;
}

.setup-length-option span {
  display: inline-grid;
  place-items: center;
  min-width: 3.25rem;
  min-height: 2.75rem;
  border: 2px solid var(--ink);
  border-radius: var(--radius);
  background: var(--surface);
  font-family: var(--font-display);
  font-size: 1.4rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  cursor: pointer;
}

.setup-length-option input:checked + span {
  background: var(--pitch-deep);
  border-color: var(--pitch-deep);
  color: var(--amber);
}

.setup-length-option input:focus-visible + span {
  outline: 3px solid var(--amber);
  outline-offset: 2px;
}
</style>
