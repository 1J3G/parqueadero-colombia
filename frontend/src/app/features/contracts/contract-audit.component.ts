import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';

interface ContractCancellation {
  contract_id: number;
  cancelled_at: string;
  cancellation_justification: string;
  administrator_document: string;
  customer_document: string;
  customer_full_name: string;
  plate: string;
}

@Component({
  selector: 'app-contract-audit',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './contract-audit.component.html',
})
export class ContractAuditComponent implements OnInit {
  private readonly http = inject(HttpClient);
  readonly cancellations = signal<ContractCancellation[]>([]);

  ngOnInit(): void {
    this.http.get<ContractCancellation[]>('/api/contracts/cancellations').subscribe({
      next: (items) => this.cancellations.set(items),
    });
  }
}
