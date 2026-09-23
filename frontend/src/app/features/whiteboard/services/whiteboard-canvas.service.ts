import { Injectable, inject } from '@angular/core';
import { Subject, Observable } from 'rxjs';
import * as joint from '@joint/core';

import { EntidadDiagrama, RelacionDiagrama } from '../interfaces/diagrama.interface';
import { TemaColores, TipoRelacionUML, PosicionEditor } from '../interfaces/whiteboard-ui.interface';
import { WhiteboardCameraService } from './whiteboard-camera.service';
import { WhiteboardEntityService } from './whiteboard-entity.service';
import { WhiteboardRelationshipService } from './whiteboard-relationship.service';

const TEMA_CLARO: TemaColores = {
  lienzo:         '#FFFFFF',
  grid:           'rgba(0,0,0,0.06)',
  entidadFondo:   '#FAFAFA',
  entidadBorde:   'rgba(0,0,0,0.18)',
  headerFondo:    '#1E293B',
  headerBorde:    '#334155',
  headerTexto:    '#F8FAFC',
  bodyTexto:      '#333333',
  bloqueadoBorde: '#F59E0B'
};

const TEMA_OSCURO: TemaColores = {
  lienzo:         '#111111',
  grid:           'rgba(255,255,255,0.04)',
  entidadFondo:   '#1A1A1A',
  entidadBorde:   'rgba(255,255,255,0.18)',
  headerFondo:    '#1E293B',
  headerBorde:    '#334155',
  headerTexto:    '#F8FAFC',
  bodyTexto:      '#AAAAAA',
  bloqueadoBorde: '#F59E0B'
};

const ALTO_HEADER = 36;
const ALTO_ATRIBUTO = 24;

export interface EventoRelacionSolicitud {
  origenId: number;
  destinoId: number;
  origenPuerto?: string;
  destinoPuerto?: string;
  pos: { x: number; y: number };
}

export interface EventoCardinalidadSolicitud {
  relacionId: number;
  extremo: 'origen' | 'destino';
  valorActual: string;
  pos: { x: number; y: number };
}

@Injectable()
export class WhiteboardCanvasService {
  private readonly cameraService       = inject(WhiteboardCameraService);
  private readonly entityService       = inject(WhiteboardEntityService);
  private readonly relationshipService = inject(WhiteboardRelationshipService);

  private graph!: joint.dia.Graph;
  private paper!: joint.dia.Paper;
  private lienzoContainer: HTMLElement | null = null;
  private resizeObserver: ResizeObserver | null = null;

  public modoOscuro = false;

  // ── Eventos hacia la página (Observables públicos) ──
  public readonly solicitudRelacion$ = new Subject<EventoRelacionSolicitud>();
  public readonly solicitudActualizarRelacion$ = new Subject<RelacionDiagrama>();
  public readonly solicitudCardinalidad$ = new Subject<EventoCardinalidadSolicitud>();
  public readonly solicitudEditorNombre$ = new Subject<number>();
  public readonly solicitudEditorNuevoAtributo$ = new Subject<number>();
  public readonly solicitudEditorAtributo$ = new Subject<{ entidadId: number; index: number }>();
  public readonly solicitudEditorNombreRelacion$ = new Subject<{ relacionId: number; pos: PosicionEditor }>();
  public readonly solicitudEliminarRelacion$ = new Subject<number>();
  public readonly solicitudMenuContextual$ = new Subject<{
    tipo: 'entidad' | 'relacion';
    id: number;
    titulo: string;
    pos: { x: number; y: number };
  }>();

  public readonly bloquearEntidadLocal$ = new Subject<number>();
  public readonly moverEntidadLocal$ = new Subject<{ entidadId: number; x: number; y: number }>();
  public readonly moverEntidadFinLocal$ = new Subject<{ entidadId: number; x: number; y: number }>();
  public readonly desbloquearEntidadLocal$ = new Subject<number>();
  public readonly snapshotRequerido$ = new Subject<void>();
  public readonly cerrarModales$ = new Subject<void>();

  private arrastrandoArrowhead = false;

  public get tema(): TemaColores {
    return this.modoOscuro ? TEMA_OSCURO : TEMA_CLARO;
  }

  public get zoomNivel(): number {
    return this.cameraService.zoomNivel;
  }

  public get zoomNivel$(): Observable<number> {
    return this.cameraService.zoomNivel$;
  }

