import {
  Component,
  OnInit,
  OnDestroy,
  AfterViewInit,
  ElementRef,
  ViewChild,
  inject,
  ChangeDetectorRef,
  HostListener
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { Subscription } from 'rxjs';

import { WhiteboardApiService } from '../../services/whiteboard-api.service';
import { WhiteboardSocketService } from '../../services/whiteboard-socket.service';
import { WhiteboardCanvasService } from '../../services/whiteboard-canvas.service';
import { WhiteboardEntityService } from '../../services/whiteboard-entity.service';
import { WhiteboardRelationshipService } from '../../services/whiteboard-relationship.service';
import { WhiteboardCameraService } from '../../services/whiteboard-camera.service';
import { DiagramaParserService } from '../../services/diagrama-parser.service';
import { AsistenteIaService } from '../../services/asistente-ia.service';
import { GeneradorService } from '../../services/generador.service';
import {
  RespuestaImportacionXML,
  SolicitudGeneracionSpring
} from '../../interfaces/generador.interface';
import { HallazgoValidacion } from '../../interfaces/validation.interface';
import { objetivoVisible } from '../../utils/validation.utils';
import {
  motivoBloqueoSpring,
  normalizarNombreProyectoSpring,
  puedeExportarSpring,
  puedeGenerarSpring
} from '../../utils/spring-generation.utils';

import { SidebarPizarraComponent } from '../../components/sidebar-pizarra/sidebar-pizarra.component';
import { ControlesZoomComponent } from '../../components/controles-zoom/controles-zoom.component';
import { MenuRelacionComponent } from '../../components/menu-relacion/menu-relacion.component';
import { MenuCardinalidadComponent } from '../../components/menu-cardinalidad/menu-cardinalidad.component';
import { EditorInlineComponent } from '../../components/editor-inline/editor-inline.component';
import { MenuContextualComponent } from '../../components/menu-contextual/menu-contextual.component';
import { ModalPropiedadesEntidadComponent } from '../../components/modal-propiedades-entidad/modal-propiedades-entidad.component';
import {
  ModalPropiedadesRelacionComponent,
  GuardarPropiedadesRelacionPayload
} from '../../components/modal-propiedades-relacion/modal-propiedades-relacion.component';
import { ModalColaboradoresComponent } from '../../components/modal-colaboradores/modal-colaboradores.component';
import { ChatAsistenteIaComponent } from '../../components/chat-asistente-ia/chat-asistente-ia.component';
import { ChatAgenteSeniorComponent } from '../../components/chat-agente-senior/chat-agente-senior.component';
import { ToastContainerComponent } from '../../../../shared/components/toast-container/toast-container.component';
import {
  ConfiguracionGeneracionSpring,
  ModalGeneracionSpringComponent
} from '../../components/modal-generacion-spring/modal-generacion-spring.component';
import { ToastNotificationService } from '../../../../core/services/toast-notification.service';
import { AuthService } from '../../../auth/services/auth.service';
import { TokenStorageService } from '../../../../core/services/token-storage.service';

import {
  DiagramaCargaInicial,
  EntidadDiagrama,
  RelacionDiagrama,
  ProyectoDiagrama,
  EstadoConexion,
  UsuarioConectado,
  MensajeWS
} from '../../interfaces/diagrama.interface';
import {
  TipoRelacionUML,
  GuardarEditorEvento,
  EventoContextualAccion,
  EventoSeleccionCardinalidad
} from '../../interfaces/whiteboard-ui.interface';
import {
  DiagramaGeneradoPayload,
  ContextoDiagramaIA,
  DeltaInstruccionIARespuesta
} from '../../interfaces/asistente-ia.interface';

@Component({
  selector: 'app-whiteboard-page',
  standalone: true,
  imports: [
    CommonModule,
    SidebarPizarraComponent,
    ChatAsistenteIaComponent,
    ChatAgenteSeniorComponent,
    ControlesZoomComponent,
    MenuRelacionComponent,
    MenuCardinalidadComponent,
    EditorInlineComponent,
    MenuContextualComponent,
    ModalPropiedadesEntidadComponent,
    ModalPropiedadesRelacionComponent,
    ModalColaboradoresComponent,
    ModalGeneracionSpringComponent,
    ToastContainerComponent
  ],
  providers: [
    WhiteboardCanvasService,
    WhiteboardEntityService,
    WhiteboardRelationshipService,
    WhiteboardCameraService
  ],
  templateUrl: './whiteboard.page.html',
  styleUrls: ['./whiteboard.page.css']
})
export class WhiteboardPage implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('lienzo', { static: true }) private lienzoRef!: ElementRef<HTMLDivElement>;

  private readonly route             = inject(ActivatedRoute);
  private readonly router            = inject(Router);
  private readonly apiService        = inject(WhiteboardApiService);
  public  readonly socketService     = inject(WhiteboardSocketService);
  public  readonly canvasService     = inject(WhiteboardCanvasService);
  private readonly asistenteIaService = inject(AsistenteIaService);
  private readonly parserService     = inject(DiagramaParserService);
  private readonly authService       = inject(AuthService);
  private readonly tokenStorage      = inject(TokenStorageService);
  private readonly toastService      = inject(ToastNotificationService);
  private readonly generadorService  = inject(GeneradorService);
  private readonly cdr               = inject(ChangeDetectorRef);

  private miUsuarioId: number | null = null;
  private proyectoId = 0;
  private subscriptions = new Subscription();
  private entidadesPendientes: EntidadDiagrama[] = [];
  private relacionesPendientes: RelacionDiagrama[] = [];

  // ── Estado del template ──
  public proyecto: ProyectoDiagrama | null = null;
  public estadoConexion: EstadoConexion = 'desconectado';
  public estadoGuardado: 'guardado' | 'guardando' | 'error' = 'guardado';
  public usuariosConectados: UsuarioConectado[] = [];
  public isLoading = true;
  public errorMessage: string | null = null;
  public modoOscuro = true;
  public zoomNivel = 100;
  public conflictoRevision: MensajeWS | null = null;
  public modalGeneracionActivo = false;
  public generandoSpring = false;
  public errorGeneracionSpring: string | null = null;
  private generacionSubscription: Subscription | null = null;

  // ── Estado Modales de Propiedades y Colaboradores ──
  public modalEntidadActivo = false;
  public entidadEditando: EntidadDiagrama | null = null;

  public modalRelacionActivo = false;
  public relacionEditando: RelacionDiagrama | null = null;
  public relacionNombreOrigen = 'Origen';
  public relacionNombreDestino = 'Destino';

  public modalColaboradoresActivo = false;

  public get puedeEditar(): boolean {
    return this.proyecto?.rol_usuario === 'propietario' || this.proyecto?.rol_usuario === 'editor';
  }

  public get puedeExportar(): boolean {
    return puedeExportarSpring(this.proyecto?.rol_usuario || '');
  }

  public get puedeGenerarSpring(): boolean {
    return puedeGenerarSpring(this.estadoActualGeneracion);
  }

  public get motivoBloqueoGeneracion(): string {
    return motivoBloqueoSpring(this.estadoActualGeneracion);
  }

  public get nombreInicialGeneracion(): string {
    return normalizarNombreProyectoSpring(this.proyecto?.nombre || '');
  }

  public get paqueteInicialGeneracion(): string {
    return this.proyecto?.paquete_base || '';
  }

  private get estadoActualGeneracion() {
    return {
      proyectoId: this.proyecto?.id ?? null,
      proyectoActivoId: this.proyectoId,
      rol: this.proyecto?.rol_usuario || '',
      conexion: this.estadoConexion,
      guardado: this.estadoGuardado,
      conflicto: !!this.conflictoRevision,
      generando: this.generandoSpring
    };
  }

  public onLocalizarHallazgo(hallazgo: HallazgoValidacion): void {
    const objetivo = objetivoVisible(hallazgo);
    if (!objetivo || !this.canvasService.enfocarObjetivo(objetivo.tipo, objetivo.id)) {
      this.toastService.info('El hallazgo no tiene un elemento visible en el lienzo.');
    }
  }

  // ── Ciclo de Vida ──

  public ngOnInit(): void {
    this.miUsuarioId = this.tokenStorage.getUser()?.id ?? null;
    const idParam = this.route.snapshot.paramMap.get('id');
    if (!idParam) {
      this.router.navigate(['/control']);
      return;
    }
    this.proyectoId = Number(idParam);
    this.cargarDiagrama();
  }

  public ngAfterViewInit(): void {
    this.canvasService.inicializar(this.lienzoRef.nativeElement);
    this.suscribirEventosCanvas();

    if (this.entidadesPendientes.length > 0) {
      this.canvasService.renderizarEntidades(this.entidadesPendientes);
      this.entidadesPendientes = [];
    }
    if (this.relacionesPendientes.length > 0) {
      this.canvasService.renderizarRelaciones(this.relacionesPendientes);
      this.relacionesPendientes = [];
    }
  }

  @HostListener('window:beforeunload')
  public onBeforeUnload(): void {
    if (this.puedeEditar && this.canvasService.estaListo) {
      const datos = this.canvasService.obtenerSnapshotDatos();
      this.socketService.forzarGuardarSnapshot(datos);
    }
  }

  public ngOnDestroy(): void {
    this.generacionSubscription?.unsubscribe();
    if (this.puedeEditar && this.canvasService.estaListo) {
      const datos = this.canvasService.obtenerSnapshotDatos();
      this.socketService.forzarGuardarSnapshot(datos);
    }
    this.canvasService.destruir();
    this.socketService.desconectar();
    this.subscriptions.unsubscribe();
  }

  // ── Carga y Sockets ──

  private cargarDiagrama(): void {
    this.isLoading = true;
    this.errorMessage = null;

    this.subscriptions.add(
      this.apiService.getDiagrama(this.proyectoId).subscribe({
        next: (datos: DiagramaCargaInicial) => {
          this.proyecto = datos.proyecto;
          this.socketService.establecerRevision(datos.proyecto.revision);
          this.canvasService.setSoloLectura(!this.puedeEditar);
          this.isLoading = false;
          this.cdr.detectChanges();

          if (this.canvasService.estaListo) {
            this.canvasService.renderizarEntidades(datos.entidades);
            this.canvasService.renderizarRelaciones(datos.relaciones);
          } else {
            this.entidadesPendientes = datos.entidades;
            this.relacionesPendientes = datos.relaciones;
          }

          this.socketService.conectar(this.proyectoId);
          this.suscribirEventosWS();
        },
        error: (err: HttpErrorResponse) => {
          this.isLoading = false;
          if      (err.status === 403) this.errorMessage = 'No tienes permisos para acceder a este proyecto.';
          else if (err.status === 404) this.errorMessage = 'El proyecto no existe.';
          else                         this.errorMessage = 'No se pudo cargar el diagrama. Verifique su conexión.';
          this.cdr.detectChanges();
        }
      })
    );
  }

  private suscribirEventosWS(): void {
    this.subscriptions.add(
      this.socketService.estado$.subscribe((estado: EstadoConexion) => {
        this.estadoConexion = estado;
        this.cdr.detectChanges();
      })
    );

    this.subscriptions.add(
      this.socketService.estadoGuardado$.subscribe(st => {
        this.estadoGuardado = st;
        this.cdr.detectChanges();
      })
    );

    this.subscriptions.add(
      this.socketService.conflicto$.subscribe(conflicto => {
        this.conflictoRevision = conflicto;
        this.cdr.detectChanges();
      })
    );

    this.subscriptions.add(
      this.socketService.usuariosConectados$.subscribe(usuarios => {
        this.usuariosConectados = usuarios;
        this.cdr.detectChanges();
      })
    );

    this.subscriptions.add(
      this.socketService.mensajes$.subscribe((msg: MensajeWS) => {
        const accion = msg.accion || msg.evento;

        if (accion === 'snapshot_guardado') {
          if (msg.exito !== false && msg.usuario_id === this.miUsuarioId && (msg.id_map || msg.rel_id_map || msg.attr_id_map || msg.operation_id_map || msg.parameter_id_map)) {
            this.canvasService.actualizarIdsSincronizados(msg.id_map, msg.rel_id_map, msg.attr_id_map, msg.operation_id_map, msg.parameter_id_map);
          }
          if (
            msg.exito !== false && msg.usuario_id !== this.miUsuarioId &&
            this.estadoGuardado === 'guardado'
          ) {
            this.recargarEstadoConfirmado();
          }
          return;
        }

        if (accion === 'proyecto_renombrado') {
          if (msg.nombre && this.proyecto) {
            this.proyecto.nombre = msg.nombre;
            this.cdr.detectChanges();
          }
          return;
        }

        if (accion === 'diagram.updated') {
          if (msg.usuario_id !== this.miUsuarioId && this.estadoGuardado === 'guardado') {
            this.recargarEstadoConfirmado();
          }
          return;
        }

        if (accion === 'access.revoked') {
          this.generacionSubscription?.unsubscribe();
          this.generacionSubscription = null;
          this.generandoSpring = false;
          this.modalGeneracionActivo = false;
          this.errorMessage = 'Tu acceso a este proyecto fue revocado.';
          this.socketService.desconectar();
          this.cdr.detectChanges();
          return;
        }

        if (this.miUsuarioId && msg.usuario_id === this.miUsuarioId) return;

        switch (accion) {
          case 'mover_entidad':
          case 'entidad_movida':
            this.canvasService.moverCeldaRemota(msg.entidad_id, msg.x, msg.y);
            break;
          case 'bloquear_entidad':
          case 'entidad_bloqueada':
            this.canvasService.setBloqueoEntidad(msg.entidad_id, true);
            break;
          case 'desbloquear_entidad':
          case 'entidad_desbloqueada':
            this.canvasService.setBloqueoEntidad(msg.entidad_id, false);
            break;
          case 'crear_entidad':
          case 'entidad_creada':
            if (msg.entidad) this.canvasService.crearCeldaRemota(msg.entidad);
            break;
          case 'actualizar_entidad':
          case 'entidad_actualizada':
            if (msg.entidad) this.canvasService.actualizarCeldaRemota(msg.entidad);
            break;
          case 'eliminar_entidad':
          case 'entidad_eliminada':
            if (msg.entidad_id !== undefined) this.canvasService.eliminarCeldaRemota(msg.entidad_id);
            break;
          case 'crear_relacion':
          case 'relacion_creada':
            if (msg.relacion) this.canvasService.crearRelacionRemota(msg.relacion);
            break;
          case 'actualizar_relacion':
          case 'relacion_actualizada':
            if (msg.relacion) this.canvasService.actualizarRelacionRemota(msg.relacion);
            break;
          case 'eliminar_relacion':
          case 'relacion_eliminada':
            if (msg.relacion_id !== undefined) this.canvasService.eliminarRelacionRemota(msg.relacion_id);
            break;
        }
      })
    );
  }

  private suscribirEventosCanvas(): void {
    this.subscriptions.add(this.canvasService.zoomNivel$.subscribe(nivel => { this.zoomNivel = nivel; this.cdr.markForCheck(); }));
    this.subscriptions.add(this.canvasService.solicitudActualizarRelacion$.subscribe(rel => {
      if (!this.puedeEditar) return;
      this.socketService.enviarActualizarRelacion(rel);
      this.programarSnapshot();
    }));
    this.subscriptions.add(this.canvasService.solicitudEliminarRelacion$.subscribe(id => {
      if (this.puedeEditar) this.socketService.enviarEliminarRelacion(id);
    }));
    this.subscriptions.add(this.canvasService.bloquearEntidadLocal$.subscribe(id => {
      if (this.puedeEditar) this.socketService.enviarBloquearEntidad(id);
    }));
    this.subscriptions.add(this.canvasService.moverEntidadLocal$.subscribe(ev => {
      if (this.puedeEditar) this.socketService.enviarMoverEntidad(ev.entidadId, ev.x, ev.y);
    }));
    this.subscriptions.add(this.canvasService.moverEntidadFinLocal$.subscribe(ev => {
      if (!this.puedeEditar) return;
      this.socketService.enviarMoverEntidad(ev.entidadId, ev.x, ev.y);
      this.programarSnapshot();
    }));
    this.subscriptions.add(this.canvasService.desbloquearEntidadLocal$.subscribe(id => {
      if (this.puedeEditar) this.socketService.enviarDesbloquearEntidad(id);
    }));
    this.subscriptions.add(this.canvasService.snapshotRequerido$.subscribe(() => {
      if (this.puedeEditar) this.programarSnapshot();
    }));
    this.subscriptions.add(this.canvasService.cerrarModales$.subscribe(() => this.cerrarTodosModales()));
  }

  private recargarEstadoConfirmado(): void {
    this.apiService.getDiagrama(this.proyectoId).subscribe({
      next: datos => {
        this.proyecto = datos.proyecto;
        this.socketService.establecerRevision(datos.proyecto.revision);
        this.canvasService.limpiar();
        this.canvasService.renderizarEntidades(datos.entidades);
        this.canvasService.renderizarRelaciones(datos.relaciones);
        this.cdr.detectChanges();
      },
      error: () => this.toastService.error('No se pudo recuperar el estado confirmado del diagrama.')
    });
  }

  // ── Guardado de Editor Inline ──

  public onGuardarEditor(evento: GuardarEditorEvento): void {
    if (!this.puedeEditar) return;
    if (evento.tipo === 'nombre_relacion' && evento.relacionId !== null) {
      const relActualizada = this.canvasService.actualizarNombreRelacion(evento.relacionId, evento.valor);
      if (relActualizada) {
        this.socketService.enviarActualizarRelacion(relActualizada);
        this.programarSnapshot();
      }
      return;
    }

    if (evento.entidadId === null) return;
    const entidad = this.canvasService.getEntidad(evento.entidadId);
    if (!entidad) return;

    let encadenarSiguiente = false;
    const valor = evento.valor;

    if (evento.tipo === 'nombre') {
      entidad.nombre = valor;
      this.canvasService.actualizarEntidadLocal(entidad);
      this.socketService.enviarActualizarEntidad(entidad);
      if (evento.encadenar && valor.length > 0 && (!entidad.atributos || entidad.atributos.length === 0)) {
        encadenarSiguiente = true;
      }
    } else if (evento.tipo === 'nuevo_atributo' && valor.length > 0) {
      const nuevoOrden = (entidad.atributos?.length ?? 0) + 1;
      const nuevoAttr = this.parserService.parsearAtributoTexto(valor, nuevoOrden, this.socketService.generarIdTemporal());
      if (!entidad.atributos) entidad.atributos = [];
      entidad.atributos.push(nuevoAttr);
      this.canvasService.actualizarEntidadLocal(entidad);
      this.socketService.enviarActualizarEntidad(entidad);
      encadenarSiguiente = evento.encadenar;
    } else if (evento.tipo === 'editar_atributo' && evento.atributoIndex !== null && entidad.atributos) {
      if (valor.length > 0) {
        const actual = entidad.atributos[evento.atributoIndex];
        entidad.atributos[evento.atributoIndex] = this.parserService.parsearAtributoTexto(valor, actual.orden, actual.id, actual.es_nulo);
      } else {
        entidad.atributos.splice(evento.atributoIndex, 1);
        entidad.atributos.forEach((a, i) => a.orden = i + 1);
      }
      this.canvasService.actualizarEntidadLocal(entidad);
      this.socketService.enviarActualizarEntidad(entidad);
    }

    this.programarSnapshot();

    if (encadenarSiguiente && evento.entidadId !== null) {
      setTimeout(() => this.canvasService.solicitudEditorNuevoAtributo$.next(evento.entidadId!), 40);
    }
  }

  // ── Selección de Relación y Cardinalidad ──

  public confirmarTipoRelacion(tipo: TipoRelacionUML): void {
    if (!this.puedeEditar) return;
    const res = this.canvasService.confirmarTipoRelacion(
      tipo,
      this.socketService.generarIdTemporal(),
      this.socketService.generarIdTemporal(),
      this.socketService.generarIdTemporal()
    );
    if (res) {
      if (res.entidadIntermedia) {
        this.socketService.enviarCrearEntidad(res.entidadIntermedia);
      }
      for (const rel of res.relaciones) {
        this.socketService.enviarCrearRelacion(rel);
      }
      this.programarSnapshot();
    }
  }

  public seleccionarCardinalidad(ev: EventoSeleccionCardinalidad): void {
    if (!this.puedeEditar) return;
    const relActualizada = this.canvasService.aplicarCardinalidad(
      ev.relacionId,
      ev.extremo,
      ev.valor
    );
    if (relActualizada) {
      this.socketService.enviarActualizarRelacion(relActualizada);
      this.programarSnapshot();
    }
  }

  // ── Manejo de Menú Contextual ──

  public onAbrirPropiedadesContextual(ev: EventoContextualAccion): void {
    if (!this.puedeEditar) return;
    if (ev.tipo === 'entidad') {
      const entidad = this.canvasService.getEntidad(ev.id);
      if (entidad) {
        this.entidadEditando = JSON.parse(JSON.stringify(entidad));
        this.modalEntidadActivo = true;
      }
    } else {
      const rel = this.canvasService.getRelacion(ev.id);
      if (rel) {
        this.relacionEditando = { ...rel };
        const entOrigen = this.canvasService.getEntidad(rel.entidad_origen_id);
        const entDestino = this.canvasService.getEntidad(rel.entidad_destino_id);
        this.relacionNombreOrigen = entOrigen?.nombre || `Entidad #${rel.entidad_origen_id}`;
        this.relacionNombreDestino = entDestino?.nombre || `Entidad #${rel.entidad_destino_id}`;
        this.modalRelacionActivo = true;
      }
    }
    this.cdr.detectChanges();
  }

  public onAgregarEtiquetaContextual(ev: EventoContextualAccion): void {
    if (!this.puedeEditar) return;
    if (ev.tipo === 'relacion') {
      const pos = this.canvasService.obtenerPosicionEditorNombreRelacion(ev.id);
      if (pos) {
        this.canvasService.solicitudEditorNombreRelacion$.next({ relacionId: ev.id, pos });
      }
    }
  }

  public onEliminarContextual(ev: EventoContextualAccion): void {
    if (!this.puedeEditar) return;
    if (ev.tipo === 'entidad') {
      this.canvasService.eliminarCeldaRemota(ev.id);
      this.socketService.enviarEliminarEntidad(ev.id);
      this.programarSnapshot();
    } else {
      this.canvasService.eliminarRelacionRemota(ev.id);
      this.socketService.enviarEliminarRelacion(ev.id);
      this.programarSnapshot();
    }
  }

  // ── Modales de Propiedades y Colaboradores ──

  public onGuardarPropiedadesEntidad(entidadActualizada: EntidadDiagrama): void {
    if (!this.puedeEditar) return;
    this.canvasService.actualizarEntidadLocal(entidadActualizada);
    this.socketService.enviarActualizarEntidad(entidadActualizada);
    this.programarSnapshot();
    this.modalEntidadActivo = false;
    this.entidadEditando = null;
    this.cdr.detectChanges();
  }

  public onCancelarModalEntidad(): void {
    this.modalEntidadActivo = false;
    this.entidadEditando = null;
    this.cdr.detectChanges();
  }

  public onGuardarPropiedadesRelacion(datos: GuardarPropiedadesRelacionPayload): void {
    if (!this.puedeEditar) return;
    const relActualizada = this.canvasService.actualizarPropiedadesRelacion(
      datos.relacionId,
      datos.nombre,
      datos.cardinalidadOrigen,
      datos.cardinalidadDestino,
      { tipo: datos.tipo, rol_origen: datos.rolOrigen, rol_destino: datos.rolDestino,
        navegable_origen: datos.navegableOrigen, navegable_destino: datos.navegableDestino }
    );
    if (relActualizada) {
      this.socketService.enviarActualizarRelacion(relActualizada);
      this.programarSnapshot();
    }
    this.modalRelacionActivo = false;
    this.relacionEditando = null;
    this.cdr.detectChanges();
  }

  public onCancelarModalRelacion(): void {
    this.modalRelacionActivo = false;
    this.relacionEditando = null;
    this.cdr.detectChanges();
  }

  public onEliminarRelacionDesdeModal(relacionId: number): void {
    if (!this.puedeEditar) return;
    this.canvasService.eliminarRelacionRemota(relacionId);
    this.socketService.enviarEliminarRelacion(relacionId);
    this.modalRelacionActivo = false;
    this.relacionEditando = null;
    this.programarSnapshot();
    this.toastService.info('Relación eliminada correctamente.');
    this.cdr.detectChanges();
  }

  public onAbrirColaboradores(): void {
    this.modalColaboradoresActivo = true;
    this.cdr.detectChanges();
  }

  public onCerrarColaboradores(): void {
    this.modalColaboradoresActivo = false;
    this.cdr.detectChanges();
  }

  public onCancelarTipoRelacion(): void {
    this.canvasService.cancelarRelacionPendiente();
  }

  private cerrarTodosModales(): void {
    this.canvasService.cerrarModales$.next();
    this.canvasService.cancelarRelacionPendiente();
    this.modalEntidadActivo = false;
    this.modalRelacionActivo = false;
    this.modalColaboradoresActivo = false;
    this.cdr.detectChanges();
  }

  @HostListener('document:keydown.escape', ['$event'])
  public onKeydownEscape(evt: KeyboardEvent): void {
    evt.preventDefault();
    this.cerrarTodosModales();
    this.canvasService.deseleccionarEnlace();
  }

  @HostListener('document:keydown', ['$event'])
  public onKeydownGlobal(evt: KeyboardEvent): void {
    if (!this.puedeEditar) return;
    if (evt.key === 'Delete' || evt.key === 'Backspace') {
      const activeTag = (document.activeElement?.tagName || '').toLowerCase();
      if (activeTag === 'input' || activeTag === 'textarea' || (document.activeElement as HTMLElement)?.isContentEditable) {
        return;
      }
      if (this.modalEntidadActivo || this.modalRelacionActivo || this.modalColaboradoresActivo) {
        return;
      }
      const relSeleccionadaId = this.canvasService.getRelacionSeleccionadaId();
      if (relSeleccionadaId !== null) {
        evt.preventDefault();
        this.canvasService.eliminarRelacionRemota(relSeleccionadaId);
        this.socketService.enviarEliminarRelacion(relSeleccionadaId);
        this.programarSnapshot();
        this.toastService.info('Relación eliminada.');
        this.cdr.detectChanges();
      }
    }
  }

  // ── Acciones Generales y de Barra Lateral ──

  public onAgregarEntidad(): void {
    if (!this.puedeEditar) return;
    const centro = this.canvasService.calcularCentroVisible();
    const offset = (this.canvasService.getCantidadEntidades() % 6) * 36;
    const nueva = this.canvasService.crearEntidadLocal(
      centro.x - 110 + offset,
      centro.y - 30 + offset,
      this.socketService.generarIdTemporal()
    );
    this.socketService.enviarCrearEntidad(nueva);
    this.canvasService.solicitudEditorNombre$.next(nueva.id);
  }

  public onAgregarClaseAsociacion(): void {
    if (!this.puedeEditar) return;
    this.toastService.info('Para modelar una Clase de Asociación (N:M): traza un enlace entre dos tablas y selecciona "Clase de Asociación (N:M)" en el menú.');
  }

  public onAgregarNota(): void {
    if (!this.puedeEditar) return;
    const centro = this.canvasService.calcularCentroVisible();
    const offset = (this.canvasService.getCantidadEntidades() % 6) * 36;
    const nueva = this.canvasService.crearEntidadLocal(
      centro.x - 110 + offset,
      centro.y - 30 + offset,
      this.socketService.generarIdTemporal()
    );
    nueva.nombre = 'Nota / Comentario';
    this.canvasService.actualizarEntidadLocal(nueva);
    this.socketService.enviarCrearEntidad(nueva);
    this.canvasService.solicitudEditorNombre$.next(nueva.id);
  }

  public onRenombrarProyecto(nuevoNombre: string): void {
    if (!this.puedeEditar) return;
    if (!this.proyecto || !nuevoNombre.trim()) return;
    const nombreLimpio = nuevoNombre.trim();
    this.proyecto.nombre = nombreLimpio;
    this.socketService.enviarRenombrarProyecto(nombreLimpio);
    this.toastService.info(`Guardando el nombre "${nombreLimpio}"...`);
  }

  public onGenerarCodigo(): void {
    this.errorGeneracionSpring = null;
    this.modalGeneracionActivo = true;
  }

  public onCerrarGeneracion(): void {
    this.generacionSubscription?.unsubscribe();
    this.generacionSubscription = null;
    this.generandoSpring = false;
    this.modalGeneracionActivo = false;
  }

  public onGuardarAntesDeGenerar(): void {
    if (!this.puedeEditar || !this.canvasService.estaListo || this.conflictoRevision) return;
    if (this.estadoGuardado === 'guardando') {
      this.toastService.info('El autoguardado ya está esperando confirmación del servidor.');
      return;
    }
    this.socketService.forzarGuardarSnapshot(this.canvasService.obtenerSnapshotDatos());
  }

  public onSolicitarGeneracion(configuracion: ConfiguracionGeneracionSpring): void {
    if (!this.puedeGenerarSpring || !this.proyecto) {
      this.errorGeneracionSpring = this.motivoBloqueoGeneracion || 'No se puede generar en este momento.';
      return;
    }
    const capturedProjectId = this.proyectoId;
    const capturedRevision = this.socketService.revisionActual;
    const request: SolicitudGeneracionSpring = {
      expected_revision: capturedRevision,
      nombre_proyecto: configuracion.nombre_proyecto,
      paquete_base: configuracion.paquete_base,
      opciones: { ...configuracion.opciones }
    };
    this.generandoSpring = true;
    this.errorGeneracionSpring = null;
    this.generacionSubscription?.unsubscribe();
    this.generacionSubscription = this.generadorService
      .generarSpringBoot(capturedProjectId, request)
      .subscribe({
        next: async response => {
          if (this.proyectoId !== capturedProjectId || this.socketService.revisionActual !== capturedRevision) {
            this.generandoSpring = false;
            return;
          }
          try {
            const prepared = await this.generadorService.prepararDescargaSpring(
              response, configuracion.nombre_proyecto
            );
            if (this.proyectoId !== capturedProjectId || this.socketService.revisionActual !== capturedRevision) return;
            this.generadorService.iniciarDescarga(prepared);
            this.toastService.exito(`Proyecto ${prepared.filename} generado y descargado.`);
            this.modalGeneracionActivo = false;
          } catch (error) {
            this.errorGeneracionSpring = error instanceof Error
              ? error.message : 'La respuesta de generación no es un ZIP válido.';
          } finally {
            this.generandoSpring = false;
            this.cdr.detectChanges();
          }
        },
        error: async (error: HttpErrorResponse) => {
          if (this.proyectoId !== capturedProjectId || this.socketService.revisionActual !== capturedRevision) return;
          const parsed = await this.generadorService.leerErrorGeneracion(error);
          if (parsed.code === 'stale_revision') {
            this.socketService.registrarConflictoRevision(parsed.current_revision, parsed.message);
          }
          this.errorGeneracionSpring = this.generadorService.describirErrorGeneracion(parsed);
          this.generandoSpring = false;
          this.cdr.detectChanges();
        }
      });
    this.subscriptions.add(this.generacionSubscription);
  }

  // ── Integración Asistente IA ──

  public onDiagramaIAGenerado(payload: DiagramaGeneradoPayload): void {
    if (!this.puedeEditar) return;
    if (!this.canvasService.estaListo) return;

    const centro = this.canvasService.calcularCentroVisible();
    const cantExistente = this.canvasService.getCantidadEntidades();
    const payloadPosicionado = this.asistenteIaService.posicionarDiagramaGenerado(payload, centro, cantExistente);

    for (const ent of payloadPosicionado.entidades) {
      this.canvasService.crearCeldaRemota(ent);
      this.socketService.enviarCrearEntidad(ent);
    }
    for (const rel of payloadPosicionado.relaciones) {
      this.canvasService.crearRelacionRemota(rel);
      this.socketService.enviarCrearRelacion(rel);
    }

    this.programarSnapshot();
  }

  public obtenerContextoDiagramaParaIA(): ContextoDiagramaIA {
    if (!this.canvasService.estaListo) {
      return { entidades: [], relaciones: [] };
    }
    return this.asistenteIaService.extraerContextoDiagrama(
      this.canvasService.getEntidades(),
      this.canvasService.getRelaciones()
    );
  }

  public onEjecutarDeltaIA(delta: DeltaInstruccionIARespuesta): void {
    if (!this.puedeEditar) return;
    if (!this.canvasService.estaListo) return;

    const res = this.asistenteIaService.procesarDelta(
      delta,
      (id: number) => this.canvasService.getEntidad(id),
      this.canvasService.calcularCentroVisible(),
      this.canvasService.getCantidadEntidades(),
      () => this.socketService.generarIdTemporal(),
      this.canvasService.getEntidades()
    );

    for (const ent of res.entidadesACrear) {
      this.canvasService.crearCeldaRemota(ent);
      this.socketService.enviarCrearEntidad(ent);
    }
    for (const ent of res.entidadesAModificar) {
      this.canvasService.actualizarEntidadLocal(ent);
      this.socketService.enviarActualizarEntidad(ent);
    }
    for (const id of res.entidadesAEliminar) {
      this.canvasService.eliminarCeldaRemota(id);
      this.socketService.enviarEliminarEntidad(id);
    }
    for (const rel of res.relacionesACrear) {
      this.canvasService.crearRelacionRemota(rel);
      this.socketService.enviarCrearRelacion(rel);
    }
    for (const id of res.relacionesAEliminar) {
      this.canvasService.eliminarRelacionRemota(id);
      this.socketService.enviarEliminarRelacion(id);
    }

    this.programarSnapshot();
  }

  public onExportarImagen(): void {
    this.toastService.info('Exportación de diagrama en formato PNG/PDF disponible próximamente en Fase 2.');
  }

  public onExportarXml(): void {
    if (!this.proyectoId) return;
    this.toastService.info('Generando y descargando XML 2.1 estándar OMG para Enterprise Architect...');
    const codigo = this.proyecto?.codigo || `PROJ_${this.proyectoId}`;
    this.generadorService.descargarArchivoXML(this.proyectoId, codigo);
  }

  public onImportarXml(archivo: File): void {
    if (!this.puedeEditar) return;
    if (!this.proyectoId || !archivo) return;
    this.toastService.info(`Importando archivo ${archivo.name}...`);
    this.generadorService.importarDiagramaXML(
      this.proyectoId, archivo, this.socketService.revisionActual, true
    ).subscribe({
      next: (resp: RespuestaImportacionXML) => {
        this.socketService.establecerRevision(resp.revision);
        const m = resp.metricas;
        const persistencia = m.entidades_persistentes
          ? ` ${m.entidades_persistentes} entidades quedaron preparadas para Spring Boot.`
          : '';
        const duplicadosOmitidos = m.clasificadores_duplicados_omitidos
          ? ` Se omitieron ${m.clasificadores_duplicados_omitidos} copias ocultas sin referencias.`
          : '';
        this.toastService.exito(
          `¡Diagrama importado! Se crearon ${m.entidades_creadas} entidades, ${m.atributos_creados} atributos y ${m.relaciones_creadas} relaciones.${persistencia}${duplicadosOmitidos}`
        );
        this.recargarEstadoConfirmado();
      },
      error: (err: HttpErrorResponse) => {
        if (err.status === 409 && err.error?.code === 'stale_revision') {
          this.socketService.registrarConflictoRevision(
            err.error?.current_revision, err.error?.message
          );
        }
        const msg = err.error?.detail || err.error?.message || 'Error al importar archivo XML 2.1.';
        this.toastService.error(msg);
      }
    });
  }

  // ── Drag & Drop de Elementos al Lienzo ──

  public onDragOverLienzo(evt: DragEvent): void {
    if (!this.puedeEditar) return;
    evt.preventDefault();
    if (evt.dataTransfer) {
      evt.dataTransfer.dropEffect = 'copy';
    }
  }

  public onDropLienzo(evt: DragEvent): void {
    if (!this.puedeEditar) return;
    evt.preventDefault();
    const rawData = evt.dataTransfer?.getData('application/json');
    let tipo = evt.dataTransfer?.getData('text/plain') || 'entidad';
    if (rawData) {
      try {
        const parsed = JSON.parse(rawData);
        tipo = parsed.tipo || tipo;
      } catch {
        // fallback
      }
    }

    const localPt = this.canvasService.clientToLocalPoint(evt.clientX, evt.clientY);

    if (tipo === 'entidad') {
      const nueva = this.canvasService.crearEntidadLocal(
        localPt.x,
        localPt.y,
        this.socketService.generarIdTemporal()
      );
      this.socketService.enviarCrearEntidad(nueva);
      this.canvasService.solicitudEditorNombre$.next(nueva.id);
    } else if (tipo === 'clase_asociacion') {
      this.onAgregarClaseAsociacion();
    } else if (tipo === 'nota') {
      const nueva = this.canvasService.crearEntidadLocal(
        localPt.x,
        localPt.y,
        this.socketService.generarIdTemporal()
      );
      nueva.nombre = 'Nota / Comentario';
      this.canvasService.actualizarEntidadLocal(nueva);
      this.socketService.enviarCrearEntidad(nueva);
      this.canvasService.solicitudEditorNombre$.next(nueva.id);
    }
  }

  // ── Controles de Vista y Navegación ──

  public onToggleTema(): void {
    this.modoOscuro = !this.modoOscuro;
    this.canvasService.setModoOscuro(this.modoOscuro);
  }

  public onZoomIn(): void { this.canvasService.zoomIn(); }
  public onZoomOut(): void { this.canvasService.zoomOut(); }
  public onZoomReset(): void { this.canvasService.zoomReset(); }

  public onRecargarTrasConflicto(): void {
    const acepta = window.confirm(
      'Recargar descartará los cambios locales no confirmados. ¿Deseas recuperar el estado remoto?'
    );
    if (!acepta) return;
    this.socketService.descartarCambiosLocalesEnConflicto();
    window.location.reload();
  }

  public onCerrarSesion(): void {
    if (this.puedeEditar && this.canvasService.estaListo) {
      const datos = this.canvasService.obtenerSnapshotDatos();
      this.socketService.forzarGuardarSnapshot(datos);
    }
    this.socketService.desconectar();
    this.authService.logout().subscribe();
  }

  public onVolverDashboard(): void {
    if (this.puedeEditar && this.canvasService.estaListo) {
      const datos = this.canvasService.obtenerSnapshotDatos();
      this.socketService.forzarGuardarSnapshot(datos);
    }
    this.socketService.desconectar();
    this.router.navigate(['/control']);
  }

  private programarSnapshot(): void {
    if (!this.puedeEditar) return;
    const datos = this.canvasService.obtenerSnapshotDatos();
    this.socketService.programarGuardarSnapshot(datos);
  }
}
