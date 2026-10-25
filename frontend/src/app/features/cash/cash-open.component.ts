import { HttpClient } from '@angular/common/http';
import { CurrencyPipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { computed } from '@angular/core';
import { AuthService } from '../../core/auth.service';

interface CashOpening {
  id: number;
  base_amount: string;
  opened_at: string;
}

interface ActiveCash extends CashOpening {
  user_id: number;
  user_document: string;
}

@Component({
  selector: 'app-cash-open',
  standalone: true,
  imports: [FormsModule, CurrencyPipe],
  templateUrl: './cash-open.component.html',
})
export class CashOpenComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  readonly isAdministrator = computed(() => this.auth.currentUser()?.role === 'Administrador');
  readonly cash = signal<CashOpening | null>(null);
  readonly activeCash = signal<ActiveCash[]>([]);
  readonly baseAmount = signal<number | null>(null);
  readonly submitting = signal(false);

  ngOnInit(): void {
    this.refresh();
  }

  openCash(): void {
    const amount = this.baseAmount();
    if (amount === null || amount < 0) {
      return;
    }
    this.submitting.set(true);
    this.http.post<CashOpening>('/api/cash/open', { base_amount: amount }).subscribe({
      next: () => this.refresh(),
      error: () => this.submitting.set(false),
      complete: () => this.submitting.set(false),
    });
  }

  closeCash(cashId: number): void {
    this.submitting.set(true);
    this.http.post(`/api/cash/${cashId}/close`, {}).subscribe({
      next: () => this.refresh(),
      error: () => this.submitting.set(false),
      complete: () => this.submitting.set(false),
    });
  }

  private refresh(): void {
    this.http.get<CashOpening | null>('/api/cash/current').subscribe({
      next: (cash) => this.cash.set(cash),
    });
    if (this.isAdministrator()) {
      this.http.get<ActiveCash[]>('/api/cash/open').subscribe({
        next: (cash) => this.activeCash.set(cash),
      });
    }
  }
}
