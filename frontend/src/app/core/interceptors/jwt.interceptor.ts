import { HttpClient, HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, finalize, shareReplay, switchMap, tap, throwError } from 'rxjs';
import { environment } from '../../../environments/environment';
import { TokenStorageService } from '../services/token-storage.service';

interface TokenRefreshResponse {
  access: string;
  refresh?: string;
}

let refreshRequest$: Observable<TokenRefreshResponse> | null = null;

export const jwtInterceptor: HttpInterceptorFn = (req, next) => {
  const tokenStorage = inject(TokenStorageService);
  const http = inject(HttpClient);
  const router = inject(Router);
  const token = tokenStorage.getAccessToken();
  const refreshUrl = `${environment.apiUrl}/usuario/token/refresh/`;

  if (req.url === refreshUrl) return next(req);

  const requestWithToken = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(requestWithToken).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status !== 401) return throwError(() => error);

      const refreshToken = tokenStorage.getRefreshToken();
      if (!refreshToken) {
        tokenStorage.clear();
        void router.navigate(['/login']);
        return throwError(() => error);
      }

      if (!refreshRequest$) {
        refreshRequest$ = http.post<TokenRefreshResponse>(refreshUrl, { refresh: refreshToken }).pipe(
          tap(response => {
            tokenStorage.saveTokens(response.access, response.refresh || refreshToken);
          }),
          catchError(refreshError => {
            tokenStorage.clear();
            void router.navigate(['/login']);
            return throwError(() => refreshError);
          }),
          finalize(() => { refreshRequest$ = null; }),
          shareReplay({ bufferSize: 1, refCount: false })
        );
      }

      return refreshRequest$.pipe(
        switchMap(response => next(req.clone({
          setHeaders: { Authorization: `Bearer ${response.access}` }
        })))
      );
    })
  );
};
