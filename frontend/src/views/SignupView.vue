<script setup lang="ts">
import { reactive, ref } from 'vue';
import { RouterLink, useRoute, useRouter } from 'vue-router';

import { getFieldErrors, getFormMessage, type FieldErrors } from '@/api/client';
import { readRedirect } from '@/auth/redirect';
import { signup } from '@/auth/session';
import FormField from '@/components/FormField.vue';

const route = useRoute();
const router = useRouter();
const account = reactive({ username: '', password: '', favorite_club: '', country: '' });
const fieldErrors = ref<FieldErrors>({});
const formMessage = ref<string>();
const isSubmitting = ref(false);

async function handleSubmit(): Promise<void> {
  isSubmitting.value = true;
  fieldErrors.value = {};
  formMessage.value = undefined;
  try {
    await signup({ ...account });
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
    <h1>Sign up</h1>
    <p class="lede">Make an account to save your scores and get on the leaderboard.</p>
    <form class="form" novalidate @submit.prevent="handleSubmit">
      <p v-if="formMessage" class="form-alert" role="alert">{{ formMessage }}</p>
      <FormField id="signup-username" label="Username" :errors="fieldErrors.username">
        <input id="signup-username" v-model.trim="account.username" autocomplete="username" required />
      </FormField>
      <FormField
        id="signup-password"
        label="Password"
        hint="At least 8 characters, not only numbers, not too close to your username."
        :errors="fieldErrors.password"
      >
        <input
          id="signup-password"
          v-model="account.password"
          type="password"
          autocomplete="new-password"
          aria-describedby="signup-password-hint"
          required
        />
      </FormField>
      <FormField id="signup-club" label="Favourite club (optional)" :errors="fieldErrors.favorite_club">
        <input id="signup-club" v-model.trim="account.favorite_club" />
      </FormField>
      <FormField id="signup-country" label="Country (optional)" :errors="fieldErrors.country">
        <input id="signup-country" v-model.trim="account.country" autocomplete="country-name" />
      </FormField>
      <div>
        <button type="submit" class="button" :disabled="isSubmitting">
          {{ isSubmitting ? 'Creating account…' : 'Create account' }}
        </button>
      </div>
      <p>Already have an account? <RouterLink :to="{ name: 'login', query: route.query }">Log in</RouterLink></p>
    </form>
  </section>
</template>
