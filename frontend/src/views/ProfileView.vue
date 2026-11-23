<script setup lang="ts">
import { session } from '@/auth/session';
</script>

<template>
  <section class="stack">
    <h1>{{ session.user?.username }}</h1>
    <p class="lede">Your profile.</p>
  </section>
</template>
