import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, finalize, map, of, shareReplay, tap, throwError } from 'rxjs';

export interface CurrentUser {
  document: string;
  role: 'Operario' | 'Administrador';
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private restoreRequest: Observable<CurrentUser | null> | null = null;
  private restored = false;
  readonly currentUser = signal<CurrentUser | null>(null);

  login(document: string, password: string): Observable<CurrentUser> {
    return this.http
      .post<CurrentUser>('/api/auth/login', { document, password })
      .pipe(tap((user) => this.setUser(user)));
  }

  restoreSession(): Observable<CurrentUser | null> {
    if (this.restored) {
      return of(this.currentUser());
    }
    if (this.restoreRequest) {
      return this.restoreRequest;
    }
    this.restoreRequest = this.http.get<CurrentUser>('/api/auth/me').pipe(
      tap((user) => this.setUser(user)),
      map((user) => user),
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401) {
          this.setUser(null);
          return of(null);
        }
        return throwError(() => error);
      }),
      tap(() => (this.restored = true)),
      finalize(() => (this.restoreRequest = null)),
      shareReplay(1),
    );
    return this.restoreRequest;
  }

  logout(): Observable<void> {
    return this.http.post<void>('/api/auth/logout', {}).pipe(tap(() => this.setUser(null)));
  }

  private setUser(user: CurrentUser | null): void {
    this.currentUser.set(user);
    this.restored = true;
  }
}
