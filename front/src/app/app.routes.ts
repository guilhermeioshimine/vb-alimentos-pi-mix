import { Routes } from '@angular/router';
import { MixDataComponent } from './mix-data/mix-data';

export const routes: Routes = [
  { path: '', redirectTo: 'mix', pathMatch: 'full' },
  { path: 'mix', component: MixDataComponent },
  { path: '**', redirectTo: 'mix' }
];
