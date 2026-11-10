import { Injectable, inject, NgZone } from '@angular/core';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { BehaviorSubject, Subject, Subscription, timer, firstValueFrom, timeout } from 'rxjs';
import { filter, switchMap, debounceTime } from 'rxjs/operators';
import { TokenStorageService } from '../../../core/services/token-storage.service';
import { MensajeWS, EstadoConexion, AccionWS, EntidadDiagrama, RelacionDiagrama, UsuarioConectado } from '../interfaces/diagrama.interface';
import { confirmacionCorresponde, esConflictoRevision, requestCorresponde } from '../utils/revision.utils';

interface SnapshotPendiente {
  datos: Record<string, unknown>;
  expectedRevision: number;
  operations?: { snapshot: Record<string, unknown>; description: string }[];
  requestId?: string;
}

const SNAPSHOT_CONFIRMATION_TIMEOUT_MS = 15_000;

@Injectable({
  providedIn: 'root'
})
export class WhiteboardSocketService {
  private readonly tokenStorage = inject(TokenStorageService);
  private readonly ngZone = inject(NgZone);

  private socket$: WebSocketSubject<MensajeWS> | null = null;
  private subscription: Subscription | null = null;

  // Estado publico de la conexion
  private readonly _estado$ = new BehaviorSubject<EstadoConexion>('desconectado');
  public readonly estado$ = this._estado$.asObservable();

  // Stream de mensajes entrantes para que el componente se suscriba
  private readonly _mensajes$ = new Subject<MensajeWS>();
  public readonly mensajes$ = this._mensajes$.asObservable();

  // Estado del autoguardado (guardado, guardando, error)
  private readonly _estadoGuardado$ = new BehaviorSubject<'guardado' | 'guardando' | 'error'>('guardado');
  public readonly estadoGuardado$ = this._estadoGuardado$.asObservable();

  private readonly _revision$ = new BehaviorSubject<number>(0);
  public readonly revision$ = this._revision$.asObservable();
  private readonly _conflicto$ = new BehaviorSubject<MensajeWS | null>(null);
  public readonly conflicto$ = this._conflicto$.asObservable();
  private guardadoPendiente = false;
  private snapshotEnDebounce: SnapshotPendiente | null = null;
  private snapshotEnCola: SnapshotPendiente | null = null;
  private snapshotPendiente: SnapshotPendiente | null = null;
  private requestPendiente: string | null = null;
  private timeoutGuardadoSub: Subscription | null = null;
  private recuperacionPendiente = false;
  private proyectoActual: number | null = null;
  private nombreEnCola: string | null = null;
  private secuenciaRequest = 0;
  private debouncePendiente = false;
  private ultimoSnapshotLocal: string | null = null;
  private snapshotIncierto: SnapshotPendiente | null = null;

  // Lista de colaboradores actualmente conectados
  private readonly _usuariosConectados$ = new BehaviorSubject<UsuarioConectado[]>([]);
  public readonly usuariosConectados$ = this._usuariosConectados$.asObservable();

  // Debounce para guardar_snapshot: 2 segundos de inactividad
  private readonly _snapshotTrigger$ = new Subject<SnapshotPendiente>();
  private snapshotSub: Subscription | null = null;