  public get estaListo(): boolean {
    return !!this.paper && !!this.graph;
  }

  // ── Inicialización y Destrucción ────────────────────────────────────────

  public inicializar(container: HTMLElement): void {
    this.lienzoContainer = container;
    this.graph = new joint.dia.Graph({}, { cellNamespace: joint.shapes });

    const wrapper = container.parentElement!;
    const w = wrapper.clientWidth  || window.innerWidth  - 260;
    const h = wrapper.clientHeight || window.innerHeight;

    this.paper = new joint.dia.Paper({
      el:                container,
      model:             this.graph,
      width:             w,
      height:            h,
      gridSize:          16,
      drawGrid:          { name: 'mesh', args: { color: this.tema.grid, thickness: 1 } },
      background:        { color: this.tema.lienzo },
      cellViewNamespace: joint.shapes,
      clickThreshold:    5,
      interactive:       { linkMove: false },
      linkPinning:       false,
      snapLinks:         { radius: 20 },
      async:             true,
      sorting:           joint.dia.Paper.sorting.APPROX,
      highlighting: {
        connecting: {
          name: 'stroke',
          options: {
            padding: 3,
            rx: 5,
            ry: 5,
            attrs: {
              stroke: '#00A3FF',
              'stroke-width': 2.5
            }
          }
        }
      },
      defaultRouter: {
        name: 'manhattan',
        args: { step: 10, padding: 20, maxAllowedDirectionChange: 90, perpendicular: true }
      },
      defaultConnector:  { name: 'rounded', args: { radius: 8 } },
      defaultLink: () => {
        const colorLinea = this.modoOscuro ? '#EDEDED' : '#222222';
        return new joint.shapes.standard.Link({
          router: { name: 'manhattan', args: { step: 10, padding: 20, maxAllowedDirectionChange: 90, perpendicular: true } },
          connector: { name: 'rounded', args: { radius: 8 } },
          attrs: {
            line: { stroke: colorLinea, strokeWidth: 1.8, strokeDasharray: '4 2', targetMarker: { type: 'none' } }
          }
        });
      },
      validateConnection: (
        cellViewS: joint.dia.CellView,
        magnetS: SVGElement,
        cellViewT: joint.dia.CellView,
        magnetT: SVGElement,
        end?: 'source' | 'target'
      ): boolean => {
        if (!cellViewS || !cellViewT) return false;
        if (!cellViewS.model.isElement() || !cellViewT.model.isElement()) return false;

        const portS = magnetS?.getAttribute('port') || magnetS?.closest?.('[port]')?.getAttribute('port');
        const portT = magnetT?.getAttribute('port') || magnetT?.closest?.('[port]')?.getAttribute('port');

        // Al mover/reubicar un extremo existente mediante su arrowhead:
        if (end === 'source' && !portS) return false;
        if (end === 'target' && !portT) return false;
        // Al crear un nuevo enlace desde cero (ambos extremos deben ser puertos):
        if (!end && (!portS || !portT)) return false;

        // Si es una relación reflexiva (consigo misma), no permitir conectar un puerto a sí mismo
        if (cellViewS === cellViewT && portS && portT && portS === portT) return false;

        return true;
      }
    });

    const observer = new ResizeObserver(() => {
      const nw = wrapper.clientWidth;
      const nh = wrapper.clientHeight;
      if (nw > 0 && nh > 0) this.paper.setDimensions(nw, nh);
    });
    observer.observe(wrapper);
    this.resizeObserver = observer;

    // Conectar sub-servicios
    this.entityService.conectar(this.graph, this.paper, container);
    this.relationshipService.conectar(this.graph, this.paper);
    this.cameraService.conectar(this.paper, container);

    this.cameraService.cerrarModales$.subscribe(() => this.cerrarModales$.next());

    container.addEventListener('contextmenu', (evt: MouseEvent) => {
      evt.preventDefault();
    });

    this.registrarEventosPaper();
  }

  public limpiar(): void {
    if (this.graph) {
      this.graph.clear();
    }
    this.relationshipService.limpiar();
    this.entityService.limpiar();
  }

  public destruir(): void {
    this.limpiar();
    this.cameraService.desconectar();
    this.relationshipService.desconectar();
    this.entityService.desconectar();
    this.resizeObserver?.disconnect();
    this.lienzoContainer = null;
  }

