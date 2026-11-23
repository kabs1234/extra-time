<script setup lang="ts">
import { reactive, ref } from 'vue';

import { getFieldErrors, getFormMessage, type FieldErrors } from '@/api/client';
import { changePassword } from '@/api/resources';
import { setAccessToken } from '@/auth/session';
import FormField from '@/components/FormField.vue';

const MISMATCH = 'The two new passwords are different.';

const draft = reactive({ oldPassword: '', newPassword: '', confirmation: '' });
const fieldErrors = ref<FieldErrors>({});
const formMessage = ref<string>();
const isChanged = ref(false);
const isSaving = ref(false);

function resetDraft(): void {
  draft.oldPassword = '';
  draft.newPassword = '';
  draft.confirmation = '';
}

async function handleSubmit(): Promise<void> {
  isChanged.value = false;
  fieldErrors.value = {};
  formMessage.value = undefined;
  if (draft.newPassword !== draft.confirmation) {
    fieldErrors.value = { confirmation: [MISMATCH] };
    return;
  }
  isSaving.value = true;
  try {
    const { access } = await changePassword(draft.oldPassword, draft.newPassword);
    setAccessToken(access);
    resetDraft();
    isChanged.value = true;
  } catch (error: unknown) {
    fieldErrors.value = getFieldErrors(error);
    formMessage.value = getFormMessage(error);
  } finally {
    isSaving.value = false;
  }
}
</script>

<template>
  <form class="form" novalidate @submit.prevent="handleSubmit">
    <h2>Change password</h2>
    <p v-if="formMessage" class="form-alert" role="alert">{{ formMessage }}</p>
    <p v-if="isChanged" class="form-success" role="status">
      Password changed. You stay logged in here; any other device has been logged out.
    </p>
    <FormField id="password-old" label="Current password" :errors="fieldErrors.old_password">
      <input
        id="password-old"
        v-model="draft.oldPassword"
        type="password"
        autocomplete="current-password"
        required
      />
    </FormField>
    <FormField id="password-new" label="New password" :errors="fieldErrors.new_password">
      <input id="password-new" v-model="draft.newPassword" type="password" autocomplete="new-password" required />
    </FormField>
    <FormField id="password-confirm" label="New password again" :errors="fieldErrors.confirmation">
      <input
        id="password-confirm"
        v-model="draft.confirmation"
        type="password"
        autocomplete="new-password"
        required
      />
    </FormField>
    <div>
      <button type="submit" class="button" :disabled="isSaving">
        {{ isSaving ? 'Changing…' : 'Change password' }}
      </button>
    </div>
  </form>
</template>
