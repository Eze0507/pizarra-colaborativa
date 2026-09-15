import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

/**
 * PizarraLayoutComponent — cascarón inmersivo de pantalla completa.
 *
 * Según SKILL.md ("La Regla de los Layouts"):
 *  - Cero peticiones HTTP
 *  - Cero lógica de negocio
 *  - Solo define la estructura macro y expone <router-outlet>
 *
 * Toda la lógica de sidebar, WebSocket y JointJS vive en WhiteboardPage.
 */
@Component({
  selector: 'app-pizarra-layout',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <div class="pizarra-shell">
      <router-outlet></router-outlet>
    </div>
  `,
  styles: [`
    :host {
      display: flex;
      flex: 1;
      width: 100%;
      min-height: 0;
      overflow: hidden;
    }

    .pizarra-shell {
      display: flex;
      flex: 1;
      width: 100%;
      min-height: 0;
      background-color: #111111;
      overflow: hidden;
    }
  `]
})
export class PizarraLayoutComponent {}

