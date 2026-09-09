import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TokenStorageService } from '../../../../core/services/token-storage.service';
import { User } from '../../../auth/interfaces/user.interface';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class HeaderComponent implements OnInit {
  private readonly tokenStorage = inject(TokenStorageService);

  public currentUser: User | null = null;

  public ngOnInit(): void {
    this.currentUser = this.tokenStorage.getUser();
  }
}
