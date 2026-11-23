<script setup lang="ts">
import { reactive, ref } from 'vue';
import { RouterLink, useRoute, useRouter } from 'vue-router';

import { getFieldErrors, getFormMessage, type FieldErrors } from '@/api/client';
import { readRedirect } from '@/auth/redirect';
import { login } from '@/auth/session';
import FormField from '@/components/FormField.vue';

const route = useRoute();
const router = useRouter();
const credentials = reactive({ username: '', password: '' });
const fieldErrors = ref<FieldErrors>({});
const formMessage = ref<string>();
const isSubmitting = ref(false);

async function handleSubmit(): Promise<void> {
  isSubmitting.value = true;
  fieldErrors.value = {};
  formMessage.value = undefined;
  try {
    await login(credentials.username, credentials.password);
    await router.push(readRedirect(route.query.redirect));
  } catch (error: unknown) {
    fieldErrors.value = getFieldErrors(error);
    formMessage.value = getFormMessage(error);
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <section class="stack">
    <h1>Log in</h1>
    <p class="lede">Log in to play quizzes, keep your results and write your own questions.</p>
    <form class="form" novalidate @submit.prevent="handleSubmit">
      <p v-if="formMessage" class="form-alert" role="alert">{{ formMessage }}</p>
      <FormField id="login-username" label="Username" :errors="fieldErrors.username">
        <input id="login-username" v-model.trim="credentials.username" autocomplete="username" required />
      </FormField>
      <FormField id="login-password" label="Password" :errors="fieldErrors.password">
        <input
          id="login-password"
          v-model="credentials.password"
          type="password"
          autocomplete="current-password"
          required
        />
      </FormField>
      <div>
        <button type="submit" class="button" :disabled="isSubmitting">
          {{ isSubmitting ? 'Logging in…' : 'Log in' }}
        </button>
      </div>
      <p>No account yet? <RouterLink :to="{ name: 'signup', query: route.query }">Sign up</RouterLink></p>
    </form>
  </section>
</template>
