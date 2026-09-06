import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./features/auth/pages/login.page').then(m => m.LoginPage)
  },
  {
    path: 'registro',
    loadComponent: () => import('./features/auth/pages/register.page').then(m => m.RegisterPage)
  },
  {
    path: 'pizarra',
    canActivate: [authGuard],
    loadComponent: () => import('./features/whiteboard/pages/whiteboard.page').then(m => m.WhiteboardPage)
  },
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'login'
  },
  {
    path: '**',
    redirectTo: 'login'
  }
];
