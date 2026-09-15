import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-custom-button',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './custom-button.component.html',
  styleUrls: ['./custom-button.component.css'],
  host: {
    '[class.full-width]': 'fullWidth'
  }
})
export class CustomButtonComponent {
  @Input() public text = '';
  @Input() public variant: 'primary' | 'secondary' | 'danger' = 'primary';
  @Input() public type: 'button' | 'submit' = 'button';
  @Input() public disabled = false;
  @Input() public loading = false;
  @Input() public loadingText = '';
  @Input() public fullWidth = false;

  @Output() public readonly btnClick = new EventEmitter<MouseEvent>();

  public onClick(event: MouseEvent): void {
    if (this.disabled || this.loading) {
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    this.btnClick.emit(event);
  }
}
