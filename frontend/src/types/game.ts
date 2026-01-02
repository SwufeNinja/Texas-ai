export interface Player {
    name: string;
    chips: number;
    bet: number;
    status: 'ACTIVE' | 'FOLDED' | 'ALL_IN' | 'OUT';
    is_active: boolean;
    hand?: string[];
}

export interface GameState {
    stage: string;
    pot: number;
    current_bet: number;
    board: string[];
    players: Player[];
    current_player_index: number;
    legal_actions: string[];
}
