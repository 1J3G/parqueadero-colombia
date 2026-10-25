import { HttpClient } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

interface ParkingContract {
  id: number;
  plate: string;
  vehicle_type: string;
  status: string;
  expires_on: string | null;
  customer_full_name: string;
}

interface ParkingCell {
  id: number;
  label: string;
  category: string;
  status: string;
}

@Component({
  selector: 'app-parking',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './parking.component.html',
})
export class ParkingComponent implements OnInit {
  private readonly http = inject(HttpClient);
  readonly contracts = signal<ParkingContract[]>([]);
  readonly cells = signal<ParkingCell[]>([]);
  readonly contractId = signal<number | null>(null);
  readonly cellId = signal<number | null>(null);
  readonly damageType = signal('Golpe');
  readonly damageDescription = signal('');
  readonly damageSeverity = signal('');
  readonly exceptionalAccess = signal(false);
  readonly administratorDocument = signal('');
  readonly administratorPassword = signal('');
  readonly exceptionalNovelty = signal('');
  readonly submitting = signal(false);
  readonly selectedContract = computed(
    () => this.contracts().find((contract) => contract.id === this.contractId()) ?? null,
  );

  setCellId(value: string | number | null): void {
    this.cellId.set(value === null || value === '' ? null : Number(value));
  }

  ngOnInit(): void {
    this.http.get<ParkingContract[]>('/api/contracts').subscribe({
      next: (contracts) => this.contracts.set(contracts),
    });
  }

  selectContract(value: string | number | null): void {
    const contractId = value === null || value === '' ? null : Number(value);
    this.contractId.set(contractId);
    this.cellId.set(null);
    const contract = this.contracts().find((item) => item.id === contractId);
    if (contract) {
      this.http
        .get<ParkingCell[]>(`/api/cells?vehicle_type=${encodeURIComponent(contract.vehicle_type)}`)
        .subscribe({ next: (cells) => this.cells.set(cells) });
    } else {
      this.cells.set([]);
    }
  }

  registerEntry(): void {
    const selectedContract = this.selectedContract();
    const cellId = this.cellId();
    if (!selectedContract || cellId === null) {
      return;
    }
    const damageDescription = this.damageDescription().trim();
    if (damageDescription && !this.damageSeverity()) {
      return;
    }
    const request: Record<string, unknown> = {
      contract_id: selectedContract.id,
      cell_id: cellId,
      physical_novelties: damageDescription
        ? [
            {
              damage_type: this.damageType(),
              description: damageDescription,
              severity: this.damageSeverity(),
            },
          ]
        : [],
    };
    if (this.exceptionalAccess()) {
      request['exceptional_authorization'] = {
        administrator_document: this.administratorDocument().trim(),
        administrator_password: this.administratorPassword(),
        novelty: this.exceptionalNovelty().trim(),
      };
    }
    this.submitting.set(true);
    this.http.post('/api/transits/entry', request).subscribe({
      next: () => {
        this.exceptionalAccess.set(false);
        this.exceptionalNovelty.set('');
        this.damageDescription.set('');
        this.refreshCells(selectedContract.vehicle_type);
      },
      error: () => this.submitting.set(false),
      complete: () => this.submitting.set(false),
    });
  }

  registerExit(): void {
    const contractId = this.contractId();
    if (!contractId) {
      return;
    }
    this.submitting.set(true);
    this.http.post('/api/transits/exit', { contract_id: contractId }).subscribe({
      next: () => this.refreshCells(this.selectedContract()?.vehicle_type ?? ''),
      error: () => this.submitting.set(false),
      complete: () => this.submitting.set(false),
    });
  }

  private refreshCells(vehicleType: string): void {
    if (!vehicleType) {
      return;
    }
    this.http
      .get<ParkingCell[]>(`/api/cells?vehicle_type=${encodeURIComponent(vehicleType)}`)
      .subscribe({ next: (cells) => this.cells.set(cells) });
  }
}
