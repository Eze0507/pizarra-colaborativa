import { Component, Input, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthService } from '../../services/auth.service';
import { ActivateResponse } from '../../interfaces/activate.interface';

@Component({
  selector: 'app-activate-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './activate-card.component.html',
  styleUrls: ['./activate-card.component.css']
})
export class ActivateCardComponent implements OnInit {
  @Input() public token: string | null = null;

  private readonly router = inject(Router);
  private readonly authService = inject(AuthService);

  public isLoading = true;
  public isSuccess = false;
  public successMessage = '';
  public errorMessage = '';

  public ngOnInit(): void {
    if (!this.token) {
      this.isLoading = false;
      this.isSuccess = false;
      this.errorMessage = 'No se proporcionó ningún token de activación.';
      return;
    }

    this.authService.activateAccount(this.token).subscribe({
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
