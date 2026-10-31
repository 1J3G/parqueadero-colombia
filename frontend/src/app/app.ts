import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from './core/auth.service';
import { ApiErrorService } from './core/api-error.service';
import { ApiSuccessService } from './core/api-success.service';

@Component({
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  standalone: true,
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  readonly auth = inject(AuthService);
  readonly errors = inject(ApiErrorService);
  readonly successes = inject(ApiSuccessService);
  private readonly router = inject(Router);

  logout(): void {
    this.auth.logout().subscribe({
      next: () => this.router.navigateByUrl('/login'),
    });
  }
}
