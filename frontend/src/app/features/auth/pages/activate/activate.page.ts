import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { ActivateCardComponent } from '../../components/activate-card/activate-card.component';

@Component({
  selector: 'app-activate-page',
  standalone: true,
  imports: [CommonModule, ActivateCardComponent],
  templateUrl: './activate.page.html',
  styleUrls: ['./activate.page.css']
})
export class ActivatePage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  public token: string | null = null;

  public ngOnInit(): void {
    this.token = this.route.snapshot.paramMap.get('token');
  }
}
