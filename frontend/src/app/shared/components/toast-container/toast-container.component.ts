import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToastNotificationService, ToastMensaje } from '../../../core/services/toast-notification.service';

@Component({
  selector: 'app-toast-container',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './toast-container.component.html',
  styleUrls: ['./toast-container.component.css']
})
export class ToastContainerComponent {
  public readonly toastService = inject(ToastNotificationService);
  public readonly toasts$ = this.toastService.toasts$;

  public cerrar(id: number): void {
    this.toastService.remover(id);
  }

  public trackByToastId(_index: number, toast: ToastMensaje): number {
    return toast.id;
  }
}
