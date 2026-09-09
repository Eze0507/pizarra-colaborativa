import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { LoginFormComponent } from '../../components/login-form/login-form.component';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [CommonModule, LoginFormComponent],
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.css']
})
export class LoginPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  public successMessage: string | null = null;

  public ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      if (params['verifique_correo'] === 'true') {
        this.successMessage = '¡Registro exitoso! Te hemos enviado un enlace a tu correo para activar tu cuenta. Por favor revísalo antes de iniciar sesión.';
      } else if (params['registrado'] === 'true' || params['registered'] === 'true') {
        this.successMessage = '¡Registro exitoso! Ya puedes iniciar sesión con tu cuenta.';
      } else {
        this.successMessage = null;
      }
    });
  }
}