  public conectar(proyectoId: number): void {
    const token = this.tokenStorage.getAccessToken();
    if (!token) {
      console.error('[WS] No hay token JWT disponible');
      this._estado$.next('error');
      return;
    }

    if (this.socket$) {
      this.desconectar();
    }
    this.proyectoActual = proyectoId;
    this.guardadoPendiente = false;
    this.snapshotEnDebounce = null;
    this.snapshotPendiente = null;
    this.snapshotEnCola = null;
    this.requestPendiente = null;
    this.nombreEnCola = null;
    this.debouncePendiente = false;
    this.recuperacionPendiente = false;
    this.ultimoSnapshotLocal = null;
    this.snapshotIncierto = null;
    this._estadoGuardado$.next('guardado');
    this._conflicto$.next(null);

    const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
    const wsUrl = `ws://${host}:8000/ws/pizarra/${proyectoId}/?token=${token}`;
    this._estado$.next('conectando');

    // Ejecutar fuera de la zona Angular para evitar deteccion de cambios excesiva
    this.ngZone.runOutsideAngular(() => {
      this.socket$ = webSocket<MensajeWS>({
        url: wsUrl,
        openObserver: {
          next: () => {
            this.ngZone.run(() => this._estado$.next('conectado'));
          }
        },
        closeObserver: {
          next: () => {
            this.ngZone.run(() => {
              this._estado$.next('desconectado');
              this.marcarGuardadoIncierto();
            });
          }
        }
      });

      this.subscription = this.socket$.subscribe({
        next: (mensaje: MensajeWS) => {
          // Normalizar campos entre envoltura (evento/data) y campos planos
          const accion = mensaje.accion || mensaje.evento;
          const dataObj = mensaje.data;
          const normalizado: MensajeWS = {
            ...mensaje,
            accion,
            evento: accion,
            entidad_id: mensaje.entidad_id ?? (dataObj?.['entidad_id'] as number | undefined),
            relacion_id: mensaje.relacion_id ?? (dataObj?.['relacion_id'] as number | undefined),
            proyecto_id: mensaje.proyecto_id ?? (dataObj?.['proyecto_id'] as number | undefined),
            nombre: mensaje.nombre ?? (dataObj?.['nombre'] as string | undefined),
            x: mensaje.x ?? (dataObj?.['x'] as number | undefined) ?? (dataObj?.['coord_x'] as number | undefined),
            y: mensaje.y ?? (dataObj?.['y'] as number | undefined) ?? (dataObj?.['coord_y'] as number | undefined),
            coord_x: mensaje.coord_x ?? (dataObj?.['coord_x'] as number | undefined) ?? (dataObj?.['x'] as number | undefined),
            coord_y: mensaje.coord_y ?? (dataObj?.['coord_y'] as number | undefined) ?? (dataObj?.['y'] as number | undefined),
            entidad: mensaje.entidad ?? (dataObj?.['entidad'] as EntidadDiagrama | undefined),
            relacion: mensaje.relacion ?? (dataObj?.['relacion'] as RelacionDiagrama | undefined),
            usuario_id: mensaje.usuario_id ?? (dataObj?.['usuario_id'] as number | undefined),
            username: mensaje.username ?? (dataObj?.['username'] as string | undefined),
            first_name: mensaje.first_name ?? (dataObj?.['first_name'] as string | undefined),
            email: mensaje.email ?? (dataObj?.['email'] as string | undefined),
            usuarios: mensaje.usuarios ?? (dataObj?.['usuarios'] as UsuarioConectado[] | undefined),
            id_map: mensaje.id_map ?? (dataObj?.['id_map'] as Record<string, number> | undefined),
            attr_id_map: mensaje.attr_id_map ?? (dataObj?.['attr_id_map'] as Record<string, number> | undefined),
            operation_id_map: mensaje.operation_id_map ?? (dataObj?.['operation_id_map'] as Record<string, number> | undefined),
            parameter_id_map: mensaje.parameter_id_map ?? (dataObj?.['parameter_id_map'] as Record<string, number> | undefined),
            rel_id_map: mensaje.rel_id_map ?? (dataObj?.['rel_id_map'] as Record<string, number> | undefined),
            exito: mensaje.exito ?? (dataObj?.['exito'] as boolean | undefined),
            revision: mensaje.revision ?? (dataObj?.['revision'] as number | undefined),
            current_revision: mensaje.current_revision ?? (dataObj?.['current_revision'] as number | undefined),
            request_id: mensaje.request_id ?? (dataObj?.['request_id'] as string | undefined),
            codigo: mensaje.codigo ?? (dataObj?.['codigo'] as string | undefined),
            mensaje: mensaje.mensaje ?? (dataObj?.['mensaje'] as string | undefined)
          };

          let confirmacionAceptada = false;
          if (accion === 'snapshot_guardado') {
            confirmacionAceptada = this.procesarConfirmacionSnapshot(normalizado);
            normalizado.confirmacion_local = confirmacionAceptada;
          } else if (accion === 'proyecto_renombrado' && normalizado.revision !== undefined) {
            this._revision$.next(normalizado.revision);
          } else if (accion === 'comando_rechazado' && normalizado.codigo) {
            this.procesarRechazoSnapshot(normalizado);
          } else if (accion === 'usuarios_conectados') {
            const lista = normalizado.usuarios || (dataObj?.['usuarios'] as UsuarioConectado[]) || [];
            this.ngZone.run(() => this._usuariosConectados$.next(lista));
          } else if (accion === 'colaborador_unido') {
            const actual = this._usuariosConectados$.getValue();
            const uid = normalizado.usuario_id ?? (dataObj?.['usuario_id'] as number | undefined);
            if (uid && !actual.some(u => u.usuario_id === uid)) {
              const nuevo: UsuarioConectado = {
                usuario_id: uid,
                username: normalizado.username ?? (dataObj?.['username'] as string | undefined) ?? 'Colaborador',
                first_name: normalizado.first_name ?? (dataObj?.['first_name'] as string | undefined),
                email: normalizado.email ?? (dataObj?.['email'] as string | undefined)
              };
              this.ngZone.run(() => this._usuariosConectados$.next([...actual, nuevo]));
            }
          } else if (accion === 'colaborador_salido') {
            const actual = this._usuariosConectados$.getValue();
            const uid = normalizado.usuario_id ?? (dataObj?.['usuario_id'] as number | undefined);
            if (uid) {
              this.ngZone.run(() => this._usuariosConectados$.next(actual.filter(u => u.usuario_id !== uid)));
            }
          }

          if (['snapshot_guardado', 'diagram.updated', 'history.updated'].includes(accion || '') &&
              !confirmacionAceptada && typeof normalizado.revision === 'number' &&
              normalizado.revision > this.revisionActual && (this.guardadoPendiente || this.hayCambiosLocalesPendientes())) {
            this.registrarConflictoRevision(normalizado.revision, 'Otro cambio fue confirmado mientras tenías cambios pendientes. Recupera el estado vigente antes de continuar.');
          }

          this.ngZone.run(() => this._mensajes$.next(normalizado));
          if (confirmacionAceptada && !this._conflicto$.getValue() && this.snapshotEnCola) {
            const siguiente = this.snapshotEnCola;
            this.snapshotEnCola = null;
            this.enviarSnapshot({
              ...siguiente,
              expectedRevision: this._revision$.getValue()
            });
          } else if (
            confirmacionAceptada && !this._conflicto$.getValue() &&
            !this.hayCambiosLocalesPendientes() && this.nombreEnCola
          ) {
            const nombre = this.nombreEnCola;
            this.nombreEnCola = null;
            this.enviarRenombrarProyecto(nombre);
          }
        },
        error: () => {
          this.ngZone.run(() => {
            this._estado$.next('error');
            this.marcarGuardadoIncierto();
          });
        }
      });
    });

    // Configurar el debounce de 2 segundos para guardar_snapshot
    this.iniciarDebounceSnapshots();
  }

