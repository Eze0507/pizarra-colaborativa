import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface RespuestaAyuda {
  explicacion: string;
  pasos: string[];
  componente_id: string | null;
  requiere_cambio_vista: boolean;
  vista_destino: string | null;
}

export interface MensajeAyudaChat {
  id: string;
  remitente: 'usuario' | 'asistente';
  texto?: string;
  respuesta?: RespuestaAyuda;
  fecha: Date;
  cargando?: boolean;
  error?: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class AyudaService {
  private readonly http = inject(HttpClient);

  private readonly _panelVisible$ = new BehaviorSubject<boolean>(false);
  public readonly panelVisible$: Observable<boolean> = this._panelVisible$.asObservable();

  private readonly _minimizado$ = new BehaviorSubject<boolean>(false);
  public readonly minimizado$: Observable<boolean> = this._minimizado$.asObservable();

  private readonly _mensajes$ = new BehaviorSubject<MensajeAyudaChat[]>([]);
  public readonly mensajes$: Observable<MensajeAyudaChat[]> = this._mensajes$.asObservable();

  private readonly _cargando$ = new BehaviorSubject<boolean>(false);
  public readonly cargando$: Observable<boolean> = this._cargando$.asObservable();

  private elementoResaltadoActual: Element | null = null;
  private timerResaltado: ReturnType<typeof setTimeout> | null = null;
  private clickHandlerResaltado: (() => void) | null = null;
  private contextMenuHandlerResaltado: (() => void) | null = null;

  public get isVisible(): boolean {
    return this._panelVisible$.value;
  }

  public get isMinimizado(): boolean {
    return this._minimizado$.value;
  }

  public togglePanel(): void {
    if (this._panelVisible$.value) {
      this.cerrarPanel();
    } else {
      this.abrirPanel();
    }
  }

  public abrirPanel(): void {
    this._panelVisible$.next(true);
    this._minimizado$.next(false);
  }

  public cerrarPanel(): void {
    this._panelVisible$.next(false);
    this.limpiarResaltado();
  }

  public toggleMinimizar(): void {
    this._minimizado$.next(!this._minimizado$.value);
  }

  public limpiarHistorial(): void {
    this._mensajes$.next([]);
    this.limpiarResaltado();
  }

  public consultar(textoConsulta: string, interfaz = 'dashboard'): void {
    const consulta = textoConsulta.trim();
    if (!consulta) return;

    const idUsuario = 'usr_' + Date.now();
    const idAsistente = 'ast_' + (Date.now() + 1);

    const mensajeUsuario: MensajeAyudaChat = {
      id: idUsuario,
      remitente: 'usuario',
      texto: consulta,
      fecha: new Date()
    };

    const mensajeAsistenteCargando: MensajeAyudaChat = {
      id: idAsistente,
      remitente: 'asistente',
      fecha: new Date(),
      cargando: true
    };

    const actuales = this._mensajes$.value;
    this._mensajes$.next([...actuales, mensajeUsuario, mensajeAsistenteCargando]);
    this._cargando$.next(true);

    const url = `${environment.apiUrl}/asistente/ayuda/`;
    this.http.post<RespuestaAyuda>(url, { consulta, interfaz }).subscribe({
      next: (resp: RespuestaAyuda) => {
        this._cargando$.next(false);
        const listaActualizada = this._mensajes$.value.map(msg => {
          if (msg.id === idAsistente) {
            return {
              ...msg,
              cargando: false,
              respuesta: resp
            };
          }
          return msg;
        });
        this._mensajes$.next(listaActualizada);

        // Paso 10: Resaltar componente visual si viene en la respuesta
        if (resp.componente_id) {
          this.resaltarComponente(resp.componente_id);
        }
      },
      error: (err: HttpErrorResponse) => {
        this._cargando$.next(false);
        const detalleError =
          err.error?.detail ||
          err.error?.error ||
          'El asistente de ayuda no se encuentra disponible temporalmente. Por favor intenta más tarde.';

        const listaActualizada = this._mensajes$.value.map(msg => {
          if (msg.id === idAsistente) {
            return {
              ...msg,
              cargando: false,
              error: detalleError
            };
          }
          return msg;
        });
        this._mensajes$.next(listaActualizada);
      }
    });
  }

  /**
   * CU-14 Paso 10 y 12: Aplica un resplandor azul al componente referenciado
   * y remueve el resaltado al hacer clic sobre él o por transcurso de tiempo (15s).
   * FE-02: Si el componente no está renderizado en el DOM, se omite de forma controlada.
   */
  public resaltarComponente(componenteId: string): void {
    this.limpiarResaltado();

    if (!componenteId) return;

    // Pequeño timeout para permitir que modales o elementos recién abiertos existan en el DOM
    setTimeout(() => {
      let elemento: Element | null = document.getElementById(componenteId);

      // Si el componenteId refiere a una entidad en el lienzo o a su opción de eliminación contextual
      // (o si no se encuentra directamente por ID), iluminar la primera entidad disponible en el lienzo
      if (!elemento) {
        if (
          componenteId === 'entidad-lienzo' ||
          componenteId === 'btn-eliminar-contextual' ||
          componenteId === 'primer-entidad-lienzo' ||
          componenteId.toLowerCase().includes('entidad')
        ) {
          elemento = document.querySelector(
            '.lienzo .joint-type-standard-headeredrectangle, .lienzo .joint-element, .figura-entidad-lienzo'
          );
        }
      }

      if (!elemento) {
        // FE-02: Componente referenciado no encontrado en la vista activa
        return;
      }

      this.elementoResaltadoActual = elemento;
      elemento.classList.add('cu14-highlight-pulse');

      // Asegurar que el elemento sea visible dentro de la ventana
      try {
        elemento.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
      } catch {
        // Ignorar si el navegador no soporta scrollIntoView options
      }

      // Paso 12: Si el usuario interactúa haciendo clic o clic derecho sobre el componente, retirar resaltado
      this.clickHandlerResaltado = () => {
        this.limpiarResaltado();
      };
      this.contextMenuHandlerResaltado = () => {
        this.limpiarResaltado();
      };
      elemento.addEventListener('click', this.clickHandlerResaltado, { once: true });
      elemento.addEventListener('contextmenu', this.contextMenuHandlerResaltado, { once: true });

      // O transcurrido el tiempo establecido (15 segundos)
      this.timerResaltado = setTimeout(() => {
        this.limpiarResaltado();
      }, 15000);
    }, 100);
  }

  public limpiarResaltado(): void {
    if (this.timerResaltado) {
      clearTimeout(this.timerResaltado);
      this.timerResaltado = null;
    }

    if (this.elementoResaltadoActual) {
      if (this.clickHandlerResaltado) {
        this.elementoResaltadoActual.removeEventListener('click', this.clickHandlerResaltado);
        this.clickHandlerResaltado = null;
      }
      if (this.contextMenuHandlerResaltado) {
        this.elementoResaltadoActual.removeEventListener('contextmenu', this.contextMenuHandlerResaltado);
        this.contextMenuHandlerResaltado = null;
      }
      this.elementoResaltadoActual.classList.remove('cu14-highlight-pulse');
      this.elementoResaltadoActual = null;
    }
  }
}

