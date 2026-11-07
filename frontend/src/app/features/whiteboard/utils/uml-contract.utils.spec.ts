import { EntidadDiagrama, RelacionDiagrama } from '../interfaces/diagrama.interface';
import { aplicarMapasIds, etiquetaAtributo, etiquetaOperacion } from './uml-contract.utils';

describe('contrato UML del lienzo', () => {
  const contrato: EntidadDiagrama = {
    id: 8, nombre: 'Pagable', estado: 'activo', coord_x: 0, coord_y: 0, ancho: 220,
    tipo_clasificador: 'interfaz', abstracto: true, atributos: [], operaciones: []
  };
  const entidades = new Map([[8, contrato]]);

  it('formatea visibilidad, referencias, parámetros y retorno sin perder semántica', () => {
    expect(etiquetaAtributo({ id: 1, nombre: 'contrato', tipo: 'string', tipo_referencia_id: 8,
      visibilidad: 'protected', es_estatico: false, es_clave: false, es_nulo: false,
      valor_predeterminado: '', orden: 1 }, entidades)).toBe('# contrato : Pagable');
    expect(etiquetaOperacion({ id: 2, nombre: 'pagar', visibilidad: 'public', tipo_retorno: 'void',
      retorno_referencia_id: 8, orden: 1, es_estatico: false, es_abstracto: true,
      parametros: [{ id: 3, nombre: 'entrada', tipo: 'string', tipo_referencia_id: 8, orden: 1 }] }, entidades))
      .toBe('+ pagar(entrada: Pagable) : Pagable');
  });

  it('representa una referencia eliminada como no resuelta', () => {
    expect(etiquetaAtributo({ id: 1, nombre: 'x', tipo: 'string', tipo_referencia_id: 99,
      visibilidad: 'private', es_estatico: false, es_clave: false, es_nulo: false,
      valor_predeterminado: '', orden: 1 }, entidades)).toContain('«no resuelto:99»');
  });

  it('aplica los cinco mapas y todas las referencias cruzadas de forma inmutable', () => {
    const local: EntidadDiagrama = { ...contrato, id: -1,
      atributos: [{ id: -2, nombre: 'a', tipo: 'string', tipo_referencia_id: -1, es_clave: false, es_nulo: false, orden: 1 }],
      operaciones: [{ id: -3, nombre: 'o', visibilidad: 'public', tipo_retorno: 'void', retorno_referencia_id: -1,
        orden: 1, es_estatico: false, es_abstracto: false,
        parametros: [{ id: -4, nombre: 'p', tipo: 'string', tipo_referencia_id: -1, orden: 1 }] }]
    };
    const relacion: RelacionDiagrama = { id: -5, nombre_relacion: '', tipo: 'asociacion',
      entidad_origen_id: -1, entidad_destino_id: -1, clase_asociacion_id: -1,
      cardinalidad_origen: '1', cardinalidad_destino: '*', rol_origen: '', rol_destino: '',
      navegable_origen: false, navegable_destino: true };
    const result = aplicarMapasIds([local], [relacion], { id_map: {'-1': 10}, attr_id_map: {'-2': 20},
      operation_id_map: {'-3': 30}, parameter_id_map: {'-4': 40}, rel_id_map: {'-5': 50} });
    expect(result.entidades[0].id).toBe(10);
    expect(result.entidades[0].atributos[0]).toEqual(jasmine.objectContaining({id: 20, tipo_referencia_id: 10}));
    expect(result.entidades[0].operaciones?.[0].parametros[0]).toEqual(jasmine.objectContaining({id: 40, tipo_referencia_id: 10}));
    expect(result.relaciones[0]).toEqual(jasmine.objectContaining({id: 50, entidad_origen_id: 10, clase_asociacion_id: 10}));
    expect(local.id).toBe(-1);
  });
});
