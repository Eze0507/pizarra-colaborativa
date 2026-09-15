import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-search-bar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './search-bar.component.html',
  styleUrls: ['./search-bar.component.css']
})
export class SearchBarComponent implements OnInit {
  @Input() public placeholder = 'Buscar proyectos...';
  @Input() public initialValue = '';

  @Output() public readonly searchChange = new EventEmitter<string>();
  @Output() public readonly searchClear = new EventEmitter<void>();

  public searchTerm = '';

  public ngOnInit(): void {
    if (this.initialValue) {
      this.searchTerm = this.initialValue;
    }
  }

  public onInputChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.searchTerm = input.value;
    this.searchChange.emit(this.searchTerm.trim());
  }

  public clearSearch(): void {
    this.searchTerm = '';
    this.searchChange.emit('');
    this.searchClear.emit();
  }
}
