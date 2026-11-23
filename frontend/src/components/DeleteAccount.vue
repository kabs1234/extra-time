<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { getFieldErrors, getFormMessage, type FieldErrors } from '@/api/client';
import { deleteMe } from '@/api/resources';
import { clearSession } from '@/auth/session';
import FormField from '@/components/FormField.vue';

const router = useRouter();
const password = ref('');
const fieldErrors = ref<FieldErrors>({});
const formMessage = ref<string>();
const isDeleting = ref(false);

async function handleSubmit(): Promise<void> {
  isDeleting.value = true;
  fieldErrors.value = {};
  formMessage.value = undefined;
  try {
    await deleteMe(password.value);
    clearSession();
    await router.push({ name: 'home' });
  } catch (error: unknown) {
    fieldErrors.value = getFieldErrors(error);
    formMessage.value = getFormMessage(error);
  } finally {
    isDeleting.value = false;
  }
}
</script>

<template>
  <form class="form danger-zone" novalidate @submit.prevent="handleSubmit">
    <h2>Delete account</h2>
    <p>
      This removes your account, your results and every question you wrote. Your rows leave the leaderboard. It can't
      be undone.
    </p>
    <p v-if="formMessage" class="form-alert" role="alert">{{ formMessage }}</p>
    <FormField id="delete-password" label="Type your password to confirm" :errors="fieldErrors.password">
      <input id="delete-password" v-model="password" type="password" autocomplete="current-password" required />
    </FormField>
    <div>
      <button type="submit" class="button button-danger" :disabled="isDeleting || !password">
        {{ isDeleting ? 'Deleting…' : 'Delete my account' }}
      </button>
    </div>
  </form>
</template>

<style scoped>
.danger-zone {
  padding: var(--space-5);
  border: 2px solid var(--red-card);
  border-radius: var(--radius);
  background: var(--surface);
}
</style>
