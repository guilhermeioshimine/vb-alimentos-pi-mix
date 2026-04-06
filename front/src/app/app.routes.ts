import { Routes } from '@angular/router';
import { MixDataComponent } from './mix-data/mix-data';
import { PreMixDataComponent } from './pre-mix-data/pre-mix-data';

export const routes: Routes = [
  { path: '', redirectTo: 'mix', pathMatch: 'full' },
  { path: 'mix', component: MixDataComponent },
  { path: 'pre-mix', component: PreMixDataComponent },
  { path: '**', redirectTo: 'mix' }
];