  // ── Tema ─────────────────────────────────────────────────────────────────

  public setModoOscuro(oscuro: boolean): void {
    this.modoOscuro = oscuro;
    this.aplicarTema();
  }

  public aplicarTema(): void {
    if (!this.paper) return;

    const p = this.paper as unknown as {
      drawBackground: (opts: { color: string }) => void;
      setGrid: (opts: { name: string; args: { color: string; thickness: number } }) => void;
    };

    p.drawBackground({ color: this.tema.lienzo });
    p.setGrid({ name: 'mesh', args: { color: this.tema.grid, thickness: 1 } });

    this.entityService.aplicarTema(this.tema);
    this.relationshipService.aplicarTema(this.modoOscuro);
  }

  // ── Cámara (Delegada a WhiteboardCameraService) ──────────────────────────

  public zoomIn(): void { this.cameraService.zoomIn(); }
  public zoomOut(): void { this.cameraService.zoomOut(); }
  public zoomReset(): void { this.cameraService.zoomReset(); }
  public calcularCentroVisible(): { x: number; y: number } { return this.cameraService.calcularCentroVisible(); }

  // ── Entidades (Delegadas a WhiteboardEntityService) ──────────────────────

  public renderizarEntidades(entidades: EntidadDiagrama[]): void {
    this.entityService.renderizarEntidades(entidades, this.tema);
    this.relationshipService.procesarRelacionesPendientes(this.modoOscuro);
    this.relationshipService.verificarConectoresClaseAsociacion(this.modoOscuro);
  }

  public crearEntidadLocal(coordX: number, coordY: number, nuevoId: number): EntidadDiagrama {
    return this.entityService.crearEntidadLocal(coordX, coordY, nuevoId, this.tema);
  }

  public actualizarEntidadLocal(entidad: EntidadDiagrama): void {
    this.entityService.actualizarEntidadLocal(entidad, this.tema);
  }

  public getEntidad(id: number): EntidadDiagrama | undefined {
    return this.entityService.getEntidad(id);
  }

  public getCantidadEntidades(): number {
    return this.entityService.getCantidadEntidades();
  }

  public moverCeldaRemota(id: number | undefined, x: number | undefined, y: number | undefined): void {
    if (id !== undefined && x !== undefined && y !== undefined) {
      this.entityService.moverCeldaRemota(Number(id), Number(x), Number(y));
    }
  }

  public crearCeldaRemota(entidad: EntidadDiagrama): void {
    this.entityService.crearCeldaRemota(entidad, this.tema);
    this.relationshipService.procesarRelacionesPendientes(this.modoOscuro);
    this.relationshipService.verificarConectoresClaseAsociacion(this.modoOscuro);
  }

  public actualizarCeldaRemota(entidad: EntidadDiagrama): void {
    this.entityService.actualizarCeldaRemota(entidad, this.tema);
  }

  public eliminarCeldaRemota(entidadId: number): void {
    this.entityService.eliminarCeldaRemota(entidadId);
    this.relationshipService.limpiarRelacionesDeEntidad(entidadId);
  }

  public cambiarBorde(id: number | undefined, color: string): void {
    if (id !== undefined) this.entityService.cambiarBorde(Number(id), color);
  }

  public setBloqueoEntidad(id: number | undefined, bloqueado: boolean): void {
    if (id !== undefined) this.entityService.setEstadoBloqueoEntidad(Number(id), bloqueado, this.tema);
  }

  // ── Posicionamiento de Editores Inline ──

  public obtenerPosicionEditorNombre(entidadId: number): PosicionEditor | null {
    return this.entityService.obtenerPosicionEditorNombre(entidadId);
  }

  public obtenerPosicionEditorNuevoAtributo(entidadId: number): PosicionEditor | null {
    return this.entityService.obtenerPosicionEditorNuevoAtributo(entidadId);
  }

  public obtenerPosicionEditorAtributo(entidadId: number, index: number): PosicionEditor | null {
    return this.entityService.obtenerPosicionEditorAtributo(entidadId, index);
  }

  // ── Relaciones (Delegadas a WhiteboardRelationshipService) ───────────────

  public renderizarRelaciones(relaciones: RelacionDiagrama[]): void {
    this.relationshipService.renderizarRelaciones(relaciones, this.modoOscuro);
  }

