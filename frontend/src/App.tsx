import { useEffect, useState } from 'react';
import { Table } from './components/Table';
import { Controls } from './components/Controls';
import type { GameState } from './types/game';
// So no import './App.css'

function App() {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [loading, setLoading] = useState(false);

  const API_URL = 'http://127.0.0.1:8000';

  const fetchState = async () => {
      try {
          const res = await fetch(`${API_URL}/game/state`);
          if (res.ok) {
              const data = await res.json();
              setGameState(data);
          }
      } catch (e) {
          console.error("Failed to fetch state", e);
      }
  };

  const createGame = async () => {
      setLoading(true);
      try {
          await fetch(`${API_URL}/game/create`, { method: 'POST' });
          await fetchState();
      } catch (e) {
          console.error("Failed to create game", e);
      }
      setLoading(false);
  };

  const handleAction = async (action: string, amount?: number) => {
      try {
          await fetch(`${API_URL}/game/action`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ action, amount })
          });
          await fetchState(); // Refresh immediately
      } catch (e) {
          console.error("Action failed", e);
      }
  };

  useEffect(() => {
      fetchState();
      // Simple polling for now
      const interval = setInterval(fetchState, 1000);
      return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ width: '100%', height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      
      {!gameState ? (
          <div style={{textAlign: 'center'}}>
              <h1 style={{color: '#d4af37', marginBottom: '20px'}}>Texas Hold'em AI</h1>
              <button 
                onClick={createGame} 
                disabled={loading}
                style={{ fontSize: '1.2rem', padding: '15px 30px' }}
              >
                {loading ? 'Dealing...' : 'Start New Game'}
              </button>
          </div>
      ) : (
          <>
            <Table gameState={gameState} />
            {/* Show controls only if game is running (not GAME_OVER) */}
            {gameState.stage !== 'GAME_OVER' && (
                <Controls gameState={gameState} onAction={handleAction} />
            )}
            
            {/* Overlay for Game Over */}
            {gameState.stage === 'GAME_OVER' && (
                 <div style={{
                     position: 'absolute', 
                     top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                     zIndex: 200, textAlign: 'center',
                     background: 'rgba(0,0,0,0.9)', padding: '40px', borderRadius: '20px',
                     border: '2px solid #d4af37'
                 }}>
                     <h2 style={{color: '#d4af37'}}>Hand Finished</h2>
                     <button onClick={createGame} style={{marginTop: '20px'}}>Next Hand</button>
                 </div>
            )}
          </>
      )}
      
      {/* Dev Controls */}
      {gameState && (
           <div style={{position: 'absolute', bottom: '20px', right: '20px', display: 'flex', gap: '10px'}}>
               <button onClick={createGame} style={{fontSize: '0.8rem', opacity: 0.5}}>Reset Game</button>
           </div>
      )}

    </div>
  );
}

export default App;
