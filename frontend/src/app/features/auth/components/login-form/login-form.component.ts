import { Component, Input, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthService } from '../../services/auth.service';
import { LoginRequest } from '../../interfaces/login-request.interface';

import { CustomButtonComponent } from '../../../../shared/components/custom-button/custom-button.component';

@Component({
  selector: 'app-login-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, CustomButtonComponent],
  templateUrl: './login-form.component.html',
  styleUrl: './login-form.component.css'
})
export class LoginFormComponent {
  @Input() public successMessage: string | null = null;

  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  public readonly loginForm: FormGroup = this.fb.group({
    username: ['', [Validators.required]],
    password: ['', [Validators.required]]
  });

  public errorMessage: string | null = null;
  public isLoading = false;

  public onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.errorMessage = null;
    this.isLoading = true;

    const credentials: LoginRequest = {
      username: this.loginForm.value.username.trim(),
      password: this.loginForm.value.password
    };

    this.authService.login(credentials).subscribe({
      next: () => {
        this.isLoading = false;
        this.router.navigate(['/control']);
      },
      error: (error: HttpErrorResponse) => {
        this.isLoading = false;
        const detail = error.error?.detail;
        if (error.status === 401) {
          this.errorMessage = 'Credenciales incorrectas. Verifique su usuario y contraseña.';
        } else if (typeof detail === 'string') {
          this.errorMessage = detail;
        } else if (Array.isArray(detail)) {
          this.errorMessage = detail.filter((message): message is string => typeof message === 'string').join(' ')
            || 'No se pudo iniciar sesión. Revise los datos.';
        } else if (error.status === 0) {
          this.errorMessage = 'Error al conectar con el servidor. Intente más tarde.';
        } else {
          this.errorMessage = 'No se pudo iniciar sesión. Revise los datos.';
        }
      }
    });
  }

  public goToRegister(): void {
    this.router.navigate(['/registro']);
  }
}
