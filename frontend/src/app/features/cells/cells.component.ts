import { HttpClient } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { AuthService } from '../../core/auth.service';

interface ParkingCell {
  id: number;
  label: string;
  category: string;
  status: 'Libre' | 'Ocupado' | 'En mantenimiento';
  plate: string | null;
}

@Component({
  selector: 'app-cells',
  standalone: true,
  templateUrl: './cells.component.html',
})
export class CellsComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  readonly cells = signal<ParkingCell[]>([]);
  readonly isAdministrator = computed(() => this.auth.currentUser()?.role === 'Administrador');
  readonly submitting = signal(false);

  ngOnInit(): void {
    this.refresh();
  }

  toggleMaintenance(cell: ParkingCell): void {
    const status = cell.status === 'Libre' ? 'En mantenimiento' : 'Libre';
    this.submitting.set(true);
    this.http.patch(`/api/cells/${cell.id}/status`, { status }).subscribe({
      next: () => this.refresh(),
      error: () => this.submitting.set(false),
      complete: () => this.submitting.set(false),
    });
  }

  private refresh(): void {
    this.http.get<ParkingCell[]>('/api/cells').subscribe({
      next: (cells) => this.cells.set(cells),
    });
  }
}
