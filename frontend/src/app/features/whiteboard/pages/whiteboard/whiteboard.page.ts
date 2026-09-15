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
import { ToastContainerComponent } from '../../../../shared/components/toast-container/toast-container.component';
import { ToastNotificationService } from '../../../../core/services/toast-notification.service';
import { AuthService } from '../../../auth/services/auth.service';
import { TokenStorageService } from '../../../../core/services/token-storage.service';
import {
  DiagramaCargaInicial,
  EntidadDiagrama,
  AtributoDiagrama,
  RelacionDiagrama,
  ProyectoDiagrama,
  EstadoConexion,
  UsuarioConectado,
  MensajeWS
} from '../../interfaces/diagrama.interface';
import {
  OpcionRelacion,
  TipoRelacionUML,
  CardinalidadEditando,
  PosicionEditor,
  TipoEditor,
  GuardarEditorPayload
} from '../../interfaces/whiteboard-ui.interface';

@Component({
  selector: 'app-whiteboard-page',
  standalone: true,
  imports: [
    CommonModule,
    SidebarPizarraComponent,
    ControlesZoomComponent,
    MenuRelacionComponent,
    MenuCardinalidadComponent,
    EditorInlineComponent,
    MenuContextualComponent,
    ModalPropiedadesEntidadComponent,
    ModalPropiedadesRelacionComponent,
    ModalColaboradoresComponent,
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

  private readonly route         = inject(ActivatedRoute);
  private readonly router        = inject(Router);
  private readonly apiService    = inject(WhiteboardApiService);
  private readonly socketService = inject(WhiteboardSocketService);
  public  readonly canvasService = inject(WhiteboardCanvasService);
  private readonly parserService = inject(DiagramaParserService);
  private readonly authService   = inject(AuthService);
  private readonly tokenStorage  = inject(TokenStorageService);
  private readonly toastService  = inject(ToastNotificationService);
  private readonly cdr           = inject(ChangeDetectorRef);

  private miUsuarioId: number | null = null;
  private proyectoId = 0;
  private contadorSesion = 0;
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
  public modoOscuro = false;
  public zoomNivel = 100;

  // ── Estado de Editores y Modales Flotantes ──
  public editorActivo = false;
  public editorTipo: TipoEditor = 'nombre';
  public editorValor = '';
  public editorPlaceholder = '';
  public editorPos: PosicionEditor = { x: 0, y: 0, w: 0, h: 0 };
  private editorEntidadId: number | null = null;
  private editorAtributoIndex: number | null = null;
  private editorRelacionId: number | null = null;

  public menuRelacionActivo = false;
  public menuRelacionPos = { x: 0, y: 0 };

  public menuCardinalidadActivo = false;
  public menuCardinalidadPos = { x: 0, y: 0 };
  public cardinalidadEditando: CardinalidadEditando | null = null;

  // ── Estado Menú Contextual y Modales de Propiedades ──
  public menuContextualActivo = false;
  public menuContextualPos: { x: number; y: number } = { x: 0, y: 0 };
  public menuContextualTipo: 'entidad' | 'relacion' = 'entidad';
  public menuContextualId: number | null = null;
  public menuContextualTitulo = '';

  public modalEntidadActivo = false;
  public entidadEditando: EntidadDiagrama | null = null;

  public modalRelacionActivo = false;
  public relacionEditando: RelacionDiagrama | null = null;
  public relacionNombreOrigen = 'Origen';
  public relacionNombreDestino = 'Destino';

  public modalColaboradoresActivo = false;

  public readonly OPCIONES_CARDINALIDAD: string[] = ['1', '0..1', '1..*', '0..*', '*'];
  public readonly TIPOS_BACKEND: AtributoDiagrama['tipo'][] = ['string', 'integer', 'long', 'double', 'boolean', 'date'];
  public readonly OPCIONES_RELACIONES: OpcionRelacion[] = [
    { tipo: 'asociacion', nombre: 'Asociación', subtitulo: 'Línea sólida continua entre tablas', svgIcon: 'asociacion' },
    { tipo: 'agregacion', nombre: 'Agregación', subtitulo: 'Contenedor débil (rombo hueco)', svgIcon: 'agregacion' },
    { tipo: 'composicion', nombre: 'Composición', subtitulo: 'Contenedor fuerte (rombo lleno)', svgIcon: 'composicion' },
    { tipo: 'herencia', nombre: 'Herencia (Generalización)', subtitulo: 'Especialización de tablas', svgIcon: 'herencia' },
    { tipo: 'clase_asociacion', nombre: 'Clase de Asociación (N:M)', subtitulo: 'Enlace principal sólido (0..* a 0..*) con clase flotante punteada', svgIcon: 'clase_asociacion' }
  ];

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
    if (this.canvasService.estaListo) {
      const datos = this.canvasService.obtenerSnapshotDatos();
      this.socketService.forzarGuardarSnapshot(datos);
    }
  }

  public ngOnDestroy(): void {
    if (this.canvasService.estaListo) {
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
          this.isLoading = false;
          this.cdr.detectChanges();

          const snapshotRelaciones = (datos.proyecto?.datos_diagrama as Record<string, unknown>)?.['relaciones'] as RelacionDiagrama[] | undefined;
          const snapshotMap = new Map<number, RelacionDiagrama>();
          if (snapshotRelaciones && Array.isArray(snapshotRelaciones)) {
            snapshotRelaciones.forEach(r => snapshotMap.set(r.id, r));
          }

          const relacionesFinales: RelacionDiagrama[] = [];
          const idsAgregados = new Set<number>();

          (datos.relaciones || []).forEach(r => {
            const deSnapshot = snapshotMap.get(r.id);
            const tipo = r.tipo;
            idsAgregados.add(r.id);
            relacionesFinales.push({
              ...r,
              nombre_relacion: r.nombre_relacion || deSnapshot?.nombre_relacion || '',
              clase_asociacion_id: r.clase_asociacion_id ?? deSnapshot?.clase_asociacion_id ?? null,
              puerto_origen: r.puerto_origen || deSnapshot?.puerto_origen,
              puerto_destino: r.puerto_destino || deSnapshot?.puerto_destino,
              vertices: r.vertices ?? deSnapshot?.vertices ?? [],
              cardinalidad_origen: r.cardinalidad_origen || deSnapshot?.cardinalidad_origen || (tipo !== 'herencia' ? '1' : ''),
              cardinalidad_destino: r.cardinalidad_destino || deSnapshot?.cardinalidad_destino || (tipo !== 'herencia' ? '0..*' : ''),
              origen_bloqueado: r.origen_bloqueado ?? deSnapshot?.origen_bloqueado ?? (tipo === 'composicion')
            });
          });

          if (snapshotRelaciones && Array.isArray(snapshotRelaciones)) {
            snapshotRelaciones.forEach(r => {
              if (r && r.id && !idsAgregados.has(r.id)) {
                idsAgregados.add(r.id);
                relacionesFinales.push(r);
              }
            });
          }

          if (this.canvasService.estaListo) {
            this.canvasService.renderizarEntidades(datos.entidades);
            this.canvasService.renderizarRelaciones(relacionesFinales);
          } else {
            this.entidadesPendientes = datos.entidades;
            this.relacionesPendientes = relacionesFinales;
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
      this.socketService.usuariosConectados$.subscribe(usuarios => {
        this.usuariosConectados = usuarios;
        this.cdr.detectChanges();
      })
    );

    this.subscriptions.add(
      this.socketService.mensajes$.subscribe((msg: MensajeWS) => {
        const accion = msg.accion || msg.evento;

        if (accion === 'snapshot_guardado') {
          if (msg.id_map || msg.rel_id_map) {
            this.canvasService.actualizarIdsSincronizados(msg.id_map, msg.rel_id_map);

            if (this.editorEntidadId !== null && msg.id_map && msg.id_map[this.editorEntidadId] !== undefined) {
              this.editorEntidadId = msg.id_map[this.editorEntidadId];
            }
            if (this.editorRelacionId !== null && msg.rel_id_map && msg.rel_id_map[this.editorRelacionId] !== undefined) {
              this.editorRelacionId = msg.rel_id_map[this.editorRelacionId];
            }
            if (this.menuContextualId !== null) {
              if (this.menuContextualTipo === 'entidad' && msg.id_map && msg.id_map[this.menuContextualId] !== undefined) {
                this.menuContextualId = msg.id_map[this.menuContextualId];
              } else if (this.menuContextualTipo === 'relacion' && msg.rel_id_map && msg.rel_id_map[this.menuContextualId] !== undefined) {
                this.menuContextualId = msg.rel_id_map[this.menuContextualId];
              }
            }
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

        if (this.miUsuarioId && msg.usuario_id === this.miUsuarioId) return;

        switch (accion) {
          case 'mover_entidad':
          case 'entidad_movida':
            this.canvasService.moverCeldaRemota(msg.entidad_id, msg.x, msg.y);
            break;
          case 'bloquear_entidad':
          case 'entidad_bloqueada':
            this.canvasService.cambiarBorde(msg.entidad_id, this.canvasService.tema.bloqueadoBorde);
            break;
          case 'desbloquear_entidad':
          case 'entidad_desbloqueada':
            this.canvasService.cambiarBorde(msg.entidad_id, this.canvasService.tema.entidadBorde);
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
    this.subscriptions.add(this.canvasService.zoomNivel$.subscribe(nivel => { this.zoomNivel = nivel; this.cdr.detectChanges(); }));
    this.subscriptions.add(this.canvasService.solicitudRelacion$.subscribe(ev => {
      this.menuRelacionPos = ev.pos;
      this.menuRelacionActivo = true;
      this.cdr.detectChanges();
    }));
    this.subscriptions.add(this.canvasService.solicitudCardinalidad$.subscribe(ev => {
      this.cardinalidadEditando = { relacionId: ev.relacionId, extremo: ev.extremo, valorActual: ev.valorActual };
      this.menuCardinalidadPos = ev.pos;
      this.menuCardinalidadActivo = true;
      this.cdr.detectChanges();
    }));
    this.subscriptions.add(this.canvasService.solicitudEditorNombre$.subscribe(id => this.abrirEditorNombre(id)));
    this.subscriptions.add(this.canvasService.solicitudEditorNuevoAtributo$.subscribe(id => this.abrirEditorNuevoAtributo(id)));
    this.subscriptions.add(this.canvasService.solicitudEditorAtributo$.subscribe(ev => this.abrirEditorAtributo(ev.entidadId, ev.index)));
    this.subscriptions.add(this.canvasService.solicitudEditorNombreRelacion$.subscribe(ev => this.abrirEditorNombreRelacion(ev.relacionId, ev.pos)));
    this.subscriptions.add(this.canvasService.solicitudActualizarRelacion$.subscribe(rel => {
      this.socketService.enviarActualizarRelacion(rel);
      this.programarSnapshot();
    }));
    this.subscriptions.add(this.canvasService.solicitudEliminarRelacion$.subscribe(id => this.socketService.enviarEliminarRelacion(id)));
    this.subscriptions.add(this.canvasService.bloquearEntidadLocal$.subscribe(id => this.socketService.enviarBloquearEntidad(id)));
    this.subscriptions.add(this.canvasService.moverEntidadLocal$.subscribe(ev => this.socketService.enviarMoverEntidad(ev.entidadId, ev.x, ev.y)));
    this.subscriptions.add(this.canvasService.moverEntidadFinLocal$.subscribe(ev => {
      this.socketService.enviarMoverEntidad(ev.entidadId, ev.x, ev.y);
      this.programarSnapshot();
    }));
    this.subscriptions.add(this.canvasService.desbloquearEntidadLocal$.subscribe(id => this.socketService.enviarDesbloquearEntidad(id)));
    this.subscriptions.add(this.canvasService.solicitudMenuContextual$.subscribe(ev => {
      this.menuContextualTipo = ev.tipo;
      this.menuContextualId = ev.id;
      this.menuContextualTitulo = ev.titulo;
      this.menuContextualPos = ev.pos;
      this.menuContextualActivo = true;
      this.cdr.detectChanges();
    }));
    this.subscriptions.add(this.canvasService.snapshotRequerido$.subscribe(() => this.programarSnapshot()));
    this.subscriptions.add(this.canvasService.cerrarModales$.subscribe(() => this.cerrarTodosModales()));
  }

  // ── Modales y Editores ──

  private abrirEditorNombreRelacion(relacionId: number, pos: PosicionEditor): void {
    const relacion = this.canvasService.getRelacion(relacionId);
    if (!relacion) return;
    this.editorEntidadId = null;
    this.editorAtributoIndex = null;
    this.editorRelacionId = relacionId;
    this.editorTipo = 'nombre_relacion';
    this.editorValor = relacion.nombre_relacion || '';
    this.editorPlaceholder = 'nombre_relacion';
    this.editorPos = pos;
    this.editorActivo = true;
    this.cdr.detectChanges();
  }

  private abrirEditorNombre(entidadId: number): void {
    const pos = this.canvasService.obtenerPosicionEditorNombre(entidadId);
    const entidad = this.canvasService.getEntidad(entidadId);
    if (!pos || !entidad) return;
    this.editorRelacionId = null;
    this.editorEntidadId = entidadId;
    this.editorTipo = 'nombre';
    this.editorAtributoIndex = null;
    this.editorValor = entidad.nombre || '';
    this.editorPlaceholder = 'Escribir nombre de entidad...';
    this.editorPos = pos;
    this.editorActivo = true;
    this.cdr.detectChanges();
  }

  private abrirEditorNuevoAtributo(entidadId: number): void {
    const pos = this.canvasService.obtenerPosicionEditorNuevoAtributo(entidadId);
    if (!pos) return;
    this.editorRelacionId = null;
    this.editorEntidadId = entidadId;
    this.editorTipo = 'nuevo_atributo';
    this.editorAtributoIndex = null;
    this.editorValor = '';
    this.editorPlaceholder = 'Ej: id: integer [pk] o nombre: string';
    this.editorPos = pos;
    this.editorActivo = true;
    this.cdr.detectChanges();
  }

  private abrirEditorAtributo(entidadId: number, index: number): void {
    const pos = this.canvasService.obtenerPosicionEditorAtributo(entidadId, index);
    const entidad = this.canvasService.getEntidad(entidadId);
    if (!pos || !entidad?.atributos?.[index]) return;
    const attr = entidad.atributos[index];
    this.editorRelacionId = null;
    this.editorEntidadId = entidadId;
    this.editorTipo = 'editar_atributo';
    this.editorAtributoIndex = index;
    const pkStr = attr.es_clave ? '[pk] ' : '';
    const optStr = attr.es_nulo ? '?' : '';
    this.editorValor = `${pkStr}${attr.nombre}: ${attr.tipo}${optStr}`;
    this.editorPlaceholder = 'Ej: nombre: string (vacío para eliminar)';
    this.editorPos = pos;
    this.editorActivo = true;
    this.cdr.detectChanges();
  }

  public onGuardarEditor(payload: GuardarEditorPayload): void {
    if (!this.editorActivo) return;

    if (this.editorTipo === 'nombre_relacion' && this.editorRelacionId !== null) {
      const relId = this.editorRelacionId;
      const valor = payload.valor.trim();
      const relActualizada = this.canvasService.actualizarNombreRelacion(relId, valor);
      if (relActualizada) {
        this.socketService.enviarActualizarRelacion(relActualizada);
        this.programarSnapshot();
      }
      this.onCancelarEditor();
      return;
    }

    if (this.editorEntidadId === null) return;
    const entidad = this.canvasService.getEntidad(this.editorEntidadId);
    if (!entidad) return;

    let encadenarSiguiente = false;
    const valor = payload.valor.trim();

    if (this.editorTipo === 'nombre') {
      entidad.nombre = valor;
      this.editorValor = valor;
      this.canvasService.actualizarEntidadLocal(entidad);
      this.socketService.enviarActualizarEntidad(entidad);
      if (payload.encadenar && valor.length > 0 && (!entidad.atributos || entidad.atributos.length === 0)) {
        encadenarSiguiente = true;
      }
    } else if (this.editorTipo === 'nuevo_atributo' && valor.length > 0) {
      const nuevoOrden = (entidad.atributos?.length ?? 0) + 1;
      const nuevoAttr = this.parserService.parsearAtributoTexto(valor, nuevoOrden, this.generarIdTemporal());
      if (!entidad.atributos) entidad.atributos = [];
      entidad.atributos.push(nuevoAttr);
      this.canvasService.actualizarEntidadLocal(entidad);
      this.socketService.enviarActualizarEntidad(entidad);
      encadenarSiguiente = payload.encadenar;
    } else if (this.editorTipo === 'editar_atributo' && this.editorAtributoIndex !== null && entidad.atributos) {
      if (valor.length > 0) {
        const actual = entidad.atributos[this.editorAtributoIndex];
        entidad.atributos[this.editorAtributoIndex] = this.parserService.parsearAtributoTexto(valor, actual.orden, actual.id);
      } else {
        entidad.atributos.splice(this.editorAtributoIndex, 1);
        entidad.atributos.forEach((a, i) => a.orden = i + 1);
      }
      this.canvasService.actualizarEntidadLocal(entidad);
      this.socketService.enviarActualizarEntidad(entidad);
    }

    const entidadId = this.editorEntidadId;
    this.onCancelarEditor();
    this.programarSnapshot();

    if (encadenarSiguiente) {
      setTimeout(() => this.abrirEditorNuevoAtributo(entidadId), 40);
    }
  }

  public onCancelarEditor(): void {
    this.editorActivo = false;
    this.editorEntidadId = null;
    this.editorAtributoIndex = null;
    this.editorRelacionId = null;
    this.editorValor = '';
    this.cdr.detectChanges();
  }

  public confirmarTipoRelacion(tipo: TipoRelacionUML): void {
    const res = this.canvasService.confirmarTipoRelacion(
      tipo,
      this.generarIdTemporal(),
      this.generarIdTemporal(),
      this.generarIdTemporal()
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
    this.cancelarMenuRelacion();
  }

  public cancelarMenuRelacion(): void {
    this.canvasService.cancelarRelacionPendiente();
    this.menuRelacionActivo = false;
    this.cdr.detectChanges();
  }

  public seleccionarCardinalidad(valor: string): void {
    if (!this.cardinalidadEditando) return;
    const relActualizada = this.canvasService.aplicarCardinalidad(
      this.cardinalidadEditando.relacionId,
      this.cardinalidadEditando.extremo,
      valor
    );
    if (relActualizada) {
      this.socketService.enviarActualizarRelacion(relActualizada);
      this.programarSnapshot();
    }
    this.cerrarSelectorCardinalidad();
  }

  public cerrarSelectorCardinalidad(): void {
    this.menuCardinalidadActivo = false;
    this.cardinalidadEditando = null;
    this.canvasService.deseleccionarCapsula();
    this.cdr.detectChanges();
  }

  // ── Manejo de Menú Contextual y Modales de Propiedades ──

  public onAbrirPropiedadesContextual(): void {
    const tipo = this.menuContextualTipo;
    const id = this.menuContextualId;
    this.menuContextualActivo = false;

    if (tipo === 'entidad' && id !== null) {
      const entidad = this.canvasService.getEntidad(id);
      if (entidad) {
        this.entidadEditando = JSON.parse(JSON.stringify(entidad));
        this.modalEntidadActivo = true;
      }
    } else if (tipo === 'relacion' && id !== null) {
      const rel = this.canvasService.getRelacion(id);
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

  public onAgregarEtiquetaContextual(): void {
    const tipo = this.menuContextualTipo;
    const relId = this.menuContextualId;
    this.menuContextualActivo = false;
    this.menuContextualId = null;

    if (tipo === 'relacion' && relId !== null) {
      const pos = this.canvasService.obtenerPosicionEditorNombreRelacion(relId);
      if (pos) {
        this.abrirEditorNombreRelacion(relId, pos);
      }
    }
    this.cdr.detectChanges();
  }

  public onEliminarContextual(): void {
    const tipo = this.menuContextualTipo;
    const id = this.menuContextualId;
    this.menuContextualActivo = false;
    this.menuContextualId = null;

    if (id !== null) {
      if (tipo === 'entidad') {
        this.canvasService.eliminarCeldaRemota(id);
        this.socketService.enviarEliminarEntidad(id);
        this.programarSnapshot();
      } else {
        this.canvasService.eliminarRelacionRemota(id);
        this.socketService.enviarEliminarRelacion(id);
        this.programarSnapshot();
      }
    }
    this.cdr.detectChanges();
  }

  public onCancelarMenuContextual(): void {
    this.menuContextualActivo = false;
    this.menuContextualId = null;
    this.cdr.detectChanges();
  }

  public onGuardarPropiedadesEntidad(entidadActualizada: EntidadDiagrama): void {
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
    const relActualizada = this.canvasService.actualizarPropiedadesRelacion(
      datos.relacionId,
      datos.nombre,
      datos.cardinalidadOrigen,
      datos.cardinalidadDestino
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

  public onAbrirColaboradores(): void {
    this.modalColaboradoresActivo = true;
    this.cdr.detectChanges();
  }

  public onCerrarColaboradores(): void {
    this.modalColaboradoresActivo = false;
    this.cdr.detectChanges();
  }

  private cerrarTodosModales(): void {
    this.onCancelarEditor();
    this.cancelarMenuRelacion();
    this.cerrarSelectorCardinalidad();
    this.onCancelarMenuContextual();
    this.onCancelarModalEntidad();
    this.onCancelarModalRelacion();
    this.onCerrarColaboradores();
  }

  @HostListener('document:keydown.escape', ['$event'])
  public onKeydownEscape(evt: KeyboardEvent): void {
    evt.preventDefault();
    this.cerrarTodosModales();
    this.canvasService.deseleccionarEnlace();
  }

  // ── Acciones Generales ──

  public onAgregarEntidad(): void {
    const centro = this.canvasService.calcularCentroVisible();
    const offset = (this.canvasService.getCantidadEntidades() % 6) * 36;
    const nueva = this.canvasService.crearEntidadLocal(centro.x - 110 + offset, centro.y - 30 + offset, this.generarIdTemporal());
    this.socketService.enviarCrearEntidad(nueva);
    this.abrirEditorNombre(nueva.id);
  }

  public onAgregarClaseAsociacion(): void {
    this.toastService.info('Para modelar una Clase de Asociación (N:M): traza un enlace entre dos tablas y selecciona "Clase de Asociación (N:M)" en el menú.');
  }

  public onAgregarNota(): void {
    const centro = this.canvasService.calcularCentroVisible();
    const offset = (this.canvasService.getCantidadEntidades() % 6) * 36;
    const nueva = this.canvasService.crearEntidadLocal(centro.x - 110 + offset, centro.y - 30 + offset, this.generarIdTemporal());
    nueva.nombre = 'Nota / Comentario';
    this.canvasService.actualizarEntidadLocal(nueva);
    this.socketService.enviarCrearEntidad(nueva);
    this.abrirEditorNombre(nueva.id);
  }

  public onRenombrarProyecto(nuevoNombre: string): void {
    if (!this.proyecto || !nuevoNombre.trim()) return;
    const nombreLimpio = nuevoNombre.trim();
    this.proyecto.nombre = nombreLimpio;
    this.socketService.enviarRenombrarProyecto(nombreLimpio);
    this.apiService.renombrarProyecto(this.proyectoId, nombreLimpio).subscribe({
      next: () => {
        this.toastService.exito(`Proyecto renombrado a "${nombreLimpio}"`);
      },
      error: () => {
        this.toastService.error('No se pudo guardar el nuevo nombre del proyecto.');
      }
    });
  }

  public onGenerarCodigo(): void {
    this.toastService.info('Generador de código Spring Boot y entidades JPA en desarrollo para la Fase 2.');
  }

  public onExportarImagen(): void {
    this.toastService.info('Exportación de diagrama en formato PNG/PDF disponible próximamente en Fase 2.');
  }

  public onDragOverLienzo(evt: DragEvent): void {
    evt.preventDefault();
    if (evt.dataTransfer) {
      evt.dataTransfer.dropEffect = 'copy';
    }
  }

  public onDropLienzo(evt: DragEvent): void {
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
      const nueva = this.canvasService.crearEntidadLocal(localPt.x, localPt.y, this.generarIdTemporal());
      this.socketService.enviarCrearEntidad(nueva);
      this.abrirEditorNombre(nueva.id);
    } else if (tipo === 'clase_asociacion') {
      this.onAgregarClaseAsociacion();
    } else if (tipo === 'nota') {
      const nueva = this.canvasService.crearEntidadLocal(localPt.x, localPt.y, this.generarIdTemporal());
      nueva.nombre = 'Nota / Comentario';
      this.canvasService.actualizarEntidadLocal(nueva);
      this.socketService.enviarCrearEntidad(nueva);
      this.abrirEditorNombre(nueva.id);
    }
  }

  public onToggleTema(): void {
    this.modoOscuro = !this.modoOscuro;
    this.canvasService.setModoOscuro(this.modoOscuro);
  }

  public onZoomIn(): void { this.canvasService.zoomIn(); }
  public onZoomOut(): void { this.canvasService.zoomOut(); }
  public onZoomReset(): void { this.canvasService.zoomReset(); }

  public onCerrarSesion(): void {
    if (this.canvasService.estaListo) {
      const datos = this.canvasService.obtenerSnapshotDatos();
      this.socketService.forzarGuardarSnapshot(datos);
    }
    this.socketService.desconectar();
    this.authService.logout().subscribe();
  }

  public onVolverDashboard(): void {
    if (this.canvasService.estaListo) {
      const datos = this.canvasService.obtenerSnapshotDatos();
      this.socketService.forzarGuardarSnapshot(datos);
    }
    this.socketService.desconectar();
    this.router.navigate(['/control']);
  }

  private programarSnapshot(): void {
    const datos = this.canvasService.obtenerSnapshotDatos();
    this.socketService.programarGuardarSnapshot(datos);
  }

  private generarIdTemporal(): number {
    this.contadorSesion++;
    const delta = Date.now() - 1700000000000;
    const userSeed = this.miUsuarioId ? (Math.abs(this.miUsuarioId) % 100) : Math.floor(Math.random() * 90 + 10);
    return - (delta * 10000 + userSeed * 100 + (this.contadorSesion % 100));
  }
}
