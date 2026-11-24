import '@fontsource/barlow-condensed/600.css';
import '@fontsource/barlow-condensed/700.css';
import '@fontsource-variable/public-sans/index.css';
import './styles.css';

import { createApp } from 'vue';

import { configureAuth } from '@/api/client';
import { clearSession, getAccessToken, refreshAccessToken } from '@/auth/session';

import App from './App.vue';
import { router } from './router';

configureAuth({
  getAccessToken,
  refreshAccessToken,
  onAuthLost: () => {
    clearSession();
    const { meta, fullPath } = router.currentRoute.value;
    if (meta.requiresAuth) {
      void router.push({ name: 'login', query: { redirect: fullPath } });
    }
  },
});

createApp(App).use(router).mount('#app');
