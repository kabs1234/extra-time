<script setup lang="ts">
import { RouterLink } from 'vue-router';
</script>

<template>
  <section class="stack">
    <h1>Football history, from the first FA rules to the 48-team World Cup</h1>
    <p class="lede">Ten questions a round. Pick an era or a topic, answer, then read why each answer is right.</p>
    <div>
      <RouterLink to="/play" class="button">Start a quiz</RouterLink>
    </div>
  </section>
</template>
