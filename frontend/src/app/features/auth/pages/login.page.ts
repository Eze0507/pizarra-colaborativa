import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { LoginFormComponent } from '../components/login-form/login-form.component';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [CommonModule, LoginFormComponent],
  template: `
    <main class="page-container">
      <app-login-form [successMessage]="successMessage"></app-login-form>
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
  `]
})
export class LoginPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  public successMessage: string | null = null;

  public ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      if (params['registrado'] === 'true' || params['registered'] === 'true') {
        this.successMessage = '¡Registro exitoso! Ya puedes iniciar sesión con tu cuenta.';
      } else {
        this.successMessage = null;
      }
    });
  }
}
