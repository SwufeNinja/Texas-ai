<script setup lang="ts">
import { computed, ref, watch } from 'vue';

const props = defineProps<{
  canAct: boolean;
  canAllIn: boolean;
  toCall: number;
  minRaise: number;
  maxRaise: number;
  hint: string;
}>();

const emit = defineEmits<{
  (e: 'action', action: string, amount?: number): void
}>();

const raiseAmount = ref(0);

// Sync raiseAmount with minRaise when minRaise changes
watch(() => props.minRaise, (newVal) => {
  if (raiseAmount.value < newVal) {
    raiseAmount.value = newVal;
  }
}, { immediate: true });

const actionEnabled = (action: string) => {
  if (!props.canAct) return false;
  if (action === 'check') return props.toCall === 0;
  if (action === 'call') return props.toCall > 0;
  if (action === 'raise') {
    if (props.maxRaise < props.minRaise) return false;
    return raiseAmount.value >= props.minRaise && raiseAmount.value <= props.maxRaise;
  }
  if (action === 'allin') return props.canAllIn;
  return true;
};

const send = (action: string) => {
  if (action === 'raise') {
    emit('action', 'raise', raiseAmount.value || props.minRaise);
  } else {
    emit('action', action);
  }
};
</script>

<template>
  <section class="action-bar panel">
    <div class="raise-control" v-if="actionEnabled('raise')">
      <label>
        Raise To
        <input 
          class="input" 
          v-model.number="raiseAmount" 
          type="number" 
          :min="minRaise" 
          :max="maxRaise"
        />
      </label>
    </div>
    
    <div class="action-row">
      <button :disabled="!actionEnabled('fold')" @click="send('fold')">Fold</button>
      <button :disabled="!actionEnabled('check')" @click="send('check')">Check</button>
      <button :disabled="!actionEnabled('call')" @click="send('call')">Call {{ toCall > 0 ? toCall : '' }}</button>
      <button :disabled="!actionEnabled('raise')" @click="send('raise')">Raise</button>
      <button :disabled="!actionEnabled('allin')" @click="send('allin')">All-in</button>
    </div>
    
    <div class="hint">{{ hint }}</div>
  </section>
</template>

<style scoped>
.action-bar {
  display: grid;
  grid-template-columns: minmax(140px, auto) 1fr auto;
  gap: 16px;
  align-items: center;
  padding: 16px;
  background: var(--panel);
  border-top: 1px solid var(--panel-edge);
}

.action-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

button {
  min-width: 80px;
  padding: 12px 16px;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 13px;
  letter-spacing: 0.05em;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: var(--ink);
  cursor: pointer;
  transition: all 0.2s;
}

button:hover:not(:disabled) {
  background: rgba(86, 242, 214, 0.15);
  border-color: var(--accent);
  transform: translateY(-2px);
}

button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

.input {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--ink);
  padding: 8px 12px;
  border-radius: 6px;
  width: 100px;
  margin-left: 8px;
}

.hint {
  font-size: 12px;
  color: var(--muted);
  text-align: right;
  white-space: pre-line;
}

@media (max-width: 768px) {
  .action-bar {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .input { width: 100%; margin-left: 0; margin-top: 4px; }
  .hint { text-align: center; }
}
</style>
