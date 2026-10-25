import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly document = signal('');
  readonly password = signal('');
  readonly submitting = signal(false);

  login(): void {
    this.submitting.set(true);
    this.auth.login(this.document().trim(), this.password()).subscribe({
      next: () => this.router.navigateByUrl('/cash'),
      error: () => this.submitting.set(false),
      complete: () => this.submitting.set(false),
    });
  }
}
