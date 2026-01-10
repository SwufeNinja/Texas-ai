<script setup lang="ts">
import { computed } from 'vue';
import type { Player } from '../types';
import Card from './Card.vue';

const props = defineProps<{
  player: Player;
  isCurrent?: boolean;
  canRemoveAi: boolean;
}>();

const emit = defineEmits<{
  (e: 'remove', id: string): void
}>();

const seatClass = computed(() => ({
  current: props.isCurrent,
  active: props.player.status === 'PLAYING',
  folded: props.player.status === 'FOLDED'
}));

const handDisplay = computed(() => {
  if (!props.player.hand || !props.player.hand.length) {
    return ["", ""];
  }
  return props.player.hand;
});

const readyLabel = computed(() => props.player.ready ? "Ready" : "Not Ready");

</script>

<template>
  <div class="seat" :class="seatClass">
    <div class="name">{{ player.name }}</div>
    <div class="meta">
      ({{ player.id }}) - {{ player.chips }} 
      <span class="bet-marker" v-if="player.bet > 0">Bet: {{ player.bet }}</span>
    </div>
    
    <div class="status-indicator">
      {{ player.seated ? readyLabel : "Spectating" }} - {{ player.status }}
    </div>

    <!-- Hand Cards -->
    <div class="hand-cards">
      <Card 
        v-for="(card, idx) in handDisplay" 
        :key="`${player.id}-card-${idx}`"
        :card="card"
        mini
      />
    </div>

    <!-- AI Control -->
    <button 
      v-if="player.is_ai && canRemoveAi" 
      class="ai-remove-btn"
      @click.stop="$emit('remove', player.id)"
      title="Remove AI"
    >
      ×
    </button>
  </div>
</template>

<style scoped>
.seat {
  position: absolute;
  min-width: 140px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(10, 18, 30, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.35);
  font-size: 12px;
  transition: all 0.3s ease;
  z-index: 10;
}

.seat.current {
  border-color: rgba(247, 201, 72, 0.6);
  box-shadow: 0 0 0 1px rgba(247, 201, 72, 0.3), 0 12px 24px rgba(0, 0, 0, 0.35);
  transform: scale(1.02);
}

.seat.active {
  border-color: rgba(61, 220, 151, 0.45);
}

.seat.folded {
  opacity: 0.7;
  filter: grayscale(0.5);
}

.name {
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--ink);
  font-size: 13px;
}

.meta {
  color: var(--muted);
  font-size: 11px;
  display: flex;
  justify-content: space-between;
}

.bet-marker {
  color: var(--accent-2);
  font-weight: bold;
}

.status-indicator {
  font-size: 10px;
  color: var(--muted);
  margin-top: 2px;
  opacity: 0.8;
}

.hand-cards {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  justify-content: center;
}

.ai-remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--card-red);
  color: white;
  border: none;
  cursor: pointer;
  display: grid;
  place-items: center;
  font-size: 14px;
  line-height: 1;
  opacity: 0;
  transition: opacity 0.2s;
}

.seat:hover .ai-remove-btn {
  opacity: 1;
}
</style>
