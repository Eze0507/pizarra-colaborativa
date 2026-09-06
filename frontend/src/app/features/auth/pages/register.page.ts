import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RegisterFormComponent } from '../components/register-form/register-form.component';

@Component({
  selector: 'app-register-page',
  standalone: true,
  imports: [CommonModule, RegisterFormComponent],
  template: `
    <main class="page-container">
      <app-register-form></app-register-form>
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
export class RegisterPage {}
