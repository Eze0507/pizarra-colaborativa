import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface ToastMensaje {
  id: number;
  mensaje: string;
  tipo: 'exito' | 'error' | 'info';
  duracionMs: number;
}

@Injectable({
  providedIn: 'root'
})
export class ToastNotificationService {
  private contador = 0;
  private readonly toastsSubject = new BehaviorSubject<ToastMensaje[]>([]);
  public readonly toasts$: Observable<ToastMensaje[]> = this.toastsSubject.asObservable();

  public exito(mensaje: string, duracionMs = 3500): void {
    this.agregar(mensaje, 'exito', duracionMs);
  }

  public error(mensaje: string, duracionMs = 4500): void {
    this.agregar(mensaje, 'error', duracionMs);
  }

  public info(mensaje: string, duracionMs = 3500): void {
    this.agregar(mensaje, 'info', duracionMs);
  }

  public remover(id: number): void {
    const actuales = this.toastsSubject.value;
    this.toastsSubject.next(actuales.filter(t => t.id !== id));
  }

  private agregar(mensaje: string, tipo: 'exito' | 'error' | 'info', duracionMs: number): void {
    const id = ++this.contador;
    const nuevo: ToastMensaje = { id, mensaje, tipo, duracionMs };
    const actuales = this.toastsSubject.value;
    this.toastsSubject.next([...actuales, nuevo]);

    if (duracionMs > 0) {
      setTimeout(() => {
        this.remover(id);
      }, duracionMs);
    }
  }
}
