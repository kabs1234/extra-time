<script setup lang="ts">
import { reactive, ref } from 'vue';

import { getFieldErrors, getFormMessage, type FieldErrors } from '@/api/client';
import { updateMe } from '@/api/resources';
import type { Me } from '@/api/types';
import FormField from '@/components/FormField.vue';

const props = defineProps<{ me: Me }>();
const emit = defineEmits<{ saved: [me: Me] }>();

const draft = reactive({
  username: props.me.username,
  favorite_club: props.me.profile.favorite_club,
  country: props.me.profile.country,
  bio: props.me.profile.bio,
});
const fieldErrors = ref<FieldErrors>({});
const formMessage = ref<string>();
const isSaved = ref(false);
const isSaving = ref(false);

async function handleSubmit(): Promise<void> {
  isSaving.value = true;
  isSaved.value = false;
  fieldErrors.value = {};
  formMessage.value = undefined;
  try {
    const me = await updateMe({
      username: draft.username,
      profile: { favorite_club: draft.favorite_club, country: draft.country, bio: draft.bio },
    });
    isSaved.value = true;
    emit('saved', me);
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
    <h2>Your details</h2>
    <p v-if="formMessage" class="form-alert" role="alert">{{ formMessage }}</p>
    <p v-if="fieldErrors.profile" class="form-alert" role="alert">{{ fieldErrors.profile.join(' ') }}</p>
    <p v-if="isSaved" class="form-success" role="status">Details saved.</p>
    <FormField id="profile-username" label="Username" :errors="fieldErrors.username">
      <input id="profile-username" v-model.trim="draft.username" autocomplete="username" required />
    </FormField>
    <FormField id="profile-club" label="Favourite club">
      <input id="profile-club" v-model.trim="draft.favorite_club" maxlength="100" />
    </FormField>
    <FormField id="profile-country" label="Country">
      <input id="profile-country" v-model.trim="draft.country" maxlength="100" autocomplete="country-name" />
    </FormField>
    <FormField id="profile-bio" label="About you">
      <textarea id="profile-bio" v-model.trim="draft.bio" rows="3" />
    </FormField>
    <div>
      <button type="submit" class="button" :disabled="isSaving">{{ isSaving ? 'Saving…' : 'Save details' }}</button>
    </div>
  </form>
</template>
