import { objetivoVisible, puedeValidarModelo } from './validation.utils';
import { HallazgoValidacion } from '../interfaces/validation.interface';

describe('validation.utils', () => {
  it('permite validar un proyecto conectado y guardado', () => {
    expect(puedeValidarModelo(7, 'conectado', 'guardado', false)).toBeTrue();
  });

  it('bloquea la validacion con cambios pendientes, desconexion o una solicitud activa', () => {
    expect(puedeValidarModelo(7, 'conectado', 'guardando', false)).toBeFalse();
    expect(puedeValidarModelo(7, 'desconectado', 'guardado', false)).toBeFalse();
    expect(puedeValidarModelo(7, 'conectado', 'guardado', true)).toBeFalse();
  });

  it('localiza directamente relaciones y clasificadores', () => {
    const base = { codigo: 'X', severidad: 'error', mensaje: 'x' } as const;
    expect(objetivoVisible({ ...base, objetivo: { tipo: 'relacion', id: 4 } })).toEqual({ tipo: 'relacion', id: 4 });
    expect(objetivoVisible({ ...base, objetivo: { tipo: 'clasificador', id: 8 } })).toEqual({ tipo: 'clasificador', id: 8 });
  });

  it('lleva atributos, operaciones y parametros a su clasificador', () => {
    const hallazgo = {
      codigo: 'X', severidad: 'warning', mensaje: 'x',
      objetivo: { tipo: 'atributo', id: 5, clasificador_id: 12 }
    } as HallazgoValidacion;
    expect(objetivoVisible(hallazgo)).toEqual({ tipo: 'clasificador', id: 12 });
  });
});