  public desconectar(): void {
    this.cancelarTimeoutGuardado();
    this.snapshotSub?.unsubscribe();
    this.subscription?.unsubscribe();
    this.socket$?.complete();
    this.socket$ = null;
    this._estado$.next('desconectado');
    this._usuariosConectados$.next([]);
  }

  public enviarRenombrarProyecto(nombre: string): void {
    if (this.guardadoPendiente || this.snapshotEnCola || this._estadoGuardado$.getValue() === 'guardando' || this._conflicto$.getValue()) {
      this.nombreEnCola = nombre;
      return;
    }
    this.enviarMensaje({
      accion: 'renombrar_proyecto', nombre,
      expected_revision: this._revision$.getValue(), request_id: this.nuevoRequestId()
    });
  }

  public enviarMoverEntidad(entidadId: number, x: number, y: number): void {
    this.enviarMensaje({
      accion: 'mover_entidad',
      entidad_id: entidadId,
      x,
      y,
      coord_x: x,
      coord_y: y
    });
  }

  public enviarBloquearEntidad(entidadId: number): void {
    this.enviarMensaje({ accion: 'bloquear_entidad', entidad_id: entidadId });
  }

  public enviarDesbloquearEntidad(entidadId: number): void {
    this.enviarMensaje({ accion: 'desbloquear_entidad', entidad_id: entidadId });
  }

  public enviarCrearEntidad(entidad: EntidadDiagrama): void {
    this.enviarMensaje({ accion: 'crear_entidad', entidad });
  }

  public enviarActualizarEntidad(entidad: EntidadDiagrama): void {
    this.enviarMensaje({ accion: 'actualizar_entidad', entidad });
  }

  public enviarEliminarEntidad(entidadId: number): void {
    this.enviarMensaje({ accion: 'eliminar_entidad', entidad_id: entidadId });
  }

