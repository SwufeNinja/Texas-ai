<script setup lang="ts">
import { computed } from 'vue';
import type { GameState, Player } from '../types';
import CardComponent from './Card.vue';
import PlayerSeat from './PlayerSeat.vue';

const props = defineProps<{
  gameState: GameState | null; // Allow null for robustness
  currentUser?: Player | null; // For identifying 'current' player visually? No, that's current turn.
}>();

const emit = defineEmits<{
  (e: 'removeAi', id: string): void
}>();

const communityDisplay = computed(() => {
  const cards = props.gameState?.community_cards || [];
  if (cards.length > 0) return cards;
  return ["", "", "", "", ""];
});

const seatedPlayers = computed(() => {
  return props.gameState?.players.filter(p => p.seated) || [];
});

const currentPlayerId = computed(() => props.gameState?.current_player_id);

const seatPositions = [
  { top: "8%", left: "50%", transform: "translate(-50%, -50%)" },
  { top: "20%", left: "85%", transform: "translate(-50%, -50%)" },
  { top: "70%", left: "88%", transform: "translate(-50%, -50%)" },
  { top: "92%", left: "50%", transform: "translate(-50%, -50%)" },
  { top: "70%", left: "12%", transform: "translate(-50%, -50%)" },
  { top: "20%", left: "15%", transform: "translate(-50%, -50%)" },
  { top: "8%", left: "20%", transform: "translate(-50%, -50%)" },
  { top: "8%", left: "80%", transform: "translate(-50%, -50%)" },
];

const getSeatStyle = (index: number) => {
  return seatPositions[index % seatPositions.length];
};
</script>

<template>
  <div class="table-area">
    <div class="title">Game State</div>
    <div class="table-meta">
      <div>Stage: <span>{{ gameState?.stage || "-" }}</span></div>
      <div>Pot: <span>{{ gameState?.pot ?? 0 }}</span></div>
      <div>Current: <span>{{ gameState?.current_player_id || "-" }}</span></div>
    </div>
    
    <div class="table">
      <!-- Community Cards -->
      <div class="community">
        <CardComponent 
          v-for="(card, index) in communityDisplay"
          :key="`community-${index}`"
          :card="card"
        />
      </div>

      <!-- Pot info could be placed here too -->

      <!-- Seats -->
      <div class="seats-layer">
        <PlayerSeat 
          v-for="(player, index) in seatedPlayers"
          :key="`seat-${player.id}`"
          :player="player"
          :is-current="player.id === currentPlayerId"
          :style="getSeatStyle(index)"
          @remove="(id) => emit('removeAi', id)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.table-area {
  position: relative;
  display: grid;
  gap: 16px;
}

.title {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.table-meta {
  display: grid;
  grid-template-columns: repeat(3, auto);
  gap: 16px;
  color: var(--muted);
  font-size: 13px;
}

.table-meta span {
  color: var(--ink);
  font-weight: 600;
}

.table {
  position: relative;
  min-height: 480px; /* Bit taller than original 420px */
  border-radius: 36px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    radial-gradient(circle at 30% 20%, rgba(86, 242, 214, 0.12), transparent 60%),
    radial-gradient(circle at 70% 80%, rgba(247, 201, 72, 0.1), transparent 55%),
    linear-gradient(180deg, rgba(9, 16, 28, 0.9) 0%, rgba(11, 20, 36, 0.96) 100%);
  overflow: hidden;
  box-shadow: inset 0 0 60px rgba(0, 0, 0, 0.6);
}

.table::before,
.table::after {
  content: "";
  position: absolute;
  inset: 12%;
  border-radius: 30px;
  border: 1px dashed rgba(255, 255, 255, 0.08);
}

.table::after {
  inset: 24%;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.community {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  gap: 10px;
  z-index: 5;
}

.seats-layer {
  position: absolute;
  inset: 0;
  pointer-events: none; /* Let clicks pass through empty areas */
}
/* But seats themselves need pointer events */
:deep(.seat) {
  pointer-events: auto;
}
</style>
