import React from 'react';
import type { Player } from '../types/game';
import { User, Cpu } from 'lucide-react';

interface PlayerSeatProps {
    player: Player;
    position: 'bottom' | 'top' | 'left' | 'right';
    cards?: string[]; // Optional for now, might need to parse hand strings
    isTurn?: boolean;
}

export const PlayerSeat: React.FC<PlayerSeatProps> = ({ player, position, isTurn }) => {
    // Parse hand if available, otherwise show backs or nothing
    // Assuming backend sends cards like "Ah" "Td" etc in the future.
    // For now we might just simulate or expect them in player object if they were visible.
    
    // Position styling
    const seatStyle: React.CSSProperties = {
        position: 'absolute',
        transition: 'all 0.3s ease',
        ...getPositionStyle(position),
    };

    const isFolded = player.status === 'FOLDED';
    return (
        <div style={seatStyle} className={`player-seat ${isTurn ? 'active-turn' : ''} ${isFolded ? 'folded' : ''}`}>
            {/* Avatar Circle */}
            <div style={avatarStyle}>
                {player.name === 'Human' ? <User size={24} color="#d4af37" /> : <Cpu size={24} color="#ccc" />}
            </div>

            {/* Info Box */}
            <div style={infoBoxStyle}>
                <div style={{ color: '#d4af37', fontWeight: 'bold', fontSize: '0.9rem' }}>{player.name}</div>
                <div style={{ color: '#4ade80', fontSize: '0.8rem' }}>${player.chips}</div>
                {player.bet > 0 && (
                    <div style={betBadgeStyle}>Bet: ${player.bet}</div>
                )}
                <div style={statusStyle}>{player.status}</div>
            </div>
        </div>
    );
};

// Styles
const getPositionStyle = (pos: string): React.CSSProperties => {
    switch (pos) {
        case 'bottom': return { bottom: '5%', left: '50%', transform: 'translateX(-50%)' };
        case 'top': return { top: '5%', left: '50%', transform: 'translateX(-50%)' };
        case 'left': return { left: '5%', top: '50%', transform: 'translateY(-50%)' };
        case 'right': return { right: '5%', top: '50%', transform: 'translateY(-50%)' };
        default: return {};
    }
};

const avatarStyle: React.CSSProperties = {
    width: '50px',
    height: '50px',
    borderRadius: '50%',
    backgroundColor: '#1a1a2e',
    border: '2px solid #d4af37',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto -25px auto', // Overlap info box
    position: 'relative',
    zIndex: 2,
    boxShadow: '0 0 10px rgba(0,0,0,0.5)',
};

const infoBoxStyle: React.CSSProperties = {
    backgroundColor: 'rgba(20, 20, 30, 0.9)',
    border: '1px solid #444',
    borderRadius: '10px',
    padding: '25px 15px 10px 15px',
    minWidth: '120px',
    textAlign: 'center',
    boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
    position: 'relative',
    zIndex: 1,
};

const betBadgeStyle: React.CSSProperties = {
    backgroundColor: '#d4af37',
    color: '#000',
    borderRadius: '10px',
    padding: '2px 8px',
    fontSize: '0.75rem',
    fontWeight: 'bold',
    position: 'absolute',
    top: '-10px',
    right: '-10px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
};

const statusStyle: React.CSSProperties = {
    fontSize: '0.65rem',
    color: '#666',
    marginTop: '4px',
};
