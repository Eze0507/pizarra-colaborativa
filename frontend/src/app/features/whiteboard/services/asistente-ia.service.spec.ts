import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { AsistenteIaService } from './asistente-ia.service';

describe('AsistenteIaService: IDs temporales del boceto', () => {
  let service: AsistenteIaService;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient()] });
    service = TestBed.inject(AsistenteIaService);
  });

  it('genera IDs de atributos únicos entre varias entidades', () => {
    spyOn(Date, 'now').and.returnValue(1_700_000_000_000);

    const resultado = service.normalizarRespuestaIA({
      entidades: [
        { id: 1, nombre: 'vehiculo', atributos: [
          { nombre: 'placa', tipo: 'string', es_clave: true },
          { nombre: 'marca', tipo: 'string' }
        ] },
        { id: 2, nombre: 'camion', atributos: [
          { nombre: 'id', tipo: 'integer', es_clave: true },
          { nombre: 'capacidad', tipo: 'double' }
        ] },
        { id: 3, nombre: 'auto', atributos: [
          { nombre: 'modelo', tipo: 'string' }
        ] }
      ],
      relaciones: [
        { entidad_origen_id: 2, entidad_destino_id: 1, tipo: 'herencia' },
        { entidad_origen_id: 3, entidad_destino_id: 1, tipo: 'herencia' }
      ]
    });

    const idsAtributos = resultado.entidades.flatMap(entidad =>
      (entidad.atributos || []).map(atributo => atributo.id)
    );

    expect(new Set(idsAtributos).size).toBe(idsAtributos.length);
    expect(idsAtributos.every(id => id < 0 && Number.isSafeInteger(id))).toBeTrue();
  });

  it('convierte los nombres detectados en identificadores Java 21 validos', () => {
    const resultado = service.normalizarRespuestaIA({
      entidades: [
        {
          id: 1,
          nombre: '123 Calculo / venta',
          atributos: [
            { nombre: 'numero factura', tipo: 'string' },
            { nombre: 'class', tipo: 'string' },
            { nombre: 'total ($)', tipo: 'double' },
            { nombre: 'total $', tipo: 'double' }
          ]
        }
      ],
      relaciones: []
    });

    const entidad = resultado.entidades[0];
    const nombres = (entidad.atributos || []).map(atributo => atributo.nombre);

    expect(entidad.nombre).toBe('Entidad_123_Calculo_venta');
    expect(entidad.tipo_clasificador).toBe('entidad_persistente');
    expect(nombres).toEqual([
      'id',
      'numero_factura',
      'campo_class',
      'total_$',
      'total_$_2'
    ]);
    expect([entidad.nombre, ...nombres].every(nombre => /^[A-Za-z_$][A-Za-z0-9_$]*$/.test(nombre))).toBeTrue();
  });

  it('prepara las jerarquias del boceto como entidades persistentes', () => {
    const resultado = service.normalizarRespuestaIA({
      entidades: [
        { id: 1, nombre: 'Vehiculo', atributos: [{ nombre: 'placa', tipo: 'string', es_clave: true }] },
        { id: 2, nombre: 'Auto', atributos: [{ nombre: 'id', tipo: 'integer', es_clave: true }] }
      ],
      relaciones: [
        { entidad_origen_id: 2, entidad_destino_id: 1, tipo: 'herencia' }
      ]
    });

    expect(resultado.entidades.map(entidad => entidad.tipo_clasificador)).toEqual([
      'entidad_persistente', 'entidad_persistente'
    ]);
    expect(resultado.relaciones[0].tipo).toBe('herencia');
    expect(resultado.entidades[0].atributos.some(atributo => atributo.es_clave)).toBeTrue();
    expect(resultado.entidades[1].atributos.some(atributo => atributo.es_clave)).toBeFalse();
  });
});
