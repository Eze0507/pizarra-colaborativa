import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-auth-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  template: `
    <div class="auth-layout-container">
      <router-outlet></router-outlet>
    </div>
  `,
  styles: [`
    .auth-layout-container {
      min-height: 100vh;
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #111111;
      padding: 16px;
      box-sizing: border-box;
    }
  `]
})
export class AuthLayoutComponent {}