  public enviarCrearRelacion(relacion: RelacionDiagrama): void {
    this.enviarMensaje({ accion: 'crear_relacion', relacion });
  }

  public enviarActualizarRelacion(relacion: RelacionDiagrama): void {
    this.enviarMensaje({ accion: 'actualizar_relacion', relacion });
  }

  public enviarEliminarRelacion(relacionId: number): void {
    this.enviarMensaje({ accion: 'eliminar_relacion', relacion_id: relacionId });
  }

  /** Programa el guardado del snapshot con debounce de 2s */
  public programarGuardarSnapshot(datos: Record<string, unknown>): void {
    const pendiente = this.prepararSnapshot(datos);
    if (!pendiente) return;
    this._estadoGuardado$.next('guardando');
    this.debouncePendiente = true;
    this.snapshotEnCola = null;
    this.snapshotEnDebounce = pendiente;
    this._snapshotTrigger$.next(this.snapshotEnDebounce);
  }

  /** Fuerza el guardado inmediato del snapshot sin esperar el debounce */
  public forzarGuardarSnapshot(datos: Record<string, unknown>): void {
    const pendiente = this.prepararSnapshot(datos) || this.snapshotEnDebounce || this.snapshotEnCola;
    if (!pendiente) return;
    if (this._conflicto$.getValue()) {
      this.snapshotEnCola = pendiente;
      this._estadoGuardado$.next('error');
      return;
    }
    this._estadoGuardado$.next('guardando');
    this.debouncePendiente = false;
    this.snapshotEnDebounce = null;
    this.snapshotEnCola = null;
    this.encolarOEnviarSnapshot(pendiente);
  }

  private prepararSnapshot(datos: Record<string, unknown>): SnapshotPendiente | null {
    const copy = JSON.parse(JSON.stringify(datos)) as Record<string, unknown>;
    const entities = copy['entidades'] as EntidadDiagrama[] | undefined;
    entities?.forEach(e => { if (e.estado === 'bloqueado') e.estado = 'activo'; });
    const serialized = JSON.stringify(copy);
    if (serialized === this.ultimoSnapshotLocal) return null;
    this.ultimoSnapshotLocal = serialized;
    const previous = this.snapshotEnDebounce || this.snapshotEnCola;
    return { datos: copy, expectedRevision: previous?.expectedRevision ?? this.revisionActual,
      operations: [...(previous?.operations || []), { snapshot: copy, description: 'Editar diagrama' }] };
  }

  public get tieneCambiosPendientes(): boolean {
    return this.guardadoPendiente || this.hayCambiosLocalesPendientes() || this.recuperacionPendiente;
  }

  /** Espera la autoridad de Django, incluyendo un debounce que aún no se envió. */
  public async esperarGuardadoConfirmado(): Promise<void> {
    if (this._estado$.value !== 'conectado') throw new Error('Sin conexión: no se puede modificar el historial.');
    if (this._conflicto$.value) throw new Error('Recupera el estado confirmado para resolver el conflicto antes de deshacer.');
    if (this.snapshotIncierto && !this.guardadoPendiente) {
      const pending = this.snapshotIncierto;
      this.snapshotIncierto = null;
      if (this.snapshotEnCola === pending) this.snapshotEnCola = null;
      this.recuperacionPendiente = false;
      this._estadoGuardado$.next('guardando');
      this.enviarSnapshot(pending);
    } else if (this.recuperacionPendiente) {
      throw new Error('El guardado fue rechazado. Recupera el estado confirmado antes de continuar.');
    }
    if (this.snapshotEnDebounce) this.forzarGuardarSnapshot(this.snapshotEnDebounce.datos);
    if (this._estadoGuardado$.value === 'guardado' && !this.tieneCambiosPendientes) return;
    const state = await firstValueFrom(this.estadoGuardado$.pipe(filter(s => s !== 'guardando'), timeout(20_000)));
    if (state !== 'guardado' || this.tieneCambiosPendientes) throw new Error('No se confirmó el guardado. El historial no se modificó.');
  }

  public establecerSnapshotConfirmado(datos: Record<string, unknown>): void {
    if (!this.tieneCambiosPendientes) this.ultimoSnapshotLocal = JSON.stringify(datos);
  }

  public establecerRevision(revision: number): void {
    this._revision$.next(revision);
  }

  public get revisionActual(): number { return this._revision$.getValue(); }

