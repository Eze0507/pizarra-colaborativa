import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../auth/services/auth.service';

@Component({
  selector: 'app-whiteboard-page',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="whiteboard-screen">
      <h1 class="welcome-title">Bienvenido a la pizarra colaborativa</h1>
      <button type="button" class="btn-logout" (click)="onLogout()" [disabled]="isLoggingOut">
        {{ isLoggingOut ? 'Cerrando sesión...' : 'Cerrar sesión' }}
      </button>
    </div>
  `,
  styles: [`
    .whiteboard-screen {
      min-height: 100vh;
      width: 100%;
      background-color: #ffffff;
      color: #111111;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 24px;
      padding: 24px;
      box-sizing: border-box;
      font-family: inherit;
    }

    .welcome-title {
      font-size: 28px;
      font-weight: 600;
      color: #111111;
      margin: 0;
      text-align: center;
    }

    .btn-logout {
      padding: 10px 24px;
      font-size: 15px;
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
export class WhiteboardPage {
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
