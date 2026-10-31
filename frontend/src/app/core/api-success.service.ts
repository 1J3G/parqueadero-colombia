import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ApiSuccessService {
  readonly message = signal('');

  show(message: string): void {
    this.message.set(message);
  }

  clear(): void {
    this.message.set('');
  }
}
