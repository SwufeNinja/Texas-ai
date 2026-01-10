<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  card?: string; // e.g. "Ah", "Td"
  mini?: boolean;
}>();

const rank = computed(() => props.card ? props.card.slice(0, 1) : '');
const suit = computed(() => props.card ? props.card.slice(1, 2) : '');

const suitInfo = computed(() => {
  if (suit.value === 'h') return { id: 'suit-heart', isRed: true };
  if (suit.value === 'd') return { id: 'suit-diamond', isRed: true };
  if (suit.value === 'c') return { id: 'suit-club', isRed: false };
  return { id: 'suit-spade', isRed: false };
});

const isEmpty = computed(() => !props.card);
</script>

<template>
  <div 
    class="card" 
    :class="{ 
      mini: mini, 
      red: suitInfo.isRed, 
      empty: isEmpty 
    }"
  >
    <template v-if="!isEmpty">
      <span class="rank">{{ rank }}</span>
      <svg class="suit-icon" viewBox="0 0 64 64">
         <use :href="`#${suitInfo.id}`"></use>
      </svg>
    </template>
    <template v-else>--</template>
  </div>
</template>

<style scoped>
/* Card Styles migrated from global, kept minimal logic here if possible */
.card {
  width: 56px;
  height: 78px;
  border-radius: 10px;
  background: linear-gradient(160deg, #ffffff 0%, #f1f4f8 55%, #e3e9f2 100%);
  border: 1px solid rgba(10, 20, 35, 0.14);
  color: var(--card-black);
  font-weight: 700;
  display: grid;
  place-items: center;
  box-shadow: 0 10px 18px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.75);
  position: relative;
  overflow: hidden;
  user-select: none;
}

.card::after {
  content: "";
  position: absolute;
  inset: 6px;
  border-radius: 8px;
  background: linear-gradient(140deg, rgba(255, 255, 255, 0.35), transparent 55%);
  opacity: 0.7;
  pointer-events: none;
}

.rank {
  position: absolute;
  top: 6px;
  left: 6px;
  font-size: 14px;
}

.suit-icon {
  position: absolute;
  bottom: 6px;
  right: 6px;
  width: 18px;
  height: 18px;
  fill: currentColor;
}

.card.red {
  color: var(--card-red);
}

.card.empty {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.4);
  border: 1px dashed rgba(255, 255, 255, 0.18);
  box-shadow: none;
}
.card.empty::after { display: none; }

.card.mini {
  width: 34px;
  height: 46px;
  border-radius: 8px;
}
.card.mini .rank {
  font-size: 10px;
  top: 4px;
  left: 5px;
}
.card.mini .suit-icon {
  width: 14px;
  height: 14px;
  bottom: 4px;
  right: 5px;
}
</style>
