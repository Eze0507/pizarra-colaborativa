import { User } from './user.interface';

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}
