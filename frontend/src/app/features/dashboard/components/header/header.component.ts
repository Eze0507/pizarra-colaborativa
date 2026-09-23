import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { TokenStorageService } from '../../../../core/services/token-storage.service';
import { ToastNotificationService } from '../../../../core/services/toast-notification.service';
import { User } from '../../../auth/interfaces/user.interface';
import { InvitacionesService } from '../../services/invitaciones.service';
import { InvitacionPendiente, RespuestaAceptarInvitacion } from '../../interfaces/invitacion.interface';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class HeaderComponent implements OnInit {
  private readonly tokenStorage = inject(TokenStorageService);
  private readonly invitacionesService = inject(InvitacionesService);
  private readonly toastService = inject(ToastNotificationService);

  public currentUser: User | null = null;
  public isPopoverOpen = false;
  public procesandoId: number | null = null;

  public readonly invitaciones$: Observable<InvitacionPendiente[]> = this.invitacionesService.invitaciones$;
  public readonly conteo$: Observable<number> = this.invitacionesService.conteoPendientes$;

  public ngOnInit(): void {
    this.currentUser = this.tokenStorage.getUser();
    this.cargarInvitaciones();
  }

  public cargarInvitaciones(): void {
    this.invitacionesService.cargarInvitaciones().subscribe({
      error: () => {
        // Manejo silencioso para no interrumpir el flujo del usuario
      }
    });
  }

  public toggleNotificaciones(): void {
    this.isPopoverOpen = !this.isPopoverOpen;
    if (this.isPopoverOpen) {
      this.cargarInvitaciones();
    }
  }

  public cerrarNotificaciones(): void {
    this.isPopoverOpen = false;
  }

  public aceptar(invitacion: InvitacionPendiente): void {
    if (this.procesandoId !== null) return;
    this.procesandoId = invitacion.id;

    this.invitacionesService.aceptarInvitacion(invitacion.id).subscribe({
      next: (resp: RespuestaAceptarInvitacion) => {
        this.procesandoId = null;
        this.toastService.exito(
          `¡Invitación aceptada! Ya puedes colaborar en "${resp.proyecto.nombre}".`
        );
      },
      error: (err: HttpErrorResponse) => {
        this.procesandoId = null;
        const msg = (err.error && typeof err.error.detail === 'string')
          ? err.error.detail
          : 'No se pudo aceptar la invitación.';
        this.toastService.error(msg);
      }
    });
  }

  public rechazar(invitacion: InvitacionPendiente): void {
    if (this.procesandoId !== null) return;
    this.procesandoId = invitacion.id;

    this.invitacionesService.rechazarInvitacion(invitacion.id).subscribe({
      next: () => {
        this.procesandoId = null;
        this.toastService.info(
          `Has rechazado la invitación al proyecto "${invitacion.proyecto.nombre}".`
        );
      },
      error: (err: HttpErrorResponse) => {
        this.procesandoId = null;
        const msg = (err.error && typeof err.error.detail === 'string')
          ? err.error.detail
          : 'No se pudo rechazar la invitación.';
        this.toastService.error(msg);
      }
    });
  }
}
