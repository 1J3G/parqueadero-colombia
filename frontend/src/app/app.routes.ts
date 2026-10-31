import { Routes } from '@angular/router';
import { administratorGuard, authGuard } from './core/auth.guard';
import { LoginComponent } from './features/auth/login.component';
import { CashOpenComponent } from './features/cash/cash-open.component';
import { ContractsComponent } from './features/contracts/contracts.component';
import { ParkingComponent } from './features/parking/parking.component';
import { PaymentsComponent } from './features/payments/payments.component';
import { CellsComponent } from './features/cells/cells.component';
import { ContractAuditComponent } from './features/contracts/contract-audit.component';
import { UsersComponent } from './features/users/users.component';

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
      { path: 'cells', component: CellsComponent },
      { path: 'payments', component: PaymentsComponent },
      { path: 'users', component: UsersComponent, canActivate: [administratorGuard] },
      { path: 'contract-audit', component: ContractAuditComponent, canActivate: [administratorGuard] },
    ],
  },
  { path: '**', redirectTo: '' },
];
