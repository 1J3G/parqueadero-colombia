import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

interface ManagedUser {
  id: number;
  document: string;
  role: 'Operario' | 'Administrador';
  created_at: string;
}

@Component({
  selector: 'app-users',
  standalone: true,
  imports: [FormsModule, DatePipe],
  templateUrl: './users.component.html',
})
export class UsersComponent implements OnInit {
  private readonly http = inject(HttpClient);
  readonly users = signal<ManagedUser[]>([]);
  readonly document = signal('');
  readonly password = signal('');
  readonly role = signal<'Operario' | 'Administrador'>('Operario');
  readonly submitting = signal(false);

  ngOnInit(): void {
    this.refresh();
  }

  createUser(): void {
    this.submitting.set(true);
    this.http.post('/api/users', {
      document: this.document().trim(),
      password: this.password(),
      role: this.role(),
    }).subscribe({
      next: () => {
        this.document.set('');
        this.password.set('');
        this.role.set('Operario');
        this.refresh();
      },
      error: () => this.submitting.set(false),
      complete: () => this.submitting.set(false),
    });
  }

  private refresh(): void {
    this.http.get<ManagedUser[]>('/api/users').subscribe({
      next: (users) => this.users.set(users),
    });
  }
}
