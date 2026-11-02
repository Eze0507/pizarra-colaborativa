import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, Subject, Subscription } from 'rxjs';
import { tap, finalize } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { WhiteboardSocketService } from './whiteboard-socket.service';
import { TokenStorageService } from '../../../core/services/token-storage.service';
import {
  ContextoDiagramaIA,
  EnviarConsultaAgenteSeniorRespuesta,
  EstadoColaAgenteSenior,
  EventoWSAgenteSenior,
  HistorialAgenteSeniorRespuesta,
  MensajeAgenteSenior
} from '../interfaces/asistente-ia.interface';
import { MensajeWS } from '../interfaces/diagrama.interface';

export const ESTADO_COLA_INICIAL: EstadoColaAgenteSenior = {
  procesando: false,
  mensaje_procesando_id: null,
  usuario_procesando: null,
  en_cola_count: 0,
  max_en_cola: 2,
  cola_llena: false,
  posiciones_cola: {}
};

@Injectable({
  providedIn: 'root'
})
export class AgenteSeniorService {
  private readonly http = inject(HttpClient);
  private readonly socketService = inject(WhiteboardSocketService);
  private readonly tokenStorage = inject(TokenStorageService);

  private readonly _mensajes$ = new BehaviorSubject<MensajeAgenteSenior[]>([]);
  public readonly mensajes$ = this._mensajes$.asObservable();

  private readonly _estadoCola$ = new BehaviorSubject<EstadoColaAgenteSenior>(ESTADO_COLA_INICIAL);
  public readonly estadoCola$ = this._estadoCola$.asObservable();

  private readonly _cargandoHistorial$ = new BehaviorSubject<boolean>(false);
  public readonly cargandoHistorial$ = this._cargandoHistorial$.asObservable();

  private readonly _enviandoConsulta$ = new BehaviorSubject<boolean>(false);
  public readonly enviandoConsulta$ = this._enviandoConsulta$.asObservable();

  private readonly _maxCaracteres$ = new BehaviorSubject<number>(2000);
  public readonly maxCaracteres$ = this._maxCaracteres$.asObservable();

  private readonly _consultaRevertida$ = new Subject<string>();
  public readonly consultaRevertida$ = this._consultaRevertida$.asObservable();

  private readonly _eventoError$ = new Subject<string>();
  public readonly eventoError$ = this._eventoError$.asObservable();

  private readonly _nuevoMensajeRecibido$ = new Subject<MensajeAgenteSenior>();
  public readonly nuevoMensajeRecibido$ = this._nuevoMensajeRecibido$.asObservable();

  private wsSub: Subscription | null = null;
  private proyectoActualId = 0;

  /**
   * Inicializa la suscripción a eventos WebSocket del proyecto y carga el historial inicial.
   */
  public inicializarProyecto(proyectoId: number): void {
    if (!proyectoId) return;
    if (this.proyectoActualId !== proyectoId) {
      this.limpiarEstado();
      this.proyectoActualId = proyectoId;
    }
    this.suscribirEventosSocket();
    this.cargarHistorial(proyectoId);
  }

  /**
   * Reinicia el estado reactivo al salir del proyecto.
   */
  public limpiarEstado(): void {
    this.wsSub?.unsubscribe();
    this.wsSub = null;
    this.proyectoActualId = 0;
    this._mensajes$.next([]);
    this._estadoCola$.next(ESTADO_COLA_INICIAL);
    this._cargandoHistorial$.next(false);
    this._enviandoConsulta$.next(false);
  }

  /**
   * Obtiene del backend el historial compartido de la conversación y el estado vigente de la cola.
   */
  public cargarHistorial(proyectoId: number): void {
    if (!proyectoId) return;
    const url = `${environment.apiUrl}/asistente/proyectos/${proyectoId}/agente-senior/`;
    this._cargandoHistorial$.next(true);

    this.http
      .get<HistorialAgenteSeniorRespuesta>(url)
      .pipe(finalize(() => this._cargandoHistorial$.next(false)))
      .subscribe({
        next: (resp: HistorialAgenteSeniorRespuesta) => {
          if (resp.max_caracteres) {
            this._maxCaracteres$.next(resp.max_caracteres);
          }
          const cola = resp.estado_cola || ESTADO_COLA_INICIAL;
          this._estadoCola$.next(cola);
          const sincronizados = this.aplicarPosicionesCola(resp.mensajes || [], cola);
          this._mensajes$.next(sincronizados);
        },
        error: (err: HttpErrorResponse) => {
          const msg = this.extraerMensajeError(err, 'No se pudo cargar el historial del Agente Senior.');
          this._eventoError$.next(msg);
        }
      });
  }

