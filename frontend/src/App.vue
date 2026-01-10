<script setup lang="ts">
import { ref, computed } from 'vue';
import { useGameSocket } from './composables/useGameSocket';
import { useGameState } from './composables/useGameState';
import GameTable from './components/GameTable.vue';
import ActionControls from './components/ActionControls.vue';
import TableControl from './components/TableControl.vue';

// State for inputs
const playerId = ref('p1');
const playerName = ref('Alice');
const aiId = ref('ai_1');
const aiName = ref('DealerBot');

// Composables
const { 
  socket, connected, lastState, logItems, 
  connect, disconnect, sendAction, toggleReady, addAi, removeAi 
} = useGameSocket();

const { 
  me, isMyTurn, toCall, minRaise, maxRaise, canAct, 
  handInProgress, seatedPlayers, waitingPlayers, actionHint 
} = useGameState(lastState, playerId);

const canAllIn = computed(() => Boolean(me.value && me.value.chips > 0 && canAct.value));
const canRemoveAi = computed(() => !handInProgress.value);

const connectionLabel = computed(() => connected.value ? "Connected" : "Disconnected");
const connectBtnText = computed(() => connected.value ? "Disconnect" : "Connect");

const readyActive = computed(() => !!me.value?.ready);
const readyDisabled = computed(() => {
  if (!me.value?.seated) return true;
  return handInProgress.value && me.value.ready;
});
const readyBtnText = computed(() => me.value?.ready ? "Unready" : "Ready");

const handleConnectToggle = () => {
  if (connected.value) {
    if (confirm("Disconnect?")) disconnect();
  } else {
    connect(playerId.value, playerName.value);
  }
};

const handleAction = (action: string, amount?: number) => {
  sendAction(action, amount || 0);
};

const handleAddAi = () => {
  if (aiId.value) addAi(aiId.value, aiName.value);
};

</script>

<template>
  <div class="app-container">
    <TableControl
      v-model:player-id="playerId"
      v-model:player-name="playerName"
      v-model:ai-id="aiId"
      v-model:ai-name="aiName"
      :connected="connected"
      :connection-label="connectionLabel"
      :connect-btn-text="connectBtnText"
      :ready-active="readyActive"
      :ready-disabled="readyDisabled"
      :ready-btn-text="readyBtnText"
      :waiting-players="waitingPlayers"
      :can-remove-ai="canRemoveAi"
      @connect-toggle="handleConnectToggle"
      @toggle-ready="toggleReady"
      @add-ai="handleAddAi"
      @remove-ai="removeAi"
    />

    <!-- Center: Table -->
    <main class="game-area">
      <GameTable 
        :game-state="lastState" 
        :current-user="me"
        :can-remove-ai="canRemoveAi"
        @remove-ai="removeAi"
      />
      
      <ActionControls 
        class="controls-overlay"
        :can-act="canAct"
        :can-all-in="canAllIn"
        :to-call="toCall"
        :min-raise="minRaise"
        :max-raise="maxRaise"
        :hint="actionHint"
        @action="handleAction"
      />
    </main>

    <!-- Right Panel: Players & Log -->
    <aside class="panel info-panel">
      <div class="section-title">Players</div>
      <div class="list-container players-list">
        <div v-for="p in seatedPlayers" :key="p.id" class="list-item" :class="{ active: p.status === 'PLAYING' }">
          <div class="row-main">
            <strong>{{ p.name }}</strong> <small>({{ p.id }})</small>
          </div>
          <div class="row-sub">
            Chips: {{ p.chips }} | {{ p.ready ? 'R' : 'NR' }}
          </div>
          <button
            v-if="p.is_ai && canRemoveAi"
            class="ai-remove"
            @click="removeAi(p.id)"
          >
            Remove AI
          </button>
        </div>
      </div>

      <div class="section-title mt-4">Log</div>
      <div class="list-container log-list">
        <div v-for="(msg, i) in logItems" :key="i" class="log-entry">{{ msg }}</div>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.app-container {
  display: grid;
  grid-template-columns: 280px 1fr 280px;
  grid-template-rows: 100vh;
  gap: 24px;
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
  overflow: hidden;
}

.panel {
  background: var(--panel);
  border: 1px solid var(--panel-edge);
  border-radius: 20px;
  padding: 20px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.game-area {
  display: grid;
  grid-template-rows: 1fr auto;
  gap: 16px;
  overflow: hidden;
}

.info-panel {
  gap: 12px;
}

.list-container {
  overflow-y: auto;
  flex: 1;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 12px;
  padding: 8px;
}

.log-list {
  font-family: monospace;
  font-size: 11px;
  flex: 0 0 200px; /* Fixed height for log */
}

.log-entry {
  margin-bottom: 4px;
  color: var(--muted);
  border-bottom: 1px solid rgba(255,255,255,0.03);
  padding-bottom: 2px;
}

.list-item {
  padding: 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  margin-bottom: 6px;
  font-size: 13px;
}
.list-item.active {
  border-left: 2px solid var(--good);
  background: linear-gradient(90deg, rgba(61, 220, 151, 0.05), transparent);
}

.ai-remove {
  margin-top: 6px;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.05);
  color: var(--ink);
  cursor: pointer;
  transition: 0.2s;
}
.ai-remove:hover {
  background: rgba(255, 255, 255, 0.1);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--muted);
}
.mt-4 { margin-top: 16px; }

@media (max-width: 1024px) {
  .app-container {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
    height: auto;
    overflow: visible;
  }
}
</style>
