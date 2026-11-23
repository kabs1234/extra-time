<script setup lang="ts">
import { RouterLink } from 'vue-router';
</script>

<template>
  <section class="stack">
    <h1>Offside</h1>
    <p class="lede">There's no page at this address.</p>
    <p><RouterLink to="/">Go to the home page</RouterLink> or <RouterLink to="/questions">browse the questions</RouterLink>.</p>
  </section>
</template>