  /**
   * Envía una consulta al Agente Senior Colaborativo validando longitud y disponibilidad de la cola.
   */
  public enviarConsulta(
    proyectoId: number,
    contenido: string,
    contextoDiagrama: ContextoDiagramaIA
  ): Observable<EnviarConsultaAgenteSeniorRespuesta> {
    const url = `${environment.apiUrl}/asistente/proyectos/${proyectoId}/agente-senior/`;
    this._enviandoConsulta$.next(true);

    return this.http
      .post<EnviarConsultaAgenteSeniorRespuesta>(url, {
        contenido: contenido.trim(),
        contexto_diagrama: contextoDiagrama
      })
      .pipe(
        tap((resp: EnviarConsultaAgenteSeniorRespuesta) => {
          if (resp.estado_cola) {
            this._estadoCola$.next(resp.estado_cola);
          }
          if (resp.mensaje) {
            this.insertarOActualizarMensaje(resp.mensaje, resp.estado_cola);
          }
        }),
        finalize(() => this._enviandoConsulta$.next(false))
      );
  }

  /**
   * Extrae un mensaje de error legible desde un HttpErrorResponse.
   */
  public extraerMensajeError(err: HttpErrorResponse, fallback: string): string {
    const body = err.error as Record<string, unknown> | null;
    if (body) {
      if (typeof body['detail'] === 'string' && body['detail']) {
        return body['detail'];
      }
      if (typeof body['error'] === 'string' && body['error']) {
        return body['error'];
      }
    }
    return fallback;
  }

  /**
   * Actualiza el estado de la cola si viene embebido en un error 429 (cola llena).
   */
  public actualizarColaDesdeError(err: HttpErrorResponse): void {
    const body = err.error as Record<string, unknown> | null;
    if (body && body['estado_cola'] && typeof body['estado_cola'] === 'object') {
      const cola = body['estado_cola'] as EstadoColaAgenteSenior;
      this._estadoCola$.next(cola);
      const actuales = this.aplicarPosicionesCola(this._mensajes$.getValue(), cola);
      this._mensajes$.next(actuales);
    }
  }

