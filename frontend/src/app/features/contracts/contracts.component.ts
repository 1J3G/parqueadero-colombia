import { HttpClient } from '@angular/common/http';
import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../core/auth.service';

interface Customer {
  id: number;
  document_type: string;
  document: string;
  full_name: string;
}

interface Contract {
  id: number;
  customer_id: number;
  plate: string;
  vehicle_type: string;
  status: string;
  starts_on: string | null;
  expires_on: string | null;
  customer_document: string;
  customer_full_name: string;
}

@Component({
  selector: 'app-contracts',
  standalone: true,
  imports: [FormsModule, DatePipe],
  templateUrl: './contracts.component.html',
})
export class ContractsComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  readonly isAdministrator = computed(() => this.auth.currentUser()?.role === 'Administrador');
  readonly customers = signal<Customer[]>([]);
  readonly contracts = signal<Contract[]>([]);
  readonly customerType = signal('CC');
  readonly customerDocument = signal('');
  readonly customerName = signal('');
  readonly selectedCustomer = signal<number | null>(null);
  readonly plate = signal('');
  readonly vehicleType = signal('Carro');
  readonly contractToChange = signal<number | null>(null);
  readonly replacementPlate = signal('');
  readonly contractToCancel = signal<number | null>(null);
  readonly cancellationJustification = signal('');

  setSelectedCustomer(value: string | number | null): void {
    this.selectedCustomer.set(value === null || value === '' ? null : Number(value));
  }

  setContractToChange(value: string | number | null): void {
    this.contractToChange.set(value === null || value === '' ? null : Number(value));
  }

  setContractToCancel(value: string | number | null): void {
    this.contractToCancel.set(value === null || value === '' ? null : Number(value));
  }

  ngOnInit(): void {
    this.refresh();
  }

  createCustomer(): void {
    this.http
      .post<Customer>('/api/customers', {
        document_type: this.customerType(),
        document: this.customerDocument().trim(),
        full_name: this.customerName().trim(),
      })
      .subscribe({ next: () => this.refresh() });
  }

  createContract(): void {
    if (this.selectedCustomer() === null) {
      return;
    }
    this.http
      .post<Contract>('/api/contracts', {
        customer_id: this.selectedCustomer(),
        plate: this.plate().trim().toUpperCase(),
        vehicle_type: this.vehicleType(),
      })
      .subscribe({ next: () => this.refresh() });
  }

  changePlate(): void {
    const contractId = this.contractToChange();
    if (!contractId) {
      return;
    }
    this.http
      .patch(`/api/contracts/${contractId}/plate`, { plate: this.replacementPlate().trim().toUpperCase() })
      .subscribe({ next: () => this.refresh() });
  }

  cancelContract(): void {
    const contractId = this.contractToCancel();
    const justification = this.cancellationJustification().trim();
    if (!contractId || !justification) {
      return;
    }
    this.http
      .post(`/api/contracts/${contractId}/cancel`, { justification })
      .subscribe({
        next: () => {
          this.contractToCancel.set(null);
          this.cancellationJustification.set('');
          this.refresh();
        },
      });
  }

  private refresh(): void {
    this.http.get<Customer[]>('/api/customers').subscribe({ next: (items) => this.customers.set(items) });
    this.http.get<Contract[]>('/api/contracts').subscribe({ next: (items) => this.contracts.set(items) });
  }
}
