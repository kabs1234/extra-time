import {
  createRouter,
  createWebHistory,
  type RouteLocationNormalized,
  type RouteLocationRaw,
} from 'vue-router';

import { initSession, isLoggedIn, session } from '@/auth/session';
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

const SITE_NAME = 'Extra Time';

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean;
    guestOnly?: boolean;
    title?: string;
  }
}

export const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/questions', name: 'questions', component: QuestionListView, meta: { title: 'Question bank' } },
    {
      path: '/questions/:id(\\d+)',
      name: 'question',
      component: QuestionView,
      props: readIdParam,
      meta: { title: 'Question' },
    },
    { path: '/leaderboard', name: 'leaderboard', component: LeaderboardView, meta: { title: 'Leaderboard' } },
    { path: '/login', name: 'login', component: LoginView, meta: { guestOnly: true, title: 'Log in' } },
    { path: '/signup', name: 'signup', component: SignupView, meta: { guestOnly: true, title: 'Sign up' } },
    { path: '/play', name: 'play', component: PlayView, meta: { requiresAuth: true, title: 'Play' } },
    { path: '/results', name: 'results', component: ResultListView, meta: { requiresAuth: true, title: 'My results' } },
    {
      path: '/results/:id(\\d+)',
      name: 'result',
      component: ResultView,
      props: readIdParam,
      meta: { requiresAuth: true, title: 'Round result' },
    },
    {
      path: '/my-questions',
      name: 'my-questions',
      component: MyQuestionListView,
      meta: { requiresAuth: true, title: 'My questions' },
    },
    {
      path: '/my-questions/new',
      name: 'my-question-new',
      component: MyQuestionFormView,
      meta: { requiresAuth: true, title: 'Write a question' },
    },
    {
      path: '/my-questions/:id(\\d+)/edit',
      name: 'my-question-edit',
      component: MyQuestionFormView,
      props: readIdParam,
      meta: { requiresAuth: true, title: 'Edit your question' },
    },
    { path: '/profile', name: 'profile', component: ProfileView, meta: { requiresAuth: true, title: 'Profile' } },
    { path: '/:path(.*)*', name: 'not-found', component: NotFoundView, meta: { title: 'Page not found' } },
  ],
});

router.beforeEach(async (to): Promise<RouteLocationRaw | true> => {
  await initSession();
  // When the session couldn't be checked (server down), App shows a retry instead of the page.
  if (to.meta.requiresAuth && !isLoggedIn() && !session.restoreError) {
    return { name: 'login', query: { redirect: to.fullPath } };
  }
  if (to.meta.guestOnly && isLoggedIn()) {
    return { name: 'home' };
  }
  return true;
});

router.afterEach((to, _from, failure) => {
  // afterEach also runs for cancelled navigations (e.g. "Leave this round?" → Cancel): keep the old title.
  if (failure) {
    return;
  }
  document.title = to.meta.title ? `${to.meta.title} · ${SITE_NAME}` : SITE_NAME;
});

function readIdParam(route: RouteLocationNormalized): { id: number } {
  return { id: Number(route.params.id) };
}