  /**
   * Transforma texto en formato Markdown (negritas, código inline, bloques, títulos y listas)
   * en HTML seguro y estilizado para las burbujas del Agente Senior.
   */
  public formatearMarkdown(textoRaw: string): string {
    if (!textoRaw) return '';
    const escapado = textoRaw
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    const lineas = escapado.split(/\r?\n/);
    const bloquesHtml: string[] = [];
    let enListaUl = false;
    let enListaOl = false;
    let enBloqueCodigo = false;
    let bufferCodigo: string[] = [];

    const cerrarListas = (): void => {
      if (enListaUl) {
        bloquesHtml.push('</ul>');
        enListaUl = false;
      }
      if (enListaOl) {
        bloquesHtml.push('</ol>');
        enListaOl = false;
      }
    };

    for (const lineaOriginal of lineas) {
      const lineaTrim = lineaOriginal.trim();

      if (lineaTrim.startsWith('```')) {
        cerrarListas();
        if (!enBloqueCodigo) {
          enBloqueCodigo = true;
          bufferCodigo = [];
        } else {
          bloquesHtml.push(`<pre class="md-pre"><code>${bufferCodigo.join('\n')}</code></pre>`);
          enBloqueCodigo = false;
          bufferCodigo = [];
        }
        continue;
      }

      if (enBloqueCodigo) {
        bufferCodigo.push(lineaOriginal);
        continue;
      }

      if (!lineaTrim) {
        cerrarListas();
        continue;
      }

      if (/^[-*_]{3,}$/.test(lineaTrim)) {
        cerrarListas();
        bloquesHtml.push('<hr class="md-hr" />');
        continue;
      }

      const matchHeading = lineaTrim.match(/^(#{1,4})\s+(.+)$/);
      if (matchHeading) {
        cerrarListas();
        const contenidoH = this.formatearInlineMarkdown(matchHeading[2]);
        bloquesHtml.push(`<h4 class="md-heading">${contenidoH}</h4>`);
        continue;
      }

      const matchUl = lineaTrim.match(/^[*•-]\s+(.+)$/);
      if (matchUl) {
        if (enListaOl) {
          bloquesHtml.push('</ol>');
          enListaOl = false;
        }
        if (!enListaUl) {
          bloquesHtml.push('<ul class="md-ul">');
          enListaUl = true;
        }
        bloquesHtml.push(`<li class="md-li">${this.formatearInlineMarkdown(matchUl[1])}</li>`);
        continue;
      }

      const matchOl = lineaTrim.match(/^\d+[.)]\s+(.+)$/);
      if (matchOl) {
        if (enListaUl) {
          bloquesHtml.push('</ul>');
          enListaUl = false;
        }
        if (!enListaOl) {
          bloquesHtml.push('<ol class="md-ol">');
          enListaOl = true;
        }
        bloquesHtml.push(`<li class="md-li">${this.formatearInlineMarkdown(matchOl[1])}</li>`);
        continue;
      }

      cerrarListas();
      bloquesHtml.push(`<p class="md-p">${this.formatearInlineMarkdown(lineaTrim)}</p>`);
    }

    cerrarListas();
    if (enBloqueCodigo && bufferCodigo.length > 0) {
      bloquesHtml.push(`<pre class="md-pre"><code>${bufferCodigo.join('\n')}</code></pre>`);
    }

    return bloquesHtml.join('');
  }

  private formatearInlineMarkdown(texto: string): string {
    return texto
      .replace(/`([^`]+)`/g, '<code class="md-code">$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong class="md-strong">$1</strong>')
      .replace(/__([^_]+)__/g, '<strong class="md-strong">$1</strong>')
      .replace(/(^|[\s(])\*([^*\n]+)\*(?=[\s.,;:!?)]|$)/g, '$1<em class="md-em">$2</em>');
  }

  private suscribirEventosSocket(): void {
    this.wsSub?.unsubscribe();
    this.wsSub = this.socketService.mensajes$.subscribe((msg: MensajeWS) => {
      const accion = msg.accion || msg.evento;
      if (
        accion !== 'agente_senior_mensaje_creado' &&
        accion !== 'agente_senior_estado_actualizado' &&
        accion !== 'agente_senior_respuesta' &&
        accion !== 'agente_senior_error'
      ) {
        return;
      }

      const payload = (msg.data || msg) as unknown as EventoWSAgenteSenior;
      this.procesarEventoRealtime(accion, payload);
    });
  }

  private procesarEventoRealtime(accion: string, payload: EventoWSAgenteSenior): void {
    const nuevaCola = payload.estado_cola || this._estadoCola$.getValue();
    if (payload.estado_cola) {
      this._estadoCola$.next(payload.estado_cola);
    }

    if (accion === 'agente_senior_mensaje_creado' || accion === 'agente_senior_estado_actualizado') {
      if (payload.mensaje) {
        this.insertarOActualizarMensaje(payload.mensaje, nuevaCola);
        this._nuevoMensajeRecibido$.next(payload.mensaje);
      }
      return;
    }

    if (accion === 'agente_senior_respuesta') {
      if (payload.pregunta) {
        this.insertarOActualizarMensaje(payload.pregunta, nuevaCola);
      }
      if (payload.siguiente_procesando) {
        this.insertarOActualizarMensaje(payload.siguiente_procesando, nuevaCola);
      }
      if (payload.respuesta) {
        this.insertarOActualizarMensaje(payload.respuesta, nuevaCola);
        this._nuevoMensajeRecibido$.next(payload.respuesta);
      }
      return;
    }

    if (accion === 'agente_senior_error') {
      if (payload.pregunta_descartada_id !== undefined) {
        const filtrados = this._mensajes$
          .getValue()
          .filter(m => m.id !== payload.pregunta_descartada_id);
        this._mensajes$.next(this.aplicarPosicionesCola(filtrados, nuevaCola));
      }
      if (payload.siguiente_procesando) {
        this.insertarOActualizarMensaje(payload.siguiente_procesando, nuevaCola);
      }
      const miId = this.tokenStorage.getUser()?.id ?? null;
      if (miId && payload.usuario_id === miId && payload.contenido_original) {
        this._consultaRevertida$.next(payload.contenido_original);
      }
      const aviso =
        payload.mensaje_error ||
        'El Agente Senior no está disponible temporalmente. Intenta enviar la consulta nuevamente.';
      this._eventoError$.next(aviso);
    }
  }

  private insertarOActualizarMensaje(
    entrante: MensajeAgenteSenior,
    cola: EstadoColaAgenteSenior
  ): void {
    const lista = [...this._mensajes$.getValue()];
    const idx = lista.findIndex(m => m.id === entrante.id);
    if (idx >= 0) {
      lista[idx] = { ...lista[idx], ...entrante };
    } else {
      lista.push(entrante);
    }
    lista.sort((a, b) => a.id - b.id);
    this._mensajes$.next(this.aplicarPosicionesCola(lista, cola));
  }

  private aplicarPosicionesCola(
    mensajes: MensajeAgenteSenior[],
    cola: EstadoColaAgenteSenior
  ): MensajeAgenteSenior[] {
    const mapa = cola.posiciones_cola || {};
    return mensajes.map(m => {
      if (m.estado === 'en_cola') {
        const pos = mapa[String(m.id)] ?? m.posicion_cola ?? null;
        return { ...m, posicion_cola: pos };
      }
      return { ...m, posicion_cola: null };
    });
  }
}

