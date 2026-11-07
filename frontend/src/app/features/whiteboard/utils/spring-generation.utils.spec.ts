import {
  EstadoGeneracionSpring,
  motivoBloqueoSpring,
  normalizarNombreProyectoSpring,
  puedeExportarSpring,
  puedeGenerarSpring
} from './spring-generation.utils';


describe('estado seguro de generación Spring', () => {
  const listo: EstadoGeneracionSpring = {
    proyectoId: 7,
    proyectoActivoId: 7,
    rol: 'propietario',
    conexion: 'conectado',
    guardado: 'guardado',
    conflicto: false,
    generando: false
  };

  it('normaliza el nombre del proyecto como artifactId portable', () => {
    expect(normalizarNombreProyectoSpring('fisica III')).toBe('fisica-iii');
    expect(normalizarNombreProyectoSpring('  F\u00edsica__III  ')).toBe('fisica-iii');
    expect(normalizarNombreProyectoSpring('calculo-2026')).toBe('calculo-2026');
  });

  it('autoriza propietario, editor y visualizador activos', () => {
    expect(puedeExportarSpring('propietario')).toBeTrue();
    expect(puedeExportarSpring('editor')).toBeTrue();
    expect(puedeExportarSpring('visualizador')).toBeTrue();
  });

  it('rechaza pendiente, retirado, externo y rol desconocido', () => {
    for (const rol of ['pendiente', 'retirado', 'externo', '']) {
      expect(puedeExportarSpring(rol)).withContext(rol).toBeFalse();
    }
  });

  it('exige confirmación, conexión, ausencia de conflicto y proyecto coincidente', () => {
    expect(puedeGenerarSpring(listo)).toBeTrue();
    expect(puedeGenerarSpring({ ...listo, guardado: 'guardando' })).toBeFalse();
    expect(motivoBloqueoSpring({ ...listo, guardado: 'guardando' })).toContain('autoguardado');
    expect(puedeGenerarSpring({ ...listo, conflicto: true })).toBeFalse();
    expect(puedeGenerarSpring({ ...listo, conexion: 'desconectado' })).toBeFalse();
    expect(puedeGenerarSpring({ ...listo, proyectoActivoId: 8 })).toBeFalse();
    expect(puedeGenerarSpring({ ...listo, generando: true })).toBeFalse();
  });
});
