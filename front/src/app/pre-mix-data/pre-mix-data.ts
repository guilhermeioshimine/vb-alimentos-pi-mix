import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { finalize } from 'rxjs/operators';
import { FormsModule } from '@angular/forms';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatNativeDateModule } from '@angular/material/core';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';

import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

interface PreMixData {
  id?: number;
  lote?: number;
  sequencia?: number;
  produto?: string;
  peso?: number;
  timestamp?: string;
}

@Component({
  selector: 'app-pre-mix-data',
  standalone: true,
  imports: [
    CommonModule, HttpClientModule, FormsModule,
    MatDatepickerModule, MatFormFieldModule, MatInputModule,
    MatNativeDateModule, MatButtonModule, MatMenuModule
  ],
  templateUrl: './pre-mix-data.html',
  styleUrls: ['./pre-mix-data.scss']
})
export class PreMixDataComponent implements OnInit {
  data: PreMixData[] = [];
  allData: PreMixData[] = [];
  loading = false;
  errorMsg: string | null = null;

  // paginação
  page = 0;
  pageSize = 10;

  // filtro
  startDate: Date | null = null;
  startTime = '00:00';
  endDate: Date | null = null;
  endTime = '23:59';

  constructor(private http: HttpClient, private cd: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.load();
  }

  load() {
    this.loading = true;
    this.errorMsg = null;
    this.http.get<PreMixData[]>('/api/pre-mix/data')
      .pipe(finalize(() => { this.loading = false; this.cd.detectChanges(); }))
      .subscribe({
        next: (res) => {
          this.allData = (res || []).slice().reverse();
          this.applyFilter();
          this.page = 0;
        },
        error: (err) => {
          this.errorMsg = err?.message ?? String(err);
          this.data = [];
        }
      });
  }

  applyFilter() {
    let filtered = this.allData;
    if (this.startDate) {
      const [sh, sm] = this.startTime.split(':').map(Number);
      const start = new Date(this.startDate);
      start.setHours(sh, sm, 0, 0);
      filtered = filtered.filter(d => d.timestamp && new Date(d.timestamp) >= start);
    }
    if (this.endDate) {
      const [eh, em] = this.endTime.split(':').map(Number);
      const end = new Date(this.endDate);
      end.setHours(eh, em, 59, 999);
      filtered = filtered.filter(d => d.timestamp && new Date(d.timestamp) <= end);
    }
    this.data = filtered;
    this.page = 0;
  }

  clearFilter() {
    this.startDate = null;
    this.startTime = '00:00';
    this.endDate = null;
    this.endTime = '23:59';
    this.data = this.allData;
    this.page = 0;
  }

  get totalPages() { return Math.max(1, Math.ceil(this.data.length / this.pageSize)); }
  get paginatedData() {
    return this.data.slice(this.page * this.pageSize, (this.page + 1) * this.pageSize);
  }
  prevPage() { if (this.page > 0) this.page--; }
  nextPage() { if (this.page < this.totalPages - 1) this.page++; }

  private getExportData() {
    return this.data.map(d => ({
      'Data': d.timestamp ? new Date(d.timestamp).toLocaleString('pt-BR') : '',
      'Lote': d.lote ?? '',
      'Sequência': d.sequencia ?? '',
      'Produto': d.produto ?? '',
      'Peso (kg)': d.peso ?? '',
    }));
  }

  exportCSV() {
    const arr = this.getExportData();
    if (!arr.length) return;
    const headers = Object.keys(arr[0]);
    const lines = [headers.join(',')].concat(arr.map(r =>
      headers.map(h => '"' + String((r as any)[h] ?? '').replace(/"/g, '""') + '"').join(',')
    ));
    this.saveBlob(new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' }), `pre_mix_report_${Date.now()}.csv`);
  }

  exportXLSX() {
    const arr = this.getExportData();
    if (!arr.length) return;
    const ws = XLSX.utils.json_to_sheet(arr);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Relatório');
    const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    this.saveBlob(new Blob([wbout], { type: 'application/octet-stream' }), `pre_mix_report_${Date.now()}.xlsx`);
  }

  exportPDF() {
    const arr = this.getExportData();
    if (!arr.length) return;
    const headers = Object.keys(arr[0]);
    const rows = arr.map(r => headers.map(h => (r as any)[h]));
    const doc = new jsPDF('l', 'pt', 'a4');
    (doc as any).autoTable({ head: [headers], body: rows, startY: 20 });
    doc.save(`pre_mix_report_${Date.now()}.pdf`);
  }

  private saveBlob(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }
}