  public confirmarTipoRelacion(
    tipo: TipoRelacionUML,
    nuevoRelacionId: number,
    nuevoRelacionId2?: number,
    nuevoClaseAsocEntidadId?: number
  ): { relaciones: RelacionDiagrama[]; entidadIntermedia?: EntidadDiagrama } | null {
    return this.relationshipService.confirmarTipoRelacion(
      tipo,
      nuevoRelacionId,
      nuevoRelacionId2,
      nuevoClaseAsocEntidadId,
      this.modoOscuro
    );
  }

  public cancelarRelacionPendiente(): void {
    this.relationshipService.cancelarRelacionPendiente();
  }

  public crearRelacionRemota(relacion: RelacionDiagrama): void {
    this.relationshipService.crearRelacionRemota(relacion, this.modoOscuro);
  }

  public actualizarRelacionRemota(relacion: RelacionDiagrama): void {
    this.relationshipService.actualizarRelacionRemota(relacion, this.modoOscuro);
  }

  public actualizarPuertosRelacion(
    relacionId: number,
    nuevoOrigenId: number,
    nuevoDestinoId: number,
    nuevoPuertoOrigen?: string,
    nuevoPuertoDestino?: string
  ): RelacionDiagrama | null {
    return this.relationshipService.actualizarPuertosRelacion(
      relacionId,
      nuevoOrigenId,
      nuevoDestinoId,
      nuevoPuertoOrigen,
      nuevoPuertoDestino,
      this.modoOscuro
    );
  }

  public eliminarRelacionRemota(relacionId: number): void {
    this.relationshipService.eliminarRelacionRemota(relacionId);
  }

  public deseleccionarEnlace(): void {
    this.relationshipService.deseleccionarEnlace();
  }

  public getRelacionSeleccionadaId(): number | null {
    return this.relationshipService.getRelacionSeleccionadaId();
  }

  public deseleccionarCapsula(): void {
    this.relationshipService.deseleccionarCapsula(this.modoOscuro);
  }

  public aplicarCardinalidad(relacionId: number, extremo: 'origen' | 'destino', valor: string): RelacionDiagrama | null {
    return this.relationshipService.aplicarCardinalidad(relacionId, extremo, valor, this.modoOscuro);
  }

  public actualizarNombreRelacion(relacionId: number, nombre: string): RelacionDiagrama | null {
    return this.relationshipService.actualizarNombreRelacion(relacionId, nombre, this.modoOscuro);
  }

  public actualizarPropiedadesRelacion(
    relacionId: number,
    nombre: string,
    cardinalidadOrigen: string,
    cardinalidadDestino: string
  ): RelacionDiagrama | null {
    return this.relationshipService.actualizarPropiedadesRelacion(
      relacionId,
      nombre,
      cardinalidadOrigen,
      cardinalidadDestino,
      this.modoOscuro
    );
  }

  public getRelacion(relacionId: number): RelacionDiagrama | undefined {
    return this.relationshipService.getRelacion(relacionId);
  }

  public obtenerPosicionEditorNombreRelacion(relacionId: number): PosicionEditor | null {
    if (!this.lienzoContainer) return null;
    return this.relationshipService.obtenerPosicionEditorNombreRelacion(relacionId, this.lienzoContainer);
  }

  // ── Snapshot Datos ───────────────────────────────────────────────────────

  public obtenerSnapshotDatos(): {
    entidades: EntidadDiagrama[];
    posiciones: Record<number, { x: number; y: number }>;
    relaciones: RelacionDiagrama[];
  } {
    return {
      entidades: this.entityService.getEntidades(),
      posiciones: this.entityService.obtenerPosiciones(),
      relaciones: this.relationshipService.getRelaciones()
    };
  }

  public getEntidades(): EntidadDiagrama[] {
    return this.entityService.getEntidades();
  }

  public getRelaciones(): RelacionDiagrama[] {
    return this.relationshipService.getRelaciones();
  }

  public actualizarIdsSincronizados(
    idMap?: Record<string | number, number>,
    relIdMap?: Record<string | number, number>
  ): void {
    if (idMap && Object.keys(idMap).length > 0) {
      this.entityService.remapIds(idMap);
    }
    if ((idMap && Object.keys(idMap).length > 0) || (relIdMap && Object.keys(relIdMap).length > 0)) {
      this.relationshipService.remapIds(idMap, relIdMap);
    }
  }

  // ── Registro de Eventos del Paper ────────────────────────────────────────

