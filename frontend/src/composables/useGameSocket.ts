import { ref, computed } from 'vue';
import type { GameState, ServerMessage } from '../types';

export function useGameSocket() {
  const socket = ref<WebSocket | null>(null);
  const connected = ref(false);
  const lastState = ref<GameState | null>(null);
  const logItems = ref<string[]>([]);

  // Protocol/Host calculation
  const wsUrl = computed(() => {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    return `${protocol}://${location.host}/ws`;
  });

  const log = (message: string) => {
    logItems.value.unshift(message);
  };

  const formatSystemMessage = (data: any) => {
    const event = data.event || "system";
    const playerId = data.player_id ? ` ${data.player_id}` : "";
    if (event === "player_joined") {
      const status = data.waiting ? "waiting" : "seated";
      return `System: ${event}${playerId} (${status})`;
    }
    return `System: ${event}${playerId}`;
  };

  const connect = (playerId: string, playerName: string) => {
    if (!playerId.trim()) return;
    
    if (socket.value) {
      socket.value.close();
    }

    const ws = new WebSocket(wsUrl.value);
    socket.value = ws;

    ws.addEventListener("open", () => {
      ws.send(JSON.stringify({
        type: "join",
        data: { player_id: playerId.trim(), name: playerName.trim() }
      }));
    });

    ws.addEventListener("message", (event) => {
      try {
        const payload: ServerMessage = JSON.parse(event.data);
        if (payload.type === "game_update") {
          lastState.value = payload.data;
          connected.value = true;
        } else if (payload.type === "join_ok") {
          connected.value = true;
        } else if (payload.type === "error") {
          log(`Error: ${payload.data.message}`);
        } else if (payload.type === "system") {
          log(formatSystemMessage(payload.data || {}));
        }
      } catch (e) {
        console.error("Failed to parse message", e);
      }
    });

    ws.addEventListener("close", () => {
      connected.value = false;
      socket.value = null;
    });
  };

  const disconnect = () => {
    if (socket.value) {
      socket.value.close();
      socket.value = null;
      connected.value = false;
    }
  };

  const sendAction = (action: string, amount: number = 0) => {
    if (!socket.value || socket.value.readyState !== WebSocket.OPEN) return;
    socket.value.send(JSON.stringify({
      type: "action",
      data: { action, amount }
    }));
  };

  const toggleReady = (currentReadyState: boolean) => {
    if (!socket.value || socket.value.readyState !== WebSocket.OPEN) return;
    socket.value.send(JSON.stringify({
      type: "ready",
      data: { ready: !currentReadyState }
    }));
  };

  const addAi = async (id: string, name: string) => {
    try {
      const res = await fetch("/ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player_id: id, name }),
      });
      const payload = await res.json();
      log(payload.ok ? `AI ${id} added` : `AI add failed: ${payload.message}`);
    } catch (e) {
      log(`Error adding AI: ${e}`);
    }
  };

  const removeAi = async (id: string) => {
    try {
      const res = await fetch("/ai/remove", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player_id: id }),
      });
      const payload = await res.json();
      log(payload.ok ? `AI ${id} removed` : `AI remove failed: ${payload.message}`);
    } catch (e) {
      log(`Error removing AI: ${e}`);
    }
  };

  return {
    socket,
    connected,
    lastState,
    logItems,
    connect,
    disconnect,
    sendAction,
    toggleReady,
    addAi,
    removeAi
  };
}
