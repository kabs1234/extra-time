<script setup lang="ts">
import { ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';

import { getErrorMessage } from '@/api/client';
import { deleteAttempt, getAttempt } from '@/api/resources';
import AttemptReview from '@/components/AttemptReview.vue';
import LoadState from '@/components/LoadState.vue';
import { useAsync } from '@/composables/useAsync';

const props = defineProps<{ id: number }>();
const router = useRouter();
const attempt = useAsync(() => getAttempt(props.id));
const isConfirmingDelete = ref(false);
const isDeleting = ref(false);
const deleteError = ref<string>();

async function handleDelete(): Promise<void> {
  isDeleting.value = true;
  deleteError.value = undefined;
  try {
    await deleteAttempt(props.id);
    await router.push({ name: 'results' });
  } catch (error: unknown) {
    deleteError.value = getErrorMessage(error);
  } finally {
    isDeleting.value = false;
  }
}
</script>

<template>
  <div class="stack">
    <p><RouterLink to="/results">Back to my results</RouterLink></p>
    <LoadState
      :is-loading="attempt.isLoading.value"
      :error="attempt.error.value"
      :is-missing="attempt.isMissing.value"
      @retry="attempt.reload"
    >
      <template #missing>
        <p>This result doesn't exist. It may have been deleted.</p>
      </template>
      <template v-if="attempt.data.value">
        <h1>Round result</h1>
        <AttemptReview :attempt="attempt.data.value">
          <div class="delete-zone">
            <p v-if="deleteError" class="form-alert" role="alert">Couldn't delete this result: {{ deleteError }}</p>
            <button
              v-if="!isConfirmingDelete"
              type="button"
              class="button button-quiet"
              @click="isConfirmingDelete = true"
            >
              Delete this result
            </button>
            <div v-else class="delete-confirm" role="group" aria-label="Confirm deletion">
              <p>Delete this result for good? Your leaderboard total will go down by {{ attempt.data.value.score }}.</p>
              <button type="button" class="button button-danger" :disabled="isDeleting" @click="handleDelete">
                {{ isDeleting ? 'Deleting…' : 'Delete result' }}
              </button>
              <button type="button" class="button button-quiet" @click="isConfirmingDelete = false">Keep it</button>
            </div>
          </div>
        </AttemptReview>
      </template>
    </LoadState>
  </div>
</template>

<style scoped>
.delete-zone {
  display: grid;
  gap: var(--space-3);
  justify-items: start;
}

.delete-confirm {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
}

.delete-confirm p {
  flex-basis: 100%;
}
</style>
