import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { environment } from '../../../environments/environment';
import { TokenStorageService } from '../services/token-storage.service';
import { jwtInterceptor } from './jwt.interceptor';


describe('jwtInterceptor', () => {
  let http: HttpClient;
  let httpTesting: HttpTestingController;
  let tokenStorage: TokenStorageService;
  let router: jasmine.SpyObj<Router>;
  const refreshUrl = `${environment.apiUrl}/usuario/token/refresh/`;

  beforeEach(() => {
    router = jasmine.createSpyObj<Router>('Router', ['navigate']);
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([jwtInterceptor])),
        provideHttpClientTesting(),
        { provide: Router, useValue: router }
      ]
    });
    http = TestBed.inject(HttpClient);
    httpTesting = TestBed.inject(HttpTestingController);
    tokenStorage = TestBed.inject(TokenStorageService);
    tokenStorage.clear();
  });

  afterEach(() => {
    httpTesting.verify();
    tokenStorage.clear();
  });

  it('adjunta el access token vigente', () => {
    tokenStorage.saveTokens('access-vigente', 'refresh-vigente');
    http.get('/api/recurso/').subscribe();

    const request = httpTesting.expectOne('/api/recurso/');
    expect(request.request.headers.get('Authorization')).toBe('Bearer access-vigente');
    request.flush({});
  });

  it('renueva el token vencido y reintenta la solicitud original', () => {
    tokenStorage.saveTokens('access-vencido', 'refresh-vigente');
    let respuesta: unknown;
    http.get('/api/recurso/').subscribe(value => { respuesta = value; });

    const original = httpTesting.expectOne('/api/recurso/');
    original.flush({}, { status: 401, statusText: 'Unauthorized' });

    const refresh = httpTesting.expectOne(refreshUrl);
    expect(refresh.request.headers.has('Authorization')).toBeFalse();
    expect(refresh.request.body).toEqual({ refresh: 'refresh-vigente' });
    refresh.flush({ access: 'access-nuevo', refresh: 'refresh-nuevo' });

    const retry = httpTesting.expectOne('/api/recurso/');
    expect(retry.request.headers.get('Authorization')).toBe('Bearer access-nuevo');
    retry.flush({ ok: true });

    expect(respuesta).toEqual({ ok: true });
    expect(tokenStorage.getAccessToken()).toBe('access-nuevo');
    expect(tokenStorage.getRefreshToken()).toBe('refresh-nuevo');
  });

  it('comparte una sola renovacion entre solicitudes simultaneas', () => {
    tokenStorage.saveTokens('access-vencido', 'refresh-vigente');
    let primeraCompleta = false;
    let segundaCompleta = false;
    http.get('/api/uno/').subscribe(() => { primeraCompleta = true; });
    http.get('/api/dos/').subscribe(() => { segundaCompleta = true; });

    httpTesting.expectOne('/api/uno/').flush({}, { status: 401, statusText: 'Unauthorized' });
    httpTesting.expectOne('/api/dos/').flush({}, { status: 401, statusText: 'Unauthorized' });

    const refresh = httpTesting.expectOne(refreshUrl);
    refresh.flush({ access: 'access-nuevo', refresh: 'refresh-nuevo' });

    const retryUno = httpTesting.expectOne('/api/uno/');
    const retryDos = httpTesting.expectOne('/api/dos/');
    expect(retryUno.request.headers.get('Authorization')).toBe('Bearer access-nuevo');
    expect(retryDos.request.headers.get('Authorization')).toBe('Bearer access-nuevo');
    retryUno.flush({});
    retryDos.flush({});
    httpTesting.expectNone(refreshUrl);
    expect(primeraCompleta).toBeTrue();
    expect(segundaCompleta).toBeTrue();
  });

  it('limpia la sesion y redirige cuando el refresh ya no es valido', () => {
    tokenStorage.saveTokens('access-vencido', 'refresh-vencido');
    http.get('/api/recurso/').subscribe({ error: () => undefined });

    httpTesting.expectOne('/api/recurso/').flush({}, { status: 401, statusText: 'Unauthorized' });
    httpTesting.expectOne(refreshUrl).flush({}, { status: 401, statusText: 'Unauthorized' });

    expect(tokenStorage.getAccessToken()).toBeNull();
    expect(tokenStorage.getRefreshToken()).toBeNull();
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });
});
