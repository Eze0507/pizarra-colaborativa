import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { SidebarPizarraComponent } from './sidebar-pizarra.component';
import { ProyectoDiagrama } from '../../interfaces/diagrama.interface';
import { ResultadoValidacion } from '../../interfaces/validation.interface';

describe('SidebarPizarraComponent - validacion F03', () => {
  let http: HttpTestingController;
  const proyecto: ProyectoDiagrama = {
    id: 9, codigo: 'P9', nombre: 'Modelo', descripcion: '', paquete_base: '',
    datos_diagrama: null, propietario: 'owner', es_propietario: false,
    rol_usuario: 'visualizador', fecha_actualizacion: '2026-11-04T00:00:00Z', revision: 0
  };
  const resultado: ResultadoValidacion = {
    origen: 'orm', proyecto_id: 9, fecha_actualizacion: null, perfil: 'java', valido: false,
    resumen: { errores: 1, advertencias: 1, informativos: 1 },
    hallazgos: [
      { codigo: 'E', severidad: 'error', mensaje: 'Error', objetivo: { tipo: 'clasificador', id: 1 } },
      { codigo: 'W', severidad: 'warning', mensaje: 'Aviso', objetivo: { tipo: 'relacion', id: 2 } },
      { codigo: 'I', severidad: 'info', mensaje: 'Dato', objetivo: { tipo: 'proyecto', id: 9 } },
    ]
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [SidebarPizarraComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function create() {
    const fixture = TestBed.createComponent(SidebarPizarraComponent);
    fixture.componentInstance.proyecto = proyecto;
    fixture.componentInstance.estadoConexion = 'conectado';
    fixture.componentInstance.estadoGuardado = 'guardado';
    fixture.detectChanges();
    return fixture;
  }

  it('ofrece los tres perfiles y selecciona UML inicialmente', () => {
    const fixture = create();
    const options = Array.from(fixture.nativeElement.querySelectorAll('.validation-controls option')) as HTMLOptionElement[];
    expect(options.map(item => item.value)).toEqual(['uml', 'java', 'jpa']);
    expect(fixture.componentInstance.perfilValidacion).toBe('uml');
  });

  it('permite al visualizador validar el ORM guardado con el perfil elegido', () => {
    const fixture = create();
    fixture.componentInstance.perfilValidacion = 'java';
    fixture.componentInstance.ejecutarValidacion();
    const request = http.expectOne(req => req.url.endsWith('/modelado/proyectos/9/validacion/'));
    expect(request.request.method).toBe('GET');
    expect(request.request.params.get('perfil')).toBe('java');
    request.flush(resultado);
    expect(fixture.componentInstance.resultadoValidacion?.origen).toBe('orm');
  });

  it('presenta errores, advertencias, informacion y el resumen', () => {
    const fixture = create();
    fixture.componentInstance.resultadoValidacion = resultado;
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('1 errores');
    expect(text).toContain('1 advertencias');
    expect(text).toContain('1 informativos');
    expect(fixture.nativeElement.querySelectorAll('.validation-finding').length).toBe(3);
    expect(text).toContain('ORM');
  });

  it('emite el hallazgo seleccionado para localizarlo sin modificar el diagrama', () => {
    const fixture = create();
    fixture.componentInstance.resultadoValidacion = resultado;
    const emit = spyOn(fixture.componentInstance.localizarHallazgo, 'emit');
    fixture.detectChanges();
    (fixture.nativeElement.querySelector('.validation-finding') as HTMLButtonElement).click();
    expect(emit).toHaveBeenCalledWith(resultado.hallazgos[0]);
  });

  it('bloquea desconexion, guardado en progreso y error de guardado', () => {
    const fixture = create();
    for (const state of ['guardando', 'error'] as const) {
      fixture.componentInstance.estadoGuardado = state;
      expect(fixture.componentInstance.puedeValidar).toBeFalse();
    }
    fixture.componentInstance.estadoGuardado = 'guardado';
    fixture.componentInstance.estadoConexion = 'desconectado';
    fixture.componentInstance.ejecutarValidacion();
    expect(fixture.componentInstance.errorValidacion).toContain('Guarda y sincroniza');
  });

  it('expone errores HTTP 400 y 403 sin conservar una solicitud activa', () => {
    const fixture = create();
    fixture.componentInstance.ejecutarValidacion();
    http.expectOne(req => req.url.includes('/validacion/')).flush(
      { detail: 'Perfil inválido.' }, { status: 400, statusText: 'Bad Request' }
    );
    expect(fixture.componentInstance.errorValidacion).toBe('Perfil inválido.');
    fixture.componentInstance.ejecutarValidacion();
    http.expectOne(req => req.url.includes('/validacion/')).flush(
      {}, { status: 403, statusText: 'Forbidden' }
    );
    expect(fixture.componentInstance.errorValidacion).toContain('permiso');
    expect(fixture.componentInstance.validandoModelo).toBeFalse();
  });

  it('reutiliza un unico boton principal Generacion Java', () => {
    const fixture = create();
    const emit = spyOn(fixture.componentInstance.generarCodigo, 'emit');
    const buttons = Array.from(
      fixture.nativeElement.querySelectorAll('.btn-cta-estrella')
    ) as HTMLButtonElement[];
    expect(buttons.length).toBe(1);
    expect(buttons[0].textContent).toContain('Generación Java');
    buttons[0].click();
    expect(emit).toHaveBeenCalledTimes(1);
  });
});
