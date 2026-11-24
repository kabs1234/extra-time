<script setup lang="ts">
import { computed, ref } from 'vue';

import { listAllQuestions, listEras, listTopics } from '@/api/resources';
import type { Era, Question } from '@/api/types';
import FormField from '@/components/FormField.vue';
import LoadState from '@/components/LoadState.vue';
import QuestionCard from '@/components/QuestionCard.vue';
import { useAsync } from '@/composables/useAsync';
import { formatYears } from '@/format';

type EraGroup = {
  readonly era: Era;
  readonly questions: ReadonlyArray<Question>;
};

const bank = useAsync(() => Promise.all([listAllQuestions(), listEras(), listTopics()]));
const chosenEra = ref<number | ''>('');
const chosenTopic = ref<number | ''>('');

const matchingQuestions = computed(() =>
  (bank.data.value?.[0] ?? []).filter(
    (question) =>
      (chosenEra.value === '' || question.era === chosenEra.value) &&
      (chosenTopic.value === '' || question.topics.includes(chosenTopic.value)),
  ),
);

const eraGroups = computed<ReadonlyArray<EraGroup>>(() =>
  (bank.data.value?.[1] ?? [])
    .map((era) => ({ era, questions: matchingQuestions.value.filter((question) => question.era === era.id) }))
    .filter((group) => group.questions.length > 0),
);

function clearFilters(): void {
  chosenEra.value = '';
  chosenTopic.value = '';
}
</script>

<template>
  <section class="stack">
    <h1>Question bank</h1>
    <p class="lede">
      Every question in the game, written by our curator and by players. Answers stay hidden until you play.
    </p>
    <LoadState :is-loading="bank.isLoading.value" :error="bank.error.value" @retry="bank.reload">
      <template v-if="bank.data.value">
        <div class="filters">
          <FormField id="bank-era" label="Era">
            <select id="bank-era" v-model="chosenEra">
              <option value="">All eras</option>
              <option v-for="era in bank.data.value[1]" :key="era.id" :value="era.id">{{ era.name }}</option>
            </select>
          </FormField>
          <FormField id="bank-topic" label="Topic">
            <select id="bank-topic" v-model="chosenTopic">
              <option value="">All topics</option>
              <option v-for="topic in bank.data.value[2]" :key="topic.id" :value="topic.id">{{ topic.name }}</option>
            </select>
          </FormField>
        </div>
        <p class="count" role="status">{{ matchingQuestions.length }} of {{ bank.data.value[0].length }} questions</p>
        <p v-if="!eraGroups.length">
          No question matches that era and topic.
          <button type="button" class="link-button" @click="clearFilters">Show every question</button>
        </p>
        <section v-for="group in eraGroups" :key="group.era.id" class="era-group" :aria-label="group.era.name">
          <h2>
            {{ group.era.name }} <span class="era-years">{{ formatYears(group.era) }}</span>
          </h2>
          <ul class="ruled-list">
            <li v-for="question in group.questions" :key="question.id">
              <QuestionCard :question="question" :to="{ name: 'question', params: { id: question.id } }" />
            </li>
          </ul>
        </section>
      </template>
    </LoadState>
  </section>
</template>

<style scoped>
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
}

.filters > * {
  flex: 1 1 14rem;
  max-width: 20rem;
}

.count {
  color: var(--muted);
}

.era-group {
  display: grid;
  gap: var(--space-3);
  margin-top: var(--space-4);
}

.era-years {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--pitch);
}

.link-button {
  padding: 0;
  border: 0;
  background: none;
  color: var(--pitch);
  text-decoration: underline;
  cursor: pointer;
}
</style>
