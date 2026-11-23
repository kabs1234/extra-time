import {
  createRouter,
  createWebHistory,
  type RouteLocationNormalized,
  type RouteLocationRaw,
} from 'vue-router';

import { initSession, isLoggedIn } from '@/auth/session';
import HomeView from '@/views/HomeView.vue';
import LeaderboardView from '@/views/LeaderboardView.vue';
import LoginView from '@/views/LoginView.vue';
import MyQuestionFormView from '@/views/MyQuestionFormView.vue';
import MyQuestionListView from '@/views/MyQuestionListView.vue';
import NotFoundView from '@/views/NotFoundView.vue';
import PlayView from '@/views/PlayView.vue';
import ProfileView from '@/views/ProfileView.vue';
import QuestionListView from '@/views/QuestionListView.vue';
import QuestionView from '@/views/QuestionView.vue';
import ResultListView from '@/views/ResultListView.vue';
import ResultView from '@/views/ResultView.vue';
import SignupView from '@/views/SignupView.vue';

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean;
    guestOnly?: boolean;
  }
}

export const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/questions', name: 'questions', component: QuestionListView },
    { path: '/questions/:id(\\d+)', name: 'question', component: QuestionView, props: readIdParam },
    { path: '/leaderboard', name: 'leaderboard', component: LeaderboardView },
    { path: '/login', name: 'login', component: LoginView, meta: { guestOnly: true } },
    { path: '/signup', name: 'signup', component: SignupView, meta: { guestOnly: true } },
    { path: '/play', name: 'play', component: PlayView, meta: { requiresAuth: true } },
    { path: '/results', name: 'results', component: ResultListView, meta: { requiresAuth: true } },
    {
      path: '/results/:id(\\d+)',
      name: 'result',
      component: ResultView,
      props: readIdParam,
      meta: { requiresAuth: true },
    },
    {
      path: '/my-questions',
      name: 'my-questions',
      component: MyQuestionListView,
      meta: { requiresAuth: true },
    },
    {
      path: '/my-questions/new',
      name: 'my-question-new',
      component: MyQuestionFormView,
      meta: { requiresAuth: true },
    },
    {
      path: '/my-questions/:id(\\d+)/edit',
      name: 'my-question-edit',
      component: MyQuestionFormView,
      props: readIdParam,
      meta: { requiresAuth: true },
    },
    { path: '/profile', name: 'profile', component: ProfileView, meta: { requiresAuth: true } },
    { path: '/:path(.*)*', name: 'not-found', component: NotFoundView },
  ],
});

router.beforeEach(async (to): Promise<RouteLocationRaw | true> => {
  await initSession();
  if (to.meta.requiresAuth && !isLoggedIn()) {
    return { name: 'login', query: { redirect: to.fullPath } };
  }
  if (to.meta.guestOnly && isLoggedIn()) {
    return { name: 'home' };
  }
  return true;
});

function readIdParam(route: RouteLocationNormalized): { id: number } {
  return { id: Number(route.params.id) };
}