  public descartarCambiosLocalesEnConflicto(): void {
    this.snapshotEnCola = null;
    this.snapshotEnDebounce = null;
    this.snapshotPendiente = null;
    this.guardadoPendiente = false;
    this.requestPendiente = null;
    this.debouncePendiente = false;
    this.recuperacionPendiente = false;
    this.snapshotIncierto = null;
    this.ultimoSnapshotLocal = null;
    this.cancelarTimeoutGuardado();
    this._conflicto$.next(null);
    this._estadoGuardado$.next('guardado');
  }

  public registrarConflictoRevision(currentRevision?: number, mensaje?: string): void {
    this._estadoGuardado$.next('error');
    this._conflicto$.next({
      accion: 'comando_rechazado', exito: false, codigo: 'stale_revision',
      current_revision: currentRevision,
      mensaje: mensaje || 'El diagrama cambió desde tu última sincronización.'
    });
  }

  private encolarOEnviarSnapshot(pendiente: SnapshotPendiente): void {
    if (this._conflicto$.getValue() || this.recuperacionPendiente || this.guardadoPendiente) {
      this.snapshotEnCola = pendiente;
      return;
    }
    this.enviarSnapshot(pendiente);
  }

  private enviarSnapshot(pendiente: SnapshotPendiente): void {
    const requestId = pendiente.requestId || this.nuevoRequestId();
    pendiente.requestId = requestId;
    this.guardadoPendiente = true;
    this.snapshotPendiente = pendiente;
    this.requestPendiente = requestId;
    this.iniciarTimeoutGuardado(requestId);
    this.enviarMensaje({
      accion: 'guardar_snapshot', datos_diagrama: pendiente.datos,
      expected_revision: pendiente.expectedRevision, request_id: requestId,
      operations: pendiente.operations
    });
  }

  private nuevoRequestId(): string {
    this.secuenciaRequest += 1;
    const cryptoApi = globalThis.crypto;
    if (typeof cryptoApi?.randomUUID === 'function') return `ws-${cryptoApi.randomUUID()}`;
    return `ws-${Date.now()}-${Math.random().toString(36).slice(2)}-${this.secuenciaRequest}`;
  }

  private procesarConfirmacionSnapshot(mensaje: MensajeWS): boolean {
    if (!this.guardadoPendiente || !this.snapshotPendiente) return false;
    if (mensaje.proyecto_id !== this.proyectoActual) return false;
    if (!confirmacionCorresponde(this.requestPendiente, mensaje)) return false;
    const revision = mensaje.revision;
    if (
      typeof revision !== 'number' || !Number.isSafeInteger(revision) ||
      revision !== this.snapshotPendiente.expectedRevision + 1
    ) {
      return false;
    }

    this.cancelarTimeoutGuardado();
    this.remapearPendientes(mensaje);
    this._revision$.next(revision);
    this.rebasarPendientesTrasConfirmacionPropia(revision);
    this.guardadoPendiente = false;
    this.snapshotPendiente = null;
    this.requestPendiente = null;
    this.recuperacionPendiente = false;
    this.ngZone.run(() => {
      this._estadoGuardado$.next(this.hayCambiosLocalesPendientes() ? 'guardando' : 'guardado');
    });
    return true;
  }

  private procesarRechazoSnapshot(mensaje: MensajeWS): void {
    if (!this.guardadoPendiente || mensaje.proyecto_id !== this.proyectoActual) return;
    if (!requestCorresponde(this.requestPendiente, mensaje)) return;

    this.cancelarTimeoutGuardado();
    const ultimo = this.snapshotEnDebounce || this.snapshotEnCola || this.snapshotPendiente;
    if (ultimo) this.snapshotEnCola = ultimo;
    this.snapshotPendiente = null;
    this.guardadoPendiente = false;
    this.requestPendiente = null;
    this.recuperacionPendiente = true;
    this.ngZone.run(() => {
      this._estadoGuardado$.next('error');
      // Todo rechazo conserva el borrador y ofrece reconciliación explícita;
      // un timeout, en cambio, conserva el recibo pendiente para reintentar.
      this._conflicto$.next(mensaje);
    });
  }

  private hayCambiosLocalesPendientes(): boolean {
    return this.debouncePendiente || this.snapshotEnDebounce !== null || this.snapshotEnCola !== null;
  }