  private registrarEventosPaper(): void {
    this.paper.on('element:mouseenter', (elementView: joint.dia.ElementView) => {
      elementView.el.classList.add('puertos-visibles');
    });

    this.paper.on('element:mouseleave', (elementView: joint.dia.ElementView) => {
      elementView.el.classList.remove('puertos-visibles');
    });

    this.paper.on('cell:mouseover', (_cellView: joint.dia.CellView, evt: MouseEvent) => {
      const target = evt?.target as SVGElement | null;
      if (target && (target.getAttribute('port') || target.closest?.('[port]'))) {
        const portEl = target.getAttribute('port') ? target : target.closest('[port]') as SVGElement;
        const circle = (portEl.tagName.toLowerCase() === 'circle') ? portEl : portEl.querySelector('circle');
        if (circle) {
          circle.setAttribute('r', '6.5');
          circle.setAttribute('stroke', '#00A3FF');
          circle.setAttribute('stroke-width', '2.5');
          circle.style.filter = 'drop-shadow(0 0 5px rgba(0, 163, 255, 0.9))';
          circle.style.cursor = 'crosshair';
        }
      }
    });

    this.paper.on('cell:mouseout', (_cellView: joint.dia.CellView, evt: MouseEvent) => {
      const target = evt?.target as SVGElement | null;
      if (target && (target.getAttribute('port') || target.closest?.('[port]'))) {
        const portEl = target.getAttribute('port') ? target : target.closest('[port]') as SVGElement;
        const circle = (portEl.tagName.toLowerCase() === 'circle') ? portEl : portEl.querySelector('circle');
        if (circle) {
          circle.setAttribute('r', '4.5');
          circle.setAttribute('stroke', this.modoOscuro ? '#38BDF8' : '#0284C7');
          circle.setAttribute('stroke-width', '1.8');
          circle.style.filter = 'none';
        }
      }
    });

    this.graph.on('batch:start', (data: { batchName?: string }) => {
      if (data?.batchName === 'arrowhead-move' || data?.batchName === 'add-link') {
        this.lienzoContainer?.classList.add('arrastrando-puerto');
        if (data?.batchName === 'arrowhead-move') {
          this.arrastrandoArrowhead = true;
        }
      }
    });

    this.graph.on('batch:stop', (data: { batchName?: string }) => {
      if (data?.batchName === 'arrowhead-move' || data?.batchName === 'add-link') {
        this.lienzoContainer?.classList.remove('arrastrando-puerto');
        if (data?.batchName === 'arrowhead-move') {
          this.arrastrandoArrowhead = false;
        }
      }
    });

    this.paper.on('link:mouseenter', (linkView: joint.dia.LinkView) => {
      this.relationshipService.mostrarHerramientasEnlace(linkView);
    });

    this.paper.on('link:mouseleave', (linkView: joint.dia.LinkView) => {
      this.relationshipService.ocultarHerramientasEnlace(linkView, this.arrastrandoArrowhead);
    });

    this.paper.on('link:connect', (linkView: joint.dia.LinkView, evt: MouseEvent) => {
      const link = linkView.model;
      const source = link.source();
      const target = link.target();

      const sourceCellId = source?.id as string;
      const targetCellId = target?.id as string;
      const sourcePort = (source?.port as string) || undefined;
      const targetPort = (target?.port as string) || undefined;

      const origenId = this.entityService.getEntidadIdPorCeldaId(sourceCellId);
      const destinoId = this.entityService.getEntidadIdPorCeldaId(targetCellId);

      if (!origenId || !destinoId) {
        link.remove();
        return;
      }

      // Comprobar si es una relación existente que se está reubicando / desanclando
      const relIdExistente = this.relationshipService.getRelacionIdPorLinkId(link.id);

      if (relIdExistente !== null) {
        const relPrevia = this.relationshipService.getRelacion(relIdExistente);
        const pOrig = sourcePort || relPrevia?.puerto_origen;
        const pDest = targetPort || relPrevia?.puerto_destino;

        // Si ya existe otra relación entre estas dos entidades en los mismos puertos exactos, revertir al estado anterior
        if (this.relationshipService.yaExisteRelacionEnMismosPuertos(origenId, destinoId, pOrig, pDest, relIdExistente)) {
          if (relPrevia) {
            const celdaOrigenAnt = this.entityService.getCelda(relPrevia.entidad_origen_id);
            const celdaDestinoAnt = this.entityService.getCelda(relPrevia.entidad_destino_id);
            if (celdaOrigenAnt && celdaDestinoAnt) {
              link.source({ id: celdaOrigenAnt.id, ...(relPrevia.puerto_origen ? { port: relPrevia.puerto_origen } : {}) });
              link.target({ id: celdaDestinoAnt.id, ...(relPrevia.puerto_destino ? { port: relPrevia.puerto_destino } : {}) });
              const esAuto = relPrevia.entidad_origen_id === relPrevia.entidad_destino_id;
              link.router('manhattan', this.relationshipService.obtenerOpcionesRouterManhattan(esAuto, relPrevia.puerto_origen, relPrevia.puerto_destino));
            }
          }
          return;
        }

        const relActualizada = this.relationshipService.actualizarPuertosRelacion(
          relIdExistente,
          origenId,
          destinoId,
          pOrig,
          pDest,
          this.modoOscuro
        );

        if (relActualizada) {
          this.solicitudActualizarRelacion$.next(relActualizada);
          this.snapshotRequerido$.next();
        }
        return;
      }

      // Caso: Nueva relación que se está creando (solo evitar colisión en los mismos puertos exactos)
      if (this.relationshipService.yaExisteRelacionEnMismosPuertos(origenId, destinoId, sourcePort, targetPort)) {
        link.remove();
        return;
      }

      // Si es una relación reflexiva (consigo misma), enrutar de inmediato con padding estricto y direcciones obligatorias de salida y entrada según los puertos
      if (origenId === destinoId) {
        link.router('manhattan', this.relationshipService.obtenerOpcionesRouterManhattan(true, sourcePort, targetPort));
      }

      this.relationshipService.cancelarRelacionPendiente();
      this.relationshipService.setRelacionPendiente(link, origenId, destinoId, sourcePort, targetPort);

      const wrapperRect = this.lienzoContainer!.parentElement!.getBoundingClientRect();
      const clickX = (evt && evt.clientX !== undefined) ? evt.clientX : (wrapperRect.left + wrapperRect.width / 2);
      const clickY = (evt && evt.clientY !== undefined) ? evt.clientY : (wrapperRect.top + wrapperRect.height / 2);

      const posX = clickX - wrapperRect.left;
      const posY = clickY - wrapperRect.top;

      const menuAncho = 280;
      const menuAlto = 310;
      const maxX = wrapperRect.width - menuAncho - 16;
      const maxY = wrapperRect.height - menuAlto - 16;

      this.solicitudRelacion$.next({
        origenId,
        destinoId,
        origenPuerto: sourcePort,
        destinoPuerto: targetPort,
        pos: { x: Math.max(16, Math.min(posX, maxX)), y: Math.max(16, Math.min(posY, maxY)) }
      });
    });

    this.paper.on('link:pointerdown', (linkView: joint.dia.LinkView, evt: MouseEvent) => {
      if (evt && evt.button !== 0) return;
      const target = evt?.target as SVGElement;
      if (target?.closest?.('[label-idx]')) return;
      if (target?.closest?.('.source-arrowhead') || target?.closest?.('.target-arrowhead')) return;
      evt?.stopPropagation?.();
      this.deseleccionarCapsula();
      this.cerrarModales$.next();
      this.relationshipService.seleccionarEnlace(linkView);
    });

    this.paper.on('link:pointerclick', (linkView: joint.dia.LinkView, evt: MouseEvent) => {
      const target = evt?.target as SVGElement;
      if (target?.closest?.('.source-arrowhead') || target?.closest?.('.target-arrowhead')) return;
      const labelG = target?.closest?.('[label-idx]') as SVGGraphicsElement | null;
      if (labelG) {
        const labelIdx = parseInt(labelG.getAttribute('label-idx') || '0', 10);
        if (labelIdx === 0 || labelIdx === 1) {
          evt?.stopPropagation?.();
          const extremo: 'origen' | 'destino' = labelIdx === 0 ? 'origen' : 'destino';
          const relId = this.relationshipService.getRelacionIdPorLinkId(linkView.model.id);
          if (relId !== null && this.lienzoContainer) {
            const res = this.relationshipService.seleccionarCapsula(relId, extremo, this.modoOscuro, labelG, this.lienzoContainer);
            if (res) this.solicitudCardinalidad$.next(res);
          }
        }
      }
    });

    const abrirMenuContextualRelacion = (linkView: joint.dia.LinkView, evt: MouseEvent) => {
      const target = evt?.target as SVGElement;
      if (target?.closest?.('.source-arrowhead') || target?.closest?.('.target-arrowhead')) return;
      if (target?.closest?.('[label-idx="0"]') || target?.closest?.('[label-idx="1"]')) return;
      if (this.relationshipService.esConectorAuxiliar(linkView.model.id)) return;

      evt?.preventDefault?.();
      evt?.stopPropagation?.();
      this.deseleccionarCapsula();
      this.cerrarModales$.next();

      const relId = this.relationshipService.getRelacionIdPorLinkId(linkView.model.id);
      if (relId !== null && this.lienzoContainer) {
        const wrapperRect = this.lienzoContainer.parentElement!.getBoundingClientRect();
        const clickX = (evt && evt.clientX !== undefined) ? evt.clientX : (wrapperRect.left + wrapperRect.width / 2);
        const clickY = (evt && evt.clientY !== undefined) ? evt.clientY : (wrapperRect.top + wrapperRect.height / 2);

        const posX = clickX - wrapperRect.left;
        const posY = clickY - wrapperRect.top;
        const menuAncho = 280;
        const menuAlto = 230;
        const maxX = wrapperRect.width - menuAncho - 16;
        const maxY = wrapperRect.height - menuAlto - 16;

        const rel = this.relationshipService.getRelacion(relId);
        const titulo = rel?.nombre_relacion || rel?.tipo || `Relación #${relId}`;

        this.solicitudMenuContextual$.next({
          tipo: 'relacion',
          id: relId,
          titulo,
          pos: { x: Math.max(16, Math.min(posX, maxX)), y: Math.max(16, Math.min(posY, maxY)) }
        });
      }
    };

    this.paper.on('link:pointerdblclick', (linkView: joint.dia.LinkView, evt: MouseEvent) => {
      abrirMenuContextualRelacion(linkView, evt);
    });

    this.paper.on('link:contextmenu', (linkView: joint.dia.LinkView, evt: MouseEvent) => {
      abrirMenuContextualRelacion(linkView, evt);
    });

    this.paper.on('element:pointerdown', (view: joint.dia.ElementView, evt: MouseEvent) => {
      if (evt && evt.button !== 0) return;
      this.cerrarModales$.next();
      this.deseleccionarEnlace();
      this.deseleccionarCapsula();
      const entidadId = this.entityService.getEntidadIdPorCeldaId(view.model.id as string);
      if (entidadId !== undefined) this.bloquearEntidadLocal$.next(entidadId);
    });

    let ultimoEnvioMove = 0;
    this.paper.on('element:pointermove', (view: joint.dia.ElementView) => {
      const entidadId = this.entityService.getEntidadIdPorCeldaId(view.model.id as string);
      const pos = view.model.position();
      if (entidadId !== undefined) {
        const ent = this.entityService.getEntidad(entidadId);
        if (ent) {
          ent.coord_x = pos.x;
          ent.coord_y = pos.y;
        }
        const ahora = performance.now();
        if (ahora - ultimoEnvioMove > 25) {
          ultimoEnvioMove = ahora;
          this.moverEntidadLocal$.next({ entidadId, x: pos.x, y: pos.y });
        }
      }
    });

    this.paper.on('element:pointerup', (view: joint.dia.ElementView) => {
      const entidadId = this.entityService.getEntidadIdPorCeldaId(view.model.id as string);
      const pos = view.model.position();
      if (entidadId !== undefined) {
        const ent = this.entityService.getEntidad(entidadId);
        if (ent) {
          ent.coord_x = pos.x;
          ent.coord_y = pos.y;
        }
        this.moverEntidadFinLocal$.next({ entidadId, x: pos.x, y: pos.y });
        this.desbloquearEntidadLocal$.next(entidadId);
      }
      this.snapshotRequerido$.next();
    });

    const manejarClickElemento = (cellView: joint.dia.ElementView, evt: MouseEvent, _x?: number, y?: number) => {
      this.cerrarModales$.next();

      const entidadId = this.entityService.getEntidadIdPorCeldaId(cellView.model.id as string);
      if (entidadId === undefined) return;

      const entidad = this.entityService.getEntidad(entidadId);
      if (!entidad) return;
      if (entidad.estado === 'bloqueado') return;

      const pos = cellView.model.position();
      const clickY = (y !== undefined)
        ? y
        : this.paper.clientToLocalPoint({ x: evt?.clientX ?? 0, y: evt?.clientY ?? 0 }).y;
      const relY = clickY - pos.y;

      if (relY <= ALTO_HEADER) {
        this.solicitudEditorNombre$.next(entidadId);
      } else {
        const numAtributos = entidad.atributos?.length ?? 0;
        const rowRelY = relY - ALTO_HEADER;
        const rowIndex = Math.floor((rowRelY - 8) / ALTO_ATRIBUTO);

        if (rowIndex >= 0 && rowIndex < numAtributos) {
          this.solicitudEditorAtributo$.next({ entidadId, index: rowIndex });
        } else {
          this.solicitudEditorNuevoAtributo$.next(entidadId);
        }
      }
    };

    let timerClickElemento: ReturnType<typeof setTimeout> | null = null;

    this.paper.on('element:pointerclick', (cellView: joint.dia.ElementView, evt: MouseEvent, _x?: number, y?: number) => {
      if (evt?.detail > 1) {
        if (timerClickElemento) {
          clearTimeout(timerClickElemento);
          timerClickElemento = null;
        }
        return;
      }
      if (timerClickElemento) {
        clearTimeout(timerClickElemento);
      }
      timerClickElemento = setTimeout(() => {
        timerClickElemento = null;
        manejarClickElemento(cellView, evt, _x, y);
      }, 220);
    });

    const abrirMenuContextualEntidad = (cellView: joint.dia.ElementView, evt: MouseEvent) => {
      if (timerClickElemento) {
        clearTimeout(timerClickElemento);
        timerClickElemento = null;
      }

      evt?.preventDefault?.();
      evt?.stopPropagation?.();
      this.deseleccionarCapsula();
      this.deseleccionarEnlace();
      this.cerrarModales$.next();

      const entidadId = this.entityService.getEntidadIdPorCeldaId(cellView.model.id as string);
      if (entidadId === undefined || !this.lienzoContainer) return;

      const entidad = this.entityService.getEntidad(entidadId);
      if (!entidad) return;

      const wrapperRect = this.lienzoContainer.parentElement!.getBoundingClientRect();
      const clickX = (evt && evt.clientX !== undefined) ? evt.clientX : (wrapperRect.left + wrapperRect.width / 2);
      const clickY = (evt && evt.clientY !== undefined) ? evt.clientY : (wrapperRect.top + wrapperRect.height / 2);

      const posX = clickX - wrapperRect.left;
      const posY = clickY - wrapperRect.top;
      const menuAncho = 280;
      const menuAlto = 170;
      const maxX = wrapperRect.width - menuAncho - 16;
      const maxY = wrapperRect.height - menuAlto - 16;

      this.solicitudMenuContextual$.next({
        tipo: 'entidad',
        id: entidadId,
        titulo: entidad.nombre || `Entidad #${entidadId}`,
        pos: { x: Math.max(16, Math.min(posX, maxX)), y: Math.max(16, Math.min(posY, maxY)) }
      });
    };

    this.paper.on('element:pointerdblclick', (cellView: joint.dia.ElementView, evt: MouseEvent) => {
      abrirMenuContextualEntidad(cellView, evt);
    });

    this.paper.on('element:contextmenu', (cellView: joint.dia.ElementView, evt: MouseEvent) => {
      abrirMenuContextualEntidad(cellView, evt);
    });

    this.paper.on('blank:contextmenu', (evt: MouseEvent) => {
      evt?.preventDefault?.();
      this.cerrarModales$.next();
    });

    this.paper.on('blank:pointerdown', (evt: MouseEvent) => {
      if (evt && evt.button !== 0) return;
      this.deseleccionarEnlace();
      this.deseleccionarCapsula();
      this.relationshipService.cancelarRelacionPendiente();
      this.cerrarModales$.next();
      this.cameraService.iniciarPaneo(evt);
    });
  }

  public clientToLocalPoint(clientX: number, clientY: number): { x: number; y: number } {
    if (!this.paper) return { x: clientX, y: clientY };
    const p = this.paper.clientToLocalPoint({ x: clientX, y: clientY });
    return { x: Math.round(p.x), y: Math.round(p.y) };
  }
}
