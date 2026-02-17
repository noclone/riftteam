import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
    },
    {
      path: '/create',
      name: 'create',
      component: () => import('@/views/CreateProfileView.vue'),
    },
    {
      path: '/p/:slug',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
    },
    {
      path: '/browse',
      name: 'browse',
      component: () => import('@/views/BrowseView.vue'),
    },
  ],
})

export default router
