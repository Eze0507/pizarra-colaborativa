import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { AuthService } from '../../features/auth/services/auth.service';

@Component({
  selector: 'app-pizarra-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  template: `
    <div class="pizarra-layout-container">
      <h1 class="blank-title">pizarra</h1>
      <button type="button" class="btn-logout" (click)="onLogout()" [disabled]="isLoggingOut">
        {{ isLoggingOut ? 'Cerrando sesión...' : 'Cerrar sesión' }}
      </button>
      <router-outlet></router-outlet>
    </div>
  `,
  styles: [`
    .pizarra-layout-container {
      min-height: 100vh;
      width: 100%;
      background-color: #ffffff;
      color: #111111;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 20px;
      padding: 24px;
      box-sizing: border-box;
      font-family: inherit;
    }

    .blank-title {
      font-size: 28px;
      font-weight: 600;
      color: #111111;
      margin: 0;
      text-transform: lowercase;
    }

    .btn-logout {
      padding: 8px 20px;
      font-size: 14px;
      font-weight: 500;
      color: #ffffff;
      background-color: #111111;
      border: 1px solid #111111;
      border-radius: 6px;
      cursor: pointer;
      transition: background-color 0.2s, opacity 0.2s;
    }

    .btn-logout:hover:not(:disabled) {
      background-color: #333333;
    }

    .btn-logout:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  `]
})
export class PizarraLayoutComponent {
  private readonly authService = inject(AuthService);
  public isLoggingOut = false;

  public onLogout(): void {
    this.isLoggingOut = true;
    this.authService.logout().subscribe({
      next: () => {
        this.isLoggingOut = false;
      },
      error: () => {
        this.isLoggingOut = false;
      }
    });
  }
}
