export type TokenOut = { access_token: string; refresh_token: string; token_type: string };
export type WalletRow = { id: number; ticker: string; quantity: number; created_at: string };
export type UserOut = { id: number; email: string };

export type Indice = {
  ticker: string;
  full_name: string;
  price: number;
  performance: number;
};
