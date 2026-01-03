import { computed, type Ref } from 'vue';
import type { GameState, Player } from '../types';

export function useGameState(lastState: Ref<GameState | null>, playerId: Ref<string>) {
  
  const me = computed<Player | null>(() => {
    if (!lastState.value) return null;
    return lastState.value.players.find(p => p.id === playerId.value) || null;
  });

  const isMyTurn = computed(() => {
    return lastState.value?.current_player_id === playerId.value;
  });

  const toCall = computed(() => {
    if (!me.value || !lastState.value) return 0;
    return Math.max(0, (lastState.value.current_bet || 0) - me.value.bet);
  });

  const minRaise = computed(() => {
    const bigBlind = Number(lastState.value?.big_blind || 0);
    const lastRaise = Number(lastState.value?.last_raise_size || 0);
    return Math.max(bigBlind, lastRaise);
  });

  const maxRaise = computed(() => {
    if (!me.value) return 0;
    return Math.max(0, me.value.chips - toCall.value);
  });

  const canAct = computed(() => {
    return Boolean(me.value && me.value.status === "PLAYING" && me.value.ready);
  });

  const handInProgress = computed(() => {
    if (!lastState.value) return false;
    if (lastState.value.awaiting_ready) return false;
    if (lastState.value.stage && lastState.value.stage !== "PREFLOP") return true;
    if ((lastState.value.pot || 0) > 0) return true;
    return Array.isArray(lastState.value.community_cards) && lastState.value.community_cards.length > 0;
  });

  const seatedPlayers = computed(() => {
    return lastState.value?.players.filter(p => p.seated) || [];
  });

  const waitingPlayers = computed(() => {
    return lastState.value?.players.filter(p => !p.seated) || [];
  });

  const communityDisplay = computed(() => {
    const cards = lastState.value?.community_cards || [];
    if (cards.length) return cards;
    return ["", "", "", "", ""];
  });

  const actionHint = computed(() => {
    if (!me.value) return "Not seated.";
    let turnLabel = "Waiting for ready";
    if (!me.value.seated) turnLabel = "Spectating";
    if (canAct.value) {
      turnLabel = isMyTurn.value ? "Your turn" : "Waiting for others";
    }
    return `${turnLabel} | To call: ${toCall.value} | Min raise: ${minRaise.value}`;
  });

  return {
    me,
    isMyTurn,
    toCall,
    minRaise,
    maxRaise,
    canAct,
    handInProgress,
    seatedPlayers,
    waitingPlayers,
    communityDisplay,
    actionHint
  };
}
