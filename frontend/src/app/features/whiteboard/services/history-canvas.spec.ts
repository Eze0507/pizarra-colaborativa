import { TestBed } from '@angular/core/testing';
import * as joint from '@joint/core';
import { WhiteboardEntityService } from './whiteboard-entity.service';
import { WhiteboardRelationshipService } from './whiteboard-relationship.service';
import { WhiteboardCanvasService } from './whiteboard-canvas.service';
import { WhiteboardCameraService } from './whiteboard-camera.service';
import { WhiteboardApiService } from './whiteboard-api.service';
import { provideHttpClient } from '@angular/common/http';

describe('Rehidratación JointJS del historial', () => {
  let entities: WhiteboardEntityService;
  let relations: WhiteboardRelationshipService;
  let graph: joint.dia.Graph;
  let paper: joint.dia.Paper;
  let element: HTMLDivElement;
  const theme: any = { headerTexto: '#222', bodyTexto: '#222', entidadBorde: '#555', headerBorde: '#555', entidadFondo: '#fff' };
  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [WhiteboardEntityService, WhiteboardRelationshipService, WhiteboardCameraService, provideHttpClient()] });
    entities = TestBed.inject(WhiteboardEntityService);
    relations = TestBed.inject(WhiteboardRelationshipService);
    element = document.createElement('div'); document.body.appendChild(element);
    graph = new joint.dia.Graph({}, { cellNamespace: joint.shapes });
    paper = new joint.dia.Paper({ el: element, model: graph, width: 800, height: 600, cellViewNamespace: joint.shapes });
    entities.conectar(graph, paper, element); relations.conectar(graph, paper);
  });
  afterEach(() => { relations.desconectar(); entities.desconectar(); paper.remove(); element.remove(); });
  function add(id: number): void {
    entities.crearCeldaRemota({ id, nombre: `Clase${id}`, coord_x: id * 100 + .5, coord_y: 20.25, ancho: 550, estado: 'activo', atributos: [], operaciones: [] }, theme);
  }
  it('conserva IDs, dimensiones y posiciones fraccionarias al volver a cargar', () => {
    add(3);
    const original = entities.getEntidades();
    expect(entities.getCelda(3)?.size().width).toBe(550);
    expect(original[0].coord_x).toBe(300.5);
    graph.clear(); entities.limpiar();
    entities.renderizarEntidades(original, theme);
    expect(entities.getEntidades()).toEqual(original);
  });
  it('movimientos remotos de presencia no entran en un snapshot local', () => {
    add(1);
    entities.moverCeldaRemota(1, 700, 800);
    expect(entities.getCelda(1)?.position().x).toBe(700);
    expect(entities.getCelda(1)?.position().y).toBe(800);
    expect(entities.getEntidades()[0].coord_x).toBe(100.5);
    expect(entities.obtenerPosiciones()[1]).toEqual({ x: 100.5, y: 20.25 });
  });
  it('recupera los vértices y puertos persistidos sin duplicar enlaces', () => {
    add(1); add(2);
    const relation: any = { id: 40, entidad_origen_id: 1, entidad_destino_id: 2, tipo: 'asociacion', nombre_relacion: 'usa', cardinalidad_origen: '1', cardinalidad_destino: '*', puerto_origen: 'right-1', puerto_destino: 'left-1', vertices: [{ x: 120, y: 230 }] };
    relations.crearRelacionRemota(relation, false);
    relations.crearRelacionRemota(relation, false);
    expect(graph.getLinks().length).toBe(1);
    expect(graph.getLinks()[0].vertices()).toEqual(relation.vertices);
    const snapshot = relations.getRelaciones();
    snapshot[0].vertices![0].x = 999;
    expect(relations.getRelaciones()[0].vertices).toEqual([{ x: 120, y: 230 }]);
  });
  it('la carga REST conserva cardinalidades y no inventa referencias de asociación', () => {
    const api = TestBed.inject(WhiteboardApiService);
    const data: any = { proyecto: { datos_diagrama: {} }, entidades: [{ id: 3, es_intermedia: true, atributos: [] }],
      relaciones: [{ id: 8, entidad_origen_id: 1, entidad_destino_id: 2, tipo: 'asociacion', cardinalidad_origen: '*', cardinalidad_destino: '1' }] };
    const result = (api as any).reconciliarDatosDiagrama(data);
    expect(result.relaciones[0].cardinalidad_origen).toBe('*');
    expect(result.relaciones[0].clase_asociacion_id).toBeNull();
  });

  it('reactiva las vistas existentes despues de salir del modo solo lectura', () => {
    const canvas = TestBed.runInInjectionContext(() => new WhiteboardCanvasService());
    const graphCanvas = new joint.dia.Graph({}, { cellNamespace: joint.shapes });
    const paperCanvas = new joint.dia.Paper({
      el: document.createElement('div'),
      model: graphCanvas,
      width: 300,
      height: 200,
      cellViewNamespace: joint.shapes,
      interactive: { linkMove: false }
    });
    const clase = new joint.shapes.standard.Rectangle();
    clase.addTo(graphCanvas);
    const vista = paperCanvas.findViewByModel(clase)!;
    (canvas as any).paper = paperCanvas;

    canvas.setSoloLectura(true);
    expect(vista.can('elementMove')).toBeFalse();

    canvas.setSoloLectura(false);
    expect(vista.can('elementMove')).toBeTrue();
    expect(vista.can('linkMove')).toBeFalse();

    paperCanvas.remove();
  });
});