  private rebasarPendientesTrasConfirmacionPropia(revision: number): void {
    if (this.snapshotEnDebounce) {
      this.snapshotEnDebounce.expectedRevision = revision;
    }
    if (this.snapshotEnCola) {
      this.snapshotEnCola.expectedRevision = revision;
    }
  }

  private iniciarTimeoutGuardado(requestId: string): void {
    this.cancelarTimeoutGuardado();
    this.timeoutGuardadoSub = timer(SNAPSHOT_CONFIRMATION_TIMEOUT_MS).subscribe(() => {
      if (this.requestPendiente === requestId) this.marcarGuardadoIncierto();
    });
  }

  private iniciarDebounceSnapshots(): void {
    this.snapshotSub?.unsubscribe();
    this.snapshotSub = this._snapshotTrigger$.pipe(
      debounceTime(2000)
    ).subscribe((pendiente) => {
      if (this.snapshotEnDebounce !== pendiente) return;
      this.debouncePendiente = false;
      this.snapshotEnDebounce = null;
      this.encolarOEnviarSnapshot(pendiente);
    });
  }

  private cancelarTimeoutGuardado(): void {
    this.timeoutGuardadoSub?.unsubscribe();
    this.timeoutGuardadoSub = null;
  }

  private marcarGuardadoIncierto(): void {
    if (!this.guardadoPendiente && !this.hayCambiosLocalesPendientes()) return;
    this.cancelarTimeoutGuardado();
    this.snapshotIncierto = this.snapshotPendiente || this.snapshotIncierto;
    const ultimo = this.snapshotEnDebounce || this.snapshotEnCola || this.snapshotPendiente;
    if (ultimo) this.snapshotEnCola = ultimo;
    this.snapshotPendiente = null;
    this.guardadoPendiente = false;
    this.requestPendiente = null;
    this.recuperacionPendiente = true;
    this._estadoGuardado$.next('error');
  }

  private remapearPendientes(maps: MensajeWS): void {
    const remap = (data: Record<string, unknown>): void => {
      const mapId = (id: number, mapping?: Record<string, number>): number => mapping?.[id] ?? id;
      const ref = (row: any): void => {
        for (const key of ['tipo_referencia_id', 'retorno_referencia_id', 'entidad_origen_id', 'entidad_destino_id', 'clase_asociacion_id']) {
          if (row[key] !== null && row[key] !== undefined) row[key] = mapId(row[key], maps.id_map);
        }
      };
      for (const e of (data['entidades'] as EntidadDiagrama[] || [])) {
        e.id = mapId(e.id, maps.id_map);
        for (const a of e.atributos || []) { a.id = mapId(a.id, maps.attr_id_map); ref(a); }
        for (const o of e.operaciones || []) {
          o.id = mapId(o.id, maps.operation_id_map); ref(o);
          for (const p of o.parametros || []) { p.id = mapId(p.id, maps.parameter_id_map); ref(p); }
        }
      }
      for (const r of (data['relaciones'] as RelacionDiagrama[] || [])) { r.id = mapId(r.id, maps.rel_id_map); ref(r); }
      if (data['posiciones']) data['posiciones'] = Object.fromEntries(Object.entries(data['posiciones'] as object).map(([key, value]) => [mapId(Number(key), maps.id_map), value]));
    };
    for (const pending of [this.snapshotEnDebounce, this.snapshotEnCola]) {
      if (!pending) continue;
      remap(pending.datos);
      pending.operations?.forEach(op => remap(op.snapshot));
    }
    if (this.ultimoSnapshotLocal) {
      const last = JSON.parse(this.ultimoSnapshotLocal); remap(last); this.ultimoSnapshotLocal = JSON.stringify(last);
    }
  }

  private enviarMensaje(mensaje: MensajeWS): void {
    if (this.socket$ && this._estado$.getValue() === 'conectado') {
      this.socket$.next(mensaje);
    }
  }

  private contadorSesion = 0;

  /**
   * Genera un identificador numérico negativo único para entidades, atributos o relaciones locales.
   * Permite la sincronización optimista local hasta que el servidor devuelva los IDs definitivos.
   */
  public generarIdTemporal(): number {
    this.contadorSesion++;
    const delta = Date.now() - 1700000000000;
    const user = this.tokenStorage.getUser();
    const userSeed = user?.id ? (Math.abs(user.id) % 100) : Math.floor(Math.random() * 90 + 10);
    return - (delta * 10000 + userSeed * 100 + (this.contadorSesion % 100));
  }
}
