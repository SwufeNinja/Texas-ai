export interface Player {
  id: string;
  name: string;
  chips: number;
  bet: number;
  hand: string[];
  seated: boolean;
  ready: boolean;
  is_ai: boolean;
  status: 'PLAYING' | 'FOLDED' | 'ALL_IN' | 'WAITING' | 'ELIMINATED' | 'SITTING_OUT'; 
}

export interface GameState {
  stage: 'PREFLOP' | 'FLOP' | 'TURN' | 'RIVER' | 'SHOWDOWN';
  pot: number;
  current_player_id: string;
  community_cards: string[];
  players: Player[];
  dealer_index?: number;
  small_blind: number;
  big_blind: number;
  current_bet: number;
  last_raise_size: number;
  awaiting_ready: boolean;
}

export interface ServerMessage {
  type: 'game_update' | 'join_ok' | 'error' | 'system';
  data: any;
}
