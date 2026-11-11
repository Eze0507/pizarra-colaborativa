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
});
