import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpErrorResponse, HttpHeaders, HttpResponse } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { firstValueFrom } from 'rxjs';

import { jwtInterceptor } from '../../../core/interceptors/jwt.interceptor';
import { TokenStorageService } from '../../../core/services/token-storage.service';
import { GeneradorService } from './generador.service';


describe('GeneradorService Spring Boot', () => {
  let service: GeneradorService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        GeneradorService,
        provideHttpClient(withInterceptors([jwtInterceptor])),
        provideHttpClientTesting(),
        { provide: TokenStorageService, useValue: { getAccessToken: () => 'jwt-prueba' } }
      ]
    });
    service = TestBed.inject(GeneradorService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('envia POST autenticado, revision y opciones esperando Blob observado', async () => {
    const promise = firstValueFrom(service.generarSpringBoot(7, {
      expected_revision: 12,
      nombre_proyecto: 'tienda',
      paquete_base: 'com.ejemplo.tienda',
      opciones: { modelo: true, repositorio: false, servicio: false, controlador: false }
    }));
    const request = http.expectOne(req => req.url.endsWith('/generador/proyectos/7/spring-boot/'));
    expect(request.request.method).toBe('POST');
    expect(request.request.headers.get('Authorization')).toBe('Bearer jwt-prueba');
    expect(request.request.responseType).toBe('blob');
    expect(request.request.body.expected_revision).toBe(12);
    request.flush(zipBlob(), {
      headers: {
        'Content-Type': 'application/zip',
        'Content-Disposition': 'attachment; filename="tienda.zip"'
      }
    });
    expect((await promise).body?.size).toBeGreaterThan(0);
  });

  it('cancela la solicitud HTTP al cerrar o cambiar de proyecto', () => {
    const subscription = service.generarSpringBoot(7, {
      expected_revision: 12,
      nombre_proyecto: 'tienda',
      paquete_base: 'com.ejemplo.tienda',
      opciones: { modelo: true, repositorio: false, servicio: false, controlador: false }
    }).subscribe();
    const request = http.expectOne(req => req.url.endsWith('/generador/proyectos/7/spring-boot/'));
    subscription.unsubscribe();
    expect(request.cancelled).toBeTrue();
  });

  it('valida firma ZIP y usa filename seguro o fallback', async () => {
    const prepared = await service.prepararDescargaSpring(
      new HttpResponse({
        body: zipBlob(), headers: new HttpHeaders({
          'Content-Type': 'application/zip',
          'Content-Disposition': "attachment; filename*=UTF-8''tienda-segura.zip"
        })
      }),
      'fallback'
    );
    expect(prepared.filename).toBe('tienda-segura.zip');

    const unsafe = new HttpResponse({
      body: zipBlob(),
      headers: new HttpHeaders({
        'Content-Type': 'application/zip',
        'Content-Disposition': 'attachment; filename="../../mal:icioso.zip"'
      })
    });
    expect((await service.prepararDescargaSpring(unsafe, 'proyecto-valido')).filename)
      .toBe('malicioso.zip');
  });

  it('rechaza JSON o bytes sin firma como descarga exitosa', async () => {
    const invalid = new HttpResponse({
      body: new Blob(['{"code":"error"}'], { type: 'application/json' }),
      headers: new HttpHeaders({ 'Content-Type': 'application/json' })
    });
    await expectAsync(service.prepararDescargaSpring(invalid, 'tienda')).toBeRejected();
  });

  it('extrae errores JSON contenidos en Blob sin mostrar object Blob', async () => {
    const error = new HttpErrorResponse({
      status: 409,
      error: new Blob([
        JSON.stringify({ code: 'stale_revision', message: 'El diagrama cambió.' })
      ], { type: 'application/json' })
    });
    const parsed = await service.leerErrorGeneracion(error);
    expect(parsed.code).toBe('stale_revision');
    expect(parsed.message).toBe('El diagrama cambió.');
  });

  it('resume perfil, diagnostico, elemento y accion sin modificar el modelo', () => {
    const message = service.describirErrorGeneracion({
      code: 'generation_validation_failed',
      message: 'El modelo no es válido.',
      details: {
        perfil: 'jpa',
        diagnosticos: [{
          codigo: 'JPA_ENTITY_WITHOUT_ID', mensaje: 'Falta una clave.',
          objetivo: { tipo: 'clasificador', id: 9 }
        }]
      }
    });
    expect(message).toContain('Perfil: jpa');
    expect(message).toContain('JPA_ENTITY_WITHOUT_ID');
    expect(message).toContain('clasificador 9');
    expect(message).toContain('no realizará correcciones automáticas');
  });

  it('crea, pulsa, retira y revoca el Object URL', fakeAsync(() => {
    spyOn(window.URL, 'createObjectURL').and.returnValue('blob:prueba');
    spyOn(window.URL, 'revokeObjectURL');
    const click = spyOn(HTMLAnchorElement.prototype, 'click');
    service.iniciarDescarga({ blob: zipBlob(), filename: 'tienda.zip' });
    expect(click).toHaveBeenCalled();
    expect(document.querySelector('a[download="tienda.zip"]')).toBeNull();
    tick();
    expect(window.URL.revokeObjectURL).toHaveBeenCalledWith('blob:prueba');
  }));
});

function zipBlob(): Blob {
  return new Blob([new Uint8Array([0x50, 0x4b, 0x03, 0x04, 0x00])], { type: 'application/zip' });
}
