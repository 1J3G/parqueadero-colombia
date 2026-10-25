import { CurrencyPipe, DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';

interface PaymentContract {
  id: number;
  plate: string;
  status: string;
  expires_on: string | null;
  customer_full_name: string;
}

interface PaymentResult {
  payment_id: number;
  contract_id: number;
  receipt_number: number;
  customer_document_type: string;
  customer_document: string;
  customer_full_name: string;
  net_amount: string;
  tax_amount: string;
  total_amount: string;
  expires_on: string;
}

@Component({
  selector: 'app-payments',
  standalone: true,
  imports: [FormsModule, CurrencyPipe, DatePipe, RouterLink],
  templateUrl: './payments.component.html',
})
export class PaymentsComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  readonly isAdministrator = computed(() => this.auth.currentUser()?.role === 'Administrador');
  readonly isOperator = computed(() => this.auth.currentUser()?.role === 'Operario');
  readonly contracts = signal<PaymentContract[]>([]);
  readonly cashOpen = signal(false);
  readonly contractId = signal<number | null>(null);
  readonly paidMonths = signal(1);
  readonly netAmount = signal<number | null>(null);
  readonly paymentMethod = signal('Efectivo');
  readonly referenceCode = signal('');
  readonly result = signal<PaymentResult | null>(null);
  readonly voidPaymentId = signal<number | null>(null);
  readonly administratorPassword = signal('');
  readonly justification = signal('');
  readonly submitting = signal(false);

  setContractId(value: string | number | null): void {
    this.contractId.set(value === null || value === '' ? null : Number(value));
  }

  setVoidPaymentId(value: string | number | null): void {
    this.voidPaymentId.set(value === null || value === '' ? null : Number(value));
  }

  setNetAmount(value: number | string | null): void {
    this.netAmount.set(value === null || value === '' ? null : Number(value));
  }

  ngOnInit(): void {
    this.http.get<PaymentContract[]>('/api/contracts').subscribe({
      next: (contracts) => this.contracts.set(contracts),
    });
    this.http.get<{ id: number } | null>('/api/cash/current').subscribe({
      next: (cash) => this.cashOpen.set(cash !== null),
    });
  }

  createPayment(): void {
    const contractId = this.contractId();
    const netAmount = this.netAmount();
    if (!contractId || netAmount === null || netAmount <= 0) {
      return;
    }
    this.submitting.set(true);
    this.http
      .post<PaymentResult>('/api/payments', {
        contract_id: contractId,
        paid_months: this.paidMonths(),
        net_amount: netAmount,
        payment_method: this.paymentMethod(),
        reference_code: this.paymentMethod() === 'Transferencia Bancaria' ? this.referenceCode().trim() : null,
      })
      .subscribe({
        next: (result) => this.result.set(result),
        error: () => this.submitting.set(false),
        complete: () => this.submitting.set(false),
      });
  }

  voidPayment(): void {
    const paymentId = this.voidPaymentId();
    if (!paymentId) {
      return;
    }
    this.submitting.set(true);
    this.http
      .post(`/api/payments/${paymentId}/void`, {
        administrator_password: this.administratorPassword(),
        justification: this.justification().trim(),
      })
      .subscribe({
        next: () => {
          this.voidPaymentId.set(null);
          this.administratorPassword.set('');
          this.justification.set('');
        },
        error: () => this.submitting.set(false),
        complete: () => this.submitting.set(false),
      });
  }
}
