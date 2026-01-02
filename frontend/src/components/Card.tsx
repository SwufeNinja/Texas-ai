import React from 'react';

interface CardProps {
    rank: string; // 'A', 'K', 'Q', 'J', 'T', '9', ...
    suit: string; // 's', 'h', 'd', 'c' or symbol
    hidden?: boolean;
    className?: string;
}

const suitMap: Record<string, { symbol: string; color: string }> = {
    s: { symbol: '♠', color: '#e0e0e0' }, // Spades - Light Gray/White
    h: { symbol: '♥', color: '#ff4d4d' }, // Hearts - Red
    d: { symbol: '♦', color: '#4d79ff' }, // Diamonds - Blue (Four Color Deck style for visibility)
    c: { symbol: '♣', color: '#00cc66' }, // Clubs - Green
};

export const Card: React.FC<CardProps> = ({ rank, suit, hidden, className = '' }) => {
    if (hidden) {
        return (
            <div className={`poker-card hidden-card ${className}`} style={cardStyle}>
                <div style={patternStyle}></div>
            </div>
        );
    }

    const normalizedSuit = suit.toLowerCase();
    const suitData = suitMap[normalizedSuit] || { symbol: suit, color: '#fff' };

    return (
        <div className={`poker-card ${className}`} style={{ ...cardStyle, color: suitData.color }}>
            <div style={topRankStyle}>{rank}</div>
            <div style={bigSuitStyle}>{suitData.symbol}</div>
            <div style={bottomRankStyle}>{rank}</div>
        </div>
    );
};

// CSS-in-JS for self-contained styles (can be moved to CSS file later)
const cardStyle: React.CSSProperties = {
    width: '60px',
    height: '84px',
    backgroundColor: '#fff', // White background for card face
    borderRadius: '4px',
    border: '1px solid #ccc',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    padding: '4px',
    position: 'relative',
    boxShadow: '0 2px 5px rgba(0,0,0,0.3)',
    userSelect: 'none',
    background: 'linear-gradient(135deg, #2a2a35 0%, #15151f 100%)', // Dark card background for digital look
    borderColor: '#d4af37', // Gold border
};

const topRankStyle: React.CSSProperties = {
    fontSize: '0.9rem',
    fontWeight: 'bold',
    textAlign: 'left',
    lineHeight: 1,
};

const bottomRankStyle: React.CSSProperties = {
    fontSize: '0.9rem',
    fontWeight: 'bold',
    textAlign: 'right',
    lineHeight: 1,
    transform: 'rotate(180deg)',
};

const bigSuitStyle: React.CSSProperties = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    fontSize: '2rem',
};

const patternStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    backgroundImage: 'repeating-linear-gradient(45deg, #d4af37 0, #d4af37 2px, transparent 0, transparent 50%)',
    backgroundSize: '10px 10px',
    opacity: 0.1,
};
