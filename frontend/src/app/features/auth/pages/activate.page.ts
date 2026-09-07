import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthService } from '../services/auth.service';
import { ActivateResponse } from '../interfaces/activate.interface';

@Component({
  selector: 'app-activate-page',
  standalone: true,
  imports: [CommonModule],
  template: `
    <main class="page-container">
      <div class="activate-card">
        <div class="activate-header">
          <img src="/NodoBoardOficial.png" alt="NodoBoard Logo" class="activate-logo" />
          <h1 class="activate-title">Activación de Cuenta</h1>
          <p class="activate-subtitle">Herramienta CASE de Diseño de Datos</p>
        </div>

        <!-- Estado: Cargando -->
        <div *ngIf="isLoading" class="state-container">
          <div class="spinner"></div>
          <p class="state-text">Validando enlace de activación...</p>
        </div>

        <!-- Estado: Éxito -->
        <div *ngIf="!isLoading && isSuccess" class="state-container">
          <div class="alert alert-success">
            {{ successMessage }}
          </div>
          <button type="button" class="btn btn-primary" (click)="goToLogin()">
            Iniciar sesión
          </button>
        </div>

        <!-- Estado: Error -->
        <div *ngIf="!isLoading && !isSuccess" class="state-container">
          <div class="alert alert-error">
            {{ errorMessage }}
          </div>
          <button type="button" class="btn btn-secondary" (click)="goToLogin()">
            Ir al inicio de sesión
          </button>
        </div>
      </div>
    </main>
  `,
  styles: [`
    .page-container {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #111111;
      padding: 16px;
      box-sizing: border-box;
    }

    .activate-card {
      width: 100%;
      max-width: 440px;
      background-color: #1a1a1a;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      padding: 32px;
      box-sizing: border-box;
      text-align: center;
    }

    .activate-header {
      margin-bottom: 24px;
    }

    .activate-logo {
      height: 48px;
      width: auto;
      object-fit: contain;
      margin: 0 auto 16px auto;
      display: block;
    }

    .activate-title {
      margin: 0 0 8px 0;
      font-size: 22px;
      font-weight: 600;
      color: #ededed;
    }

    .activate-subtitle {
      margin: 0;
      font-size: 13px;
      color: #888888;
    }

    .state-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
    }

    .spinner {
      width: 32px;
      height: 32px;
      border: 3px solid rgba(255, 255, 255, 0.1);
      border-top-color: #2563eb;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .state-text {
      color: #888888;
      font-size: 14px;
      margin: 0;
    }

    .alert {
      padding: 12px 14px;
      border-radius: 6px;
      font-size: 13px;
      line-height: 1.4;
      width: 100%;
      box-sizing: border-box;
      text-align: left;
    }

    .alert-success {
      background-color: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #34d399;
    }

    .alert-error {
      background-color: rgba(239, 68, 68, 0.1);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: #f87171;
    }

    .btn {
      padding: 10px 16px;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: background-color 0.2s, border-color 0.2s;
      text-align: center;
      box-sizing: border-box;
      width: 100%;
    }

    .btn-primary {
      background-color: #2563eb;
      border: 1px solid #2563eb;
      color: #ffffff;
    }

    .btn-primary:hover {
      background-color: #1d4ed8;
      border-color: #1d4ed8;
    }

    .btn-secondary {
      background-color: transparent;
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #ededed;
    }

    .btn-secondary:hover {
      background-color: rgba(255, 255, 255, 0.05);
      border-color: rgba(255, 255, 255, 0.25);
    }
  `]
})
export class ActivatePage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly authService = inject(AuthService);

  public isLoading = true;
  public isSuccess = false;
  public successMessage = '';
  public errorMessage = '';

  public ngOnInit(): void {
    const token = this.route.snapshot.paramMap.get('token');

    if (!token) {
      this.isLoading = false;
      this.isSuccess = false;
      this.errorMessage = 'No se proporcionó ningún token de activación.';
      return;
    }

    this.authService.activateAccount(token).subscribe({
      next: (response: ActivateResponse) => {
        this.isLoading = false;
        this.isSuccess = true;
        this.successMessage = response.detail || '¡Tu cuenta ha sido activada con éxito! Ya puedes iniciar sesión.';
      },
      error: (error: HttpErrorResponse) => {
        this.isLoading = false;
        this.isSuccess = false;
        if (error.error && typeof error.error.detail === 'string') {
          this.errorMessage = error.error.detail;
        } else {
          this.errorMessage = 'El enlace de activación es inválido o ha expirado.';
        }
      }
    });
  }

  public goToLogin(): void {
    this.router.navigate(['/login']);
  }
}
