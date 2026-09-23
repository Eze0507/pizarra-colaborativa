import { Injectable, inject, NgZone } from '@angular/core';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { BehaviorSubject, Subject, Subscription, timer } from 'rxjs';
import { filter, switchMap, debounceTime } from 'rxjs/operators';
import { TokenStorageService } from '../../../core/services/token-storage.service';
import { MensajeWS, EstadoConexion, AccionWS, EntidadDiagrama, RelacionDiagrama, UsuarioConectado } from '../interfaces/diagrama.interface';

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

  // Lista de colaboradores actualmente conectados
  private readonly _usuariosConectados$ = new BehaviorSubject<UsuarioConectado[]>([]);
  public readonly usuariosConectados$ = this._usuariosConectados$.asObservable();

  // Debounce para guardar_snapshot: 2 segundos de inactividad
  private readonly _snapshotTrigger$ = new Subject<Record<string, unknown>>();
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

    const wsUrl = `ws://localhost:8000/ws/pizarra/${proyectoId}/?token=${token}`;
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
            this.ngZone.run(() => this._estado$.next('desconectado'));
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
            rel_id_map: mensaje.rel_id_map ?? (dataObj?.['rel_id_map'] as Record<string, number> | undefined),
            exito: mensaje.exito ?? (dataObj?.['exito'] as boolean | undefined)
          };

          if (accion === 'snapshot_guardado') {
            const exito = normalizado.exito !== false;
            this.ngZone.run(() => this._estadoGuardado$.next(exito ? 'guardado' : 'error'));
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

          this.ngZone.run(() => this._mensajes$.next(normalizado));
        },
        error: () => {
          this.ngZone.run(() => {
            this._estado$.next('error');
            this._estadoGuardado$.next('error');
          });
        }
      });
    });

    // Configurar el debounce de 2 segundos para guardar_snapshot
    this.snapshotSub = this._snapshotTrigger$.pipe(
      debounceTime(2000)
    ).subscribe((datos) => {
      this.enviarMensaje({ accion: 'guardar_snapshot', datos_diagrama: datos });
    });
  }

  public desconectar(): void {
    this.snapshotSub?.unsubscribe();
    this.subscription?.unsubscribe();
    this.socket$?.complete();
    this.socket$ = null;
    this._estado$.next('desconectado');
    this._usuariosConectados$.next([]);
  }

  public enviarRenombrarProyecto(nombre: string): void {
    this.enviarMensaje({ accion: 'renombrar_proyecto', nombre });
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
    this._estadoGuardado$.next('guardando');
    this._snapshotTrigger$.next(datos);
  }

  /** Fuerza el guardado inmediato del snapshot sin esperar el debounce */
  public forzarGuardarSnapshot(datos: Record<string, unknown>): void {
    this._estadoGuardado$.next('guardando');
    this.enviarMensaje({ accion: 'guardar_snapshot', datos_diagrama: datos });
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
