import { Injectable } from '@angular/core';
import { User } from '../../features/auth/interfaces/user.interface';

@Injectable({
  providedIn: 'root'
})
export class TokenStorageService {
  private readonly accessTokenKey = 'auth_access_token';
  private readonly refreshTokenKey = 'auth_refresh_token';
  private readonly userKey = 'auth_user';

  public saveTokens(access: string, refresh: string): void {
    localStorage.setItem(this.accessTokenKey, access);
    localStorage.setItem(this.refreshTokenKey, refresh);
  }

  public saveUser(user: User): void {
    localStorage.setItem(this.userKey, JSON.stringify(user));
  }

  public getAccessToken(): string | null {
    return localStorage.getItem(this.accessTokenKey);
  }

  public getRefreshToken(): string | null {
    return localStorage.getItem(this.refreshTokenKey);
  }

  public getUser(): User | null {
    const raw = localStorage.getItem(this.userKey);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  }

  public clear(): void {
    localStorage.removeItem(this.accessTokenKey);
    localStorage.removeItem(this.refreshTokenKey);
    localStorage.removeItem(this.userKey);
  }

  public isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }
}
