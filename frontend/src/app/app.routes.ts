import { Routes } from '@angular/router';
import { authGuard } from './core/auth.guard';
import { LoginComponent } from './features/auth/login.component';
import { CashOpenComponent } from './features/cash/cash-open.component';
import { ContractsComponent } from './features/contracts/contracts.component';
import { ParkingComponent } from './features/parking/parking.component';
import { PaymentsComponent } from './features/payments/payments.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  {
    path: '',
    canActivate: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'cash' },
      { path: 'cash', component: CashOpenComponent },
      { path: 'contracts', component: ContractsComponent },
      { path: 'parking', component: ParkingComponent },
      { path: 'payments', component: PaymentsComponent },
    ],
  },
  { path: '**', redirectTo: '' },
];
