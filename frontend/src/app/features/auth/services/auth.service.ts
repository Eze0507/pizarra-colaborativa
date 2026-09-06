import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, of, finalize } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { TokenStorageService } from '../../../core/services/token-storage.service';
import { LoginRequest } from '../interfaces/login-request.interface';
import { LoginResponse } from '../interfaces/login-response.interface';
import { RegisterRequest } from '../interfaces/register-request.interface';
import { RegisterResponse } from '../interfaces/register-response.interface';
import { LogoutRequest, LogoutResponse } from '../interfaces/logout.interface';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly tokenStorage = inject(TokenStorageService);

  private readonly baseUrl = `${environment.apiUrl}/usuario`;

  public login(credentials: LoginRequest): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.baseUrl}/login/`, credentials).pipe(
      tap((response: LoginResponse) => {
        this.tokenStorage.saveTokens(response.access, response.refresh);
        this.tokenStorage.saveUser(response.user);
      })
    );
  }

  public register(data: RegisterRequest): Observable<RegisterResponse> {
    return this.http.post<RegisterResponse>(`${this.baseUrl}/registro/`, data);
  }

  public logout(): Observable<LogoutResponse | null> {
    const refreshToken = this.tokenStorage.getRefreshToken();

    if (!refreshToken) {
      this.tokenStorage.clear();
      this.router.navigate(['/login']);
      return of(null);
    }

    const body: LogoutRequest = { refresh: refreshToken };

    return this.http.post<LogoutResponse>(`${this.baseUrl}/logout/`, body).pipe(
      catchError(() => of(null)),
      finalize(() => {
        this.tokenStorage.clear();
        this.router.navigate(['/login']);
      })
    );
  }

  public isAuthenticated(): boolean {
    return this.tokenStorage.isAuthenticated();
  }
}
