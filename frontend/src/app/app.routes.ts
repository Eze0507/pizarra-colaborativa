import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { AuthLayoutComponent } from './layouts/auth-layout/auth-layout.component';
import { DashboardLayoutComponent } from './layouts/dashboard-layout/dashboard-layout.component';
import { PizarraLayoutComponent } from './layouts/pizarra-layout/pizarra-layout.component';

export const routes: Routes = [
  // 1. Layout de Autenticación
  {
    path: '',
    component: AuthLayoutComponent,
    children: [
      {
        path: 'login',
        loadComponent: () => import('./features/auth/pages/login/login.page').then(m => m.LoginPage)
      },
      {
        path: 'registro',
        loadComponent: () => import('./features/auth/pages/register/register.page').then(m => m.RegisterPage)
      },
      {
        path: 'activar/:token',
        loadComponent: () => import('./features/auth/pages/activate/activate.page').then(m => m.ActivatePage)
      },
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'login'
      }
    ]
  },
  // 2. Layout del Panel de Control / Dashboard
  {
    path: 'control',
    component: DashboardLayoutComponent,
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () => import('./features/dashboard/pages/projects-list/projects-list.page').then(m => m.ProjectsListPage)
      }
    ]
  },
  {
    path: 'panel',
    redirectTo: 'control',
    pathMatch: 'full'
  },
  // 3. Layout de la Pizarra
  {
    path: 'pizarra',
    component: PizarraLayoutComponent,
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () => import('./features/whiteboard/pages/whiteboard.page').then(m => m.WhiteboardPage)
      }
    ]
  },
  // Redirección comodín
  {
    path: '**',
    redirectTo: 'login'
  }
];
