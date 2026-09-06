import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthService } from '../../services/auth.service';
import { RegisterRequest } from '../../interfaces/register-request.interface';

@Component({
  selector: 'app-register-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './register-form.component.html',
  styleUrl: './register-form.component.css'
})
export class RegisterFormComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  public readonly registerForm: FormGroup = this.fb.group({
    first_name: ['', [Validators.required]],
    last_name: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    username: ['', [Validators.required]],
    password: ['', [Validators.required, Validators.minLength(8)]]
  });

  public errorMessage: string | null = null;
  public isLoading = false;

  public onSubmit(): void {
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }

    this.errorMessage = null;
    this.isLoading = true;

    const data: RegisterRequest = {
      first_name: this.registerForm.value.first_name.trim(),
      last_name: this.registerForm.value.last_name.trim(),
      email: this.registerForm.value.email.trim(),
      username: this.registerForm.value.username.trim(),
      password: this.registerForm.value.password
    };

    this.authService.register(data).subscribe({
      next: () => {
        this.isLoading = false;
        // Redirige al login con el mensaje de registro exitoso
        this.router.navigate(['/login'], { queryParams: { registrado: 'true' } });
      },
      error: (error: HttpErrorResponse) => {
        this.isLoading = false;
        if (error.error && typeof error.error === 'object') {
          const errors = error.error as Record<string, string[] | string>;
          const messages: string[] = [];
          for (const key of Object.keys(errors)) {
            const val = errors[key];
            if (Array.isArray(val)) {
              messages.push(...val);
            } else if (typeof val === 'string') {
              messages.push(val);
            }
          }
          this.errorMessage = messages.length > 0 ? messages.join(' ') : 'Error al registrar el usuario.';
        } else {
          this.errorMessage = 'No se pudo conectar con el servidor. Intente más tarde.';
        }
      }
    });
  }

  public onCancel(): void {
    // Redirige al login sin ningún mensaje
    this.router.navigate(['/login']);
  }
}
