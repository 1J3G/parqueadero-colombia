import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { apiErrorInterceptor } from './api-error.interceptor';
import { ApiErrorService } from './api-error.service';
import { ApiSuccessService } from './api-success.service';

describe('apiErrorInterceptor', () => {
  let http: HttpClient;
  let controller: HttpTestingController;
  let errors: ApiErrorService;
  let successes: ApiSuccessService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([apiErrorInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpClient);
    controller = TestBed.inject(HttpTestingController);
    errors = TestBed.inject(ApiErrorService);
    successes = TestBed.inject(ApiSuccessService);
  });

  afterEach(() => controller.verify());

  it('confirms successfully created records', () => {
    http.post('/api/customers', {}).subscribe();
    controller.expectOne('/api/customers').flush({}, { status: 201, statusText: 'Created' });

    expect(successes.message()).toBe('El registro se creó exitosamente.');
    expect(errors.message()).toBe('');
  });

  it('does not confirm a failed creation', () => {
    http.post('/api/customers', {}).subscribe({ error: () => undefined });
    controller.expectOne('/api/customers').flush(
      { detail: 'Conflicto' },
      { status: 409, statusText: 'Conflict' },
    );

    expect(successes.message()).toBe('');
    expect(errors.message()).toBe('Conflicto');
  });
});
