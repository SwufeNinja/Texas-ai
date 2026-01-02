import React from 'react';
import type { GameState } from '../types/game';

interface ControlsProps {
    gameState: GameState;
    onAction: (action: string, amount?: number) => void;
}

export const Controls: React.FC<ControlsProps> = ({ gameState, onAction }) => {
    // Determine if it's our turn
    // We assume we are "Human" for now and we are at index `current_player_index`
    // Ideally we match by name or ID.
    const currentPlayer = gameState.players[gameState.current_player_index];
    const isMyTurn = currentPlayer.name === 'Human'; // Hardcoded for single player demo
    
    if (!isMyTurn) {
        return (
            <div style={controlsContainerStyle}>
                <div style={{color: '#999', fontStyle: 'italic'}}>Waiting for opponents...</div>
            </div>
        );
    }

    const { legal_actions } = gameState;

    return (
        <div style={controlsContainerStyle}>
            {legal_actions.includes('fold') && (
                <button 
                  onClick={() => onAction('fold')} 
                  style={{...btnStyle, backgroundColor: '#ef4444', color: '#fff'}}
                >
                    Fold
                </button>
            )}
            
            {legal_actions.includes('check') && (
                <button 
                  onClick={() => onAction('check')} 
                  style={{...btnStyle, backgroundColor: '#3b82f6', color: '#fff'}}
                >
                    Check
                </button>
            )}

            {legal_actions.includes('call') && (
                <button 
                  onClick={() => onAction('call')} 
                  style={{...btnStyle, backgroundColor: '#3b82f6', color: '#fff'}}
                >
                    Call
                </button>
            )}

            {legal_actions.includes('raise') && (
                <button 
                  onClick={() => onAction('raise')} 
                  style={{...btnStyle, backgroundColor: '#eab308', color: '#000'}}
                >
                    Raise
                </button>
            )}

            {legal_actions.includes('all_in') && (
                <button 
                  onClick={() => onAction('all_in')} 
                  style={{...btnStyle, backgroundColor: '#a855f7', color: '#fff'}}
                >
                    All In
                </button>
            )}
        </div>
    );
};

const controlsContainerStyle: React.CSSProperties = {
    position: 'absolute',
    bottom: '20px',
    left: '50%',
    transform: 'translateX(-50%)',
    display: 'flex',
    gap: '15px',
    padding: '15px',
    backgroundColor: 'rgba(0,0,0,0.8)',
    borderRadius: '15px',
    border: '1px solid #444',
    boxShadow: '0 5px 15px rgba(0,0,0,0.5)',
    zIndex: 100,
};

const btnStyle: React.CSSProperties = {
    minWidth: '80px',
    fontWeight: 'bold',
    textTransform: 'uppercase',
    border: 'none',
};
