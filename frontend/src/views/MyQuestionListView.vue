<script setup lang="ts">
import { computed, nextTick, ref } from 'vue';
import { RouterLink, useRoute } from 'vue-router';

import { getErrorMessage } from '@/api/client';
import { deleteQuestion, listMyQuestions } from '@/api/resources';
import type { Question } from '@/api/types';
import LoadState from '@/components/LoadState.vue';
import QuestionCard from '@/components/QuestionCard.vue';
import { useAsync } from '@/composables/useAsync';
import { readPageNumber } from '@/format';

const route = useRoute();
const page = readPageNumber(route.query.page);
const questions = useAsync(() => listMyQuestions(page));
const results = computed(() => questions.data.value?.results ?? []);
const confirmingId = ref<number>();
const deletingId = ref<number>();
const deleteError = ref<string>();

function deleteButtonId(questionId: number): string {
  return `delete-question-${questionId}`;
}

function keepButtonId(questionId: number): string {
  return `keep-question-${questionId}`;
}

async function focusElement(elementId: string): Promise<void> {
  await nextTick();
  document.getElementById(elementId)?.focus();
}

async function openDeleteConfirm(questionId: number): Promise<void> {
  confirmingId.value = questionId;
  await focusElement(keepButtonId(questionId));
}

async function closeDeleteConfirm(questionId: number): Promise<void> {
  confirmingId.value = undefined;
  await focusElement(deleteButtonId(questionId));
}

function findCorrectText(question: Question): string {
  return question.choices.find((choice) => choice.is_correct)?.text ?? 'not set';
}

async function handleDelete(id: number): Promise<void> {
  deletingId.value = id;
  deleteError.value = undefined;
  try {
    await deleteQuestion(id);
    confirmingId.value = undefined;
    await questions.reload();
  } catch (error: unknown) {
    deleteError.value = getErrorMessage(error);
  } finally {
    deletingId.value = undefined;
  }
}
</script>

<template>
  <section class="stack">
    <h1>My questions</h1>
    <p class="lede">
      Questions you write go straight into the public bank and into other players' quizzes. You never get them in your
      own rounds.
    </p>
    <div>
      <RouterLink :to="{ name: 'my-question-new' }" class="button">Write a question</RouterLink>
    </div>
    <p v-if="deleteError" class="form-alert" role="alert">Couldn't delete the question: {{ deleteError }}</p>
    <LoadState :is-loading="questions.isLoading.value" :error="questions.error.value" @retry="questions.reload">
      <p v-if="!results.length">
        You haven't written any questions yet. Know a story from football history?
        <RouterLink :to="{ name: 'my-question-new' }">Turn it into a question</RouterLink>.
      </p>
      <template v-else>
        <ul class="ruled-list">
          <li v-for="question in results" :key="question.id">
            <QuestionCard :question="question" :to="{ name: 'question', params: { id: question.id } }">
              <p class="answer">Answer: <strong>{{ findCorrectText(question) }}</strong></p>
              <div class="row-actions">
                <RouterLink :to="{ name: 'my-question-edit', params: { id: question.id } }" class="button button-quiet">
                  Edit
                </RouterLink>
                <button
                  v-if="confirmingId !== question.id"
                  :id="deleteButtonId(question.id)"
                  type="button"
                  class="button button-quiet"
                  @click="openDeleteConfirm(question.id)"
                >
                  Delete
                </button>
                <template v-else>
                  <span class="confirm-text">Delete this question for good?</span>
                  <button
                    type="button"
                    class="button button-danger"
                    :disabled="deletingId === question.id"
                    @click="handleDelete(question.id)"
                  >
                    {{ deletingId === question.id ? 'Deleting…' : 'Delete question' }}
                  </button>
                  <button
                    :id="keepButtonId(question.id)"
                    type="button"
                    class="button button-quiet"
                    @click="closeDeleteConfirm(question.id)"
                  >
                    Keep it
                  </button>
                </template>
              </div>
            </QuestionCard>
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
          <RouterLink v-if="questions.data.value?.next" :to="{ query: { page: page + 1 } }" class="button button-quiet">
            Next page
          </RouterLink>
        </nav>
      </template>
    </LoadState>
  </section>
</template>

<style scoped>
.answer {
  color: var(--right);
}

.row-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2) var(--space-3);
}

.confirm-text {
  font-weight: 600;
}

.pager {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-5);
}
</style>
