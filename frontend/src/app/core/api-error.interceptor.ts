import { HttpErrorResponse, HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, tap, throwError } from 'rxjs';
import { ApiErrorService } from './api-error.service';
import { ApiSuccessService } from './api-success.service';

export const apiErrorInterceptor: HttpInterceptorFn = (request, next) => {
  const errors = inject(ApiErrorService);
  const successes = inject(ApiSuccessService);
  const apiRequest = request.url.startsWith('/api')
    ? request.clone({ withCredentials: true })
    : request;
  if (apiRequest.url.startsWith('/api') && apiRequest.method !== 'GET') {
    successes.clear();
  }

  return next(apiRequest).pipe(
    tap((event) => {
      if (event instanceof HttpResponse && event.status === 201) {
        errors.clear();
        successes.show('El registro se creó exitosamente.');
      }
    }),
    catchError((error: unknown) => {
      const isExpectedSessionMiss =
        error instanceof HttpErrorResponse &&
        error.status === 401 &&
        request.url === '/api/auth/me';
      if (!isExpectedSessionMiss) {
        const message = error instanceof HttpErrorResponse ? getUserMessage(error) : 'Ocurrió un error inesperado.';
        errors.show(message);
      }
      return throwError(() => error);
    }),
  );
};

function getUserMessage(error: HttpErrorResponse): string {
  const detail = error.error?.detail;
  if (typeof detail === 'string') {
    return detail;
  }
  if (error.status === 0) {
    return 'No fue posible conectar con el servidor.';
  }
  if (error.status === 401) {
    return 'La sesión no está activa o las credenciales no son válidas.';
  }
  if (error.status === 403) {
    return 'No tiene autorización para realizar esta operación.';
  }
  if (error.status === 409) {
    return 'La operación entra en conflicto con el estado actual.';
  }
  if (error.status >= 500) {
    return 'El servidor no pudo completar la operación.';
  }
  return 'Revise la información ingresada e intente nuevamente.';
}
