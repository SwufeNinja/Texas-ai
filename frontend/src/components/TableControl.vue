<script setup lang="ts">
import type { Player } from '../types';

const props = defineProps<{
  playerId: string;
  playerName: string;
  aiId: string;
  aiName: string;
  connected: boolean;
  connectionLabel: string;
  connectBtnText: string;
  readyActive: boolean;
  readyDisabled: boolean;
  readyBtnText: string;
  waitingPlayers: Player[];
  canRemoveAi: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:playerId', value: string): void;
  (e: 'update:playerName', value: string): void;
  (e: 'update:aiId', value: string): void;
  (e: 'update:aiName', value: string): void;
  (e: 'connect-toggle'): void;
  (e: 'toggle-ready', value: boolean): void;
  (e: 'add-ai'): void;
  (e: 'remove-ai', id: string): void;
}>();

const updateValue = (e: Event) =>
  e.target instanceof HTMLInputElement ? e.target.value : '';
</script>

<template>
  <aside class="panel control-panel">
    <div class="title">Table Control</div>
    <div class="badge" :class="{ connected }">{{ connectionLabel }}</div>

    <div class="stack">
      <div class="section player-section">
        <div class="section-title">Player</div>

        <label class="field">
          <span class="label">Player ID</span>
          <input
            class="input"
            :value="playerId"
            @input="emit('update:playerId', updateValue($event))"
          />
        </label>

        <label class="field">
          <span class="label">Name</span>
          <input
            class="input"
            :value="playerName"
            @input="emit('update:playerName', updateValue($event))"
          />
        </label>

        <div class="btn-row">
          <button class="btn btn--primary" @click="emit('connect-toggle')">
            {{ connectBtnText }}
          </button>

          <button
            class="btn"
            :class="{ 'btn--ready': readyActive }"
            :disabled="readyDisabled"
            @click="emit('toggle-ready', readyActive)"
          >
            {{ readyBtnText }}
          </button>
        </div>
      </div>

      <div class="section ai-section">
        <div class="section-title">AI</div>

        <label class="field">
          <span class="label">AI ID</span>
          <input
            class="input"
            :value="aiId"
            @input="emit('update:aiId', updateValue($event))"
          />
        </label>

        <label class="field">
          <span class="label">AI Name</span>
          <input
            class="input"
            :value="aiName"
            @input="emit('update:aiName', updateValue($event))"
          />
        </label>

        <button
          class="btn btn--primary"
          :disabled="!canRemoveAi"
          @click="emit('add-ai')"
        >
          Add AI
        </button>
      </div>
    </div>

    <!-- Waiting: 贴底 + 自适应高度 + 只有 list 滚动 -->
    <div class="waiting-panel section waiting-section">
      <div class="waiting-header">
        <div class="section-title">Waiting</div>
        <div class="count" v-if="waitingPlayers.length">
          {{ waitingPlayers.length }}
        </div>
      </div>

      <div class="waiting-list">
        <div
          v-for="p in waitingPlayers"
          :key="p.id"
          class="list-item waiting"
        >
          <div class="row">
            <div class="row-text">
              <div class="row-main">
                {{ p.name }} <small>({{ p.id }})</small>
              </div>
              <div class="row-sub">Spectating</div>
            </div>

            <button
              v-if="p.is_ai && canRemoveAi"
              class="btn btn--danger btn--sm"
              @click="emit('remove-ai', p.id)"
            >
              Remove
            </button>
          </div>
        </div>

        <div v-if="!waitingPlayers.length" class="empty-state">
          No waiting players
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.panel {
  background: var(--panel);
  border: 1px solid var(--panel-edge);
  border-radius: 20px;
  padding: 20px;
  display: flex;
  flex-direction: column;

  /* ✅ 1) 取消 overflow:hidden，避免内容被裁掉 */
  overflow: visible;

  /* 自适应容器宽度 */
  width: 100%;
  min-width: 0;
}

.control-panel {
  justify-content: flex-start;
  max-height: calc(100vh - 48px);

  /* 让 waiting 能“贴底”，中间 stack 占用剩余空间 */
  gap: 12px;
}

.title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 4px;
}

.badge {
  display: inline-flex;
  padding: 4px 12px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--muted);
  font-size: 12px;
  text-transform: uppercase;
  align-self: flex-start;
  border: 1px solid transparent;
}
.badge.connected {
  background: rgba(86, 242, 214, 0.12);
  color: var(--accent);
  border-color: rgba(86, 242, 214, 0.3);
}

.stack {
  display: grid;
  gap: 12px;

  /* 让 stack 在中间区域弹性伸缩 */
  flex: 0 0 auto;
  min-width: 0;
}

.section {
  display: grid;
  gap: 10px;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(0, 0, 0, 0.15);
  min-width: 0;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.player-section {
  /* ✅ 自适应，不写死宽高 */
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
}

.ai-section {
  border-color: rgba(86, 242, 214, 0.16);
}

.field {
  display: grid;
  gap: 6px;
}

.label {
  font-size: 12px;
  color: var(--muted);
}

.input {
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(0, 0, 0, 0.2);
  color: var(--ink);
  min-width: 0;
}

.divider {
  border: 0;
  border-top: 1px solid var(--panel-edge);
  margin: 4px 0;
  display: block;
  width: 100%;
}

/* ✅ 3) 按钮分级（替代全局 button 样式） */
.btn {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.05);
  color: var(--ink);
  cursor: pointer;
  transition: 0.2s;
  width: 100%;
}

.btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn--primary {
  border-color: rgba(86, 242, 214, 0.25);
  background: rgba(86, 242, 214, 0.12);
  color: var(--ink);
}

.btn--ready {
  border-color: var(--good);
  background: rgba(61, 220, 151, 0.15);
  color: var(--good);
}

.btn--danger {
  width: auto;
  border-color: rgba(255, 99, 99, 0.35);
  background: rgba(255, 99, 99, 0.12);
}

.btn--sm {
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 12px;
}

/* 两个主按钮并排 */
.btn-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

/* ✅ 2) waiting：贴底 + 自适应高度；只有 waiting-list 滚动 */
.waiting-panel {
  margin-top: auto; /* 贴底 */
  display: grid;
  gap: 10px;

  /* 自适应：占用剩余空间，但不强制固定 */
  min-height: 320px;
  max-height: 42vh;
}

.waiting-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.count {
  font-size: 12px;
  color: var(--muted);
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 8px;
  border-radius: 999px;
}

.waiting-list {
  /* ✅ 只保留这一个滚动容器 */
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 12px;
  padding: 8px;
  min-height: 0; /* 允许在 flex/grid 中正确收缩 */
}

.list-item {
  padding: 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  margin-bottom: 6px;
  font-size: 13px;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.row-text {
  min-width: 0;
}

.row-main {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-sub {
  font-size: 12px;
  color: var(--muted);
  margin-top: 2px;
}

.empty-state {
  font-size: 12px;
  color: var(--muted);
  text-align: center;
  padding: 12px 0;
}
</style>
