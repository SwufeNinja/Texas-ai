import React from 'react';
import type { GameState } from '../types/game';
import { Card } from './Card';
import { PlayerSeat } from './PlayerSeat';

interface TableProps {
    gameState: GameState;
}

export const Table: React.FC<TableProps> = ({ gameState }) => {
    return (
        <div style={tableContainerStyle}>
            <div style={tableFeltStyle}>
                {/* Community Cards */}
                <div style={communityCardsContainer}>
                     {gameState.board.length === 0 && (
                         <div style={{color: 'rgba(255,255,255,0.2)', fontStyle: 'italic'}}>Waiting for flop...</div>
                     )}
                     {gameState.board.map((cardStr, idx) => {
                         // Parse card string "Ah", "Td"
                         const rank = cardStr[0];
                         const suit = cardStr[1];
                         return <Card key={idx} rank={rank} suit={suit} />;
                     })}
                </div>

                {/* Pot Display */}
                <div style={potMetricsStyle}>
                    <div style={{fontSize: '0.8rem', color: '#ccc'}}>POT</div>
                    <div style={{fontSize: '1.5rem', color: '#ffd700', fontWeight: 'bold'}}>${gameState.pot}</div>
                </div>
            </div>

            {/* Players - Absolute positioned relative to container, NOT felt (so they sit on edge) */}
            {gameState.players.map((p) => (
                <PlayerSeat 
                    key={p.name} 
                    player={p} 
                    position={p.name === 'Human' ? 'bottom' : 'top'} 
                    isTurn={false} // Todo: Add current turn logic to GameState API
                />
            ))}
        </div>
    );
};

const tableContainerStyle: React.CSSProperties = {
    position: 'relative',
    width: '800px',
    height: '500px',
    margin: 'auto',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
};

const tableFeltStyle: React.CSSProperties = {
    width: '700px',
    height: '350px',
    backgroundColor: '#0d4a2e',
    background: 'radial-gradient(ellipse at center, #0d4a2e 0%, #073d1f 100%)',
    borderRadius: '175px',
    border: '8px solid #3d2b1f', // Wood rail
    boxShadow: '0 0 50px rgba(0,0,0,0.5), inset 0 0 100px rgba(0,0,0,0.5)',
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
};

const communityCardsContainer: React.CSSProperties = {
    display: 'flex',
    gap: '10px',
    marginTop: '-20px',
};

const potMetricsStyle: React.CSSProperties = {
    marginTop: '20px',
    textAlign: 'center',
    background: 'rgba(0,0,0,0.3)',
    padding: '5px 20px',
    borderRadius: '20px',
    border: '1px solid rgba(255,215,0,0.3)',
};
