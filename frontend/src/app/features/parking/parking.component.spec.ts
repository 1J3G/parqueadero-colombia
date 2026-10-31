import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ParkingComponent } from './parking.component';

describe('ParkingComponent', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [ParkingComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('does not offer another cell when the selected vehicle is already inside', () => {
    const fixture = TestBed.createComponent(ParkingComponent);
    fixture.detectChanges();

    http.expectOne('/api/contracts').flush([
      {
        id: 5,
        plate: 'DHL325',
        vehicle_type: 'Carro',
        status: 'Activo',
        expires_on: '2026-11-30',
        customer_full_name: 'Pedro Franco',
        vehicle_inside: true,
        occupied_cell_label: 'AUT01',
      },
    ]);
    fixture.detectChanges();
    fixture.componentInstance.selectContract(5);
    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;
    expect(element.textContent).toContain('La placa DHL325 ya ocupa la celda AUT01.');
    expect(element.querySelector('select[name="cell"]')).toBeNull();
    expect(element.querySelector('button[type="submit"]')).toBeNull();
    expect(element.querySelector('button.secondary')?.hasAttribute('disabled')).toBe(false);
    http.expectNone((request) => request.url.startsWith('/api/cells'));
  });

  it('offers a new cell after the vehicle exits and its state refreshes', () => {
    const fixture = TestBed.createComponent(ParkingComponent);
    fixture.detectChanges();

    http.expectOne('/api/contracts').flush([
      {
        id: 5,
        plate: 'DHL325',
        vehicle_type: 'Carro',
        status: 'Activo',
        expires_on: '2026-11-30',
        customer_full_name: 'Pedro Franco',
        vehicle_inside: true,
        occupied_cell_label: 'AUT01',
      },
    ]);
    fixture.detectChanges();
    fixture.componentInstance.selectContract(5);
    fixture.componentInstance.registerExit();
    http.expectOne('/api/transits/exit').flush({ direction: 'Salida' });
    http.expectOne('/api/contracts').flush([
      {
        id: 5,
        plate: 'DHL325',
        vehicle_type: 'Carro',
        status: 'Activo',
        expires_on: '2026-11-30',
        customer_full_name: 'Pedro Franco',
        vehicle_inside: false,
        occupied_cell_label: null,
      },
    ]);
    http.expectOne('/api/cells?vehicle_type=Carro').flush([
      { id: 9, label: 'AUT03', category: 'Carro', status: 'Libre' },
    ]);
    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;
    expect(element.querySelector('select[name="cell"]')).not.toBeNull();
    expect(element.textContent).toContain('AUT03 · Carro');
    expect(element.querySelector('button[type="submit"]')).not.toBeNull();
  });
});
