const { createApp } = Vue;

createApp({
  data() {
    return {
      socket: null,
      connected: false,
      lastState: null,
      logItems: [],
      playerId: "p1",
      playerName: "Alice",
      aiId: "ai_1",
      aiName: "DealerBot",
      raiseAmount: 10,
      seatPositions: [
        { top: "8%", left: "50%", transform: "translate(-50%, -50%)" },
        { top: "20%", left: "85%", transform: "translate(-50%, -50%)" },
        { top: "70%", left: "88%", transform: "translate(-50%, -50%)" },
        { top: "92%", left: "50%", transform: "translate(-50%, -50%)" },
        { top: "70%", left: "12%", transform: "translate(-50%, -50%)" },
        { top: "20%", left: "15%", transform: "translate(-50%, -50%)" },
        { top: "8%", left: "20%", transform: "translate(-50%, -50%)" },
        { top: "8%", left: "80%", transform: "translate(-50%, -50%)" },
      ],
    };
  },
  computed: {
    wsUrl() {
      const scheme = location.protocol === "https:" ? "wss" : "ws";
      return `${scheme}://${location.host}/ws`;
    },
    connectionStatus() {
      return this.connected ? "Connected" : "Disconnected";
    },
    connectButtonText() {
      return this.connected ? "Disconnect" : "Connect";
    },
    me() {
      const players = this.lastState?.players || [];
      return players.find((player) => player.id === this.playerId) || null;
    },
    isMyTurn() {
      return this.lastState?.current_player_id === this.playerId;
    },
    toCall() {
      if (!this.me || !this.lastState) {
        return 0;
      }
      return Math.max(0, (this.lastState.current_bet || 0) - this.me.bet);
    },
    minRaise() {
      const bigBlind = Number(this.lastState?.big_blind || 0);
      const lastRaise = Number(this.lastState?.last_raise_size || 0);
      return Math.max(bigBlind, lastRaise);
    },
    maxRaise() {
      if (!this.me) {
        return 0;
      }
      return Math.max(0, this.me.chips - this.toCall);
    },
    canAct() {
      return Boolean(this.me && this.me.status === "PLAYING" && this.me.ready);
    },
    handInProgress() {
      if (!this.lastState) {
        return false;
      }
      if (this.lastState.awaiting_ready) {
        return false;
      }
      if (this.lastState.stage && this.lastState.stage !== "PREFLOP") {
        return true;
      }
      if ((this.lastState.pot || 0) > 0) {
        return true;
      }
      return Array.isArray(this.lastState.community_cards) && this.lastState.community_cards.length > 0;
    },
    canRemoveAi() {
      return !this.handInProgress;
    },
    seatedPlayers() {
      const players = this.lastState?.players || [];
      return players.filter((player) => player.seated);
    },
    waitingPlayers() {
      const players = this.lastState?.players || [];
      return players.filter((player) => !player.seated);
    },
    communityDisplay() {
      const cards = this.lastState?.community_cards || [];
      if (cards.length) {
        return cards;
      }
      return ["", "", "", "", ""];
    },
    readyActive() {
      return Boolean(this.me && this.me.ready);
    },
    readyDisabled() {
      if (!this.me || !this.me.seated) {
        return true;
      }
      return this.handInProgress && this.me.ready;
    },
    readyButtonText() {
      if (this.me && this.me.ready) {
        return "Unready";
      }
      return "Ready";
    },
    actionHint() {
      if (!this.me) {
        return "Not seated.";
      }
      let turnLabel = "Waiting for ready";
      if (this.me && !this.me.seated) {
        turnLabel = "Spectating (waiting for a seat)";
      }
      if (this.canAct) {
        turnLabel = this.isMyTurn ? "Your turn" : "Waiting for others";
      }
      return `${turnLabel} | To call: ${this.toCall} | Min raise: ${this.minRaise} | Max raise: ${this.maxRaise}`;
    },
  },
  methods: {
    log(message) {
      this.logItems.unshift(message);
    },
    toggleConnection() {
      if (this.socket && this.socket.readyState !== WebSocket.CLOSED) {
        const ok = window.confirm("Are you sure you want to disconnect?");
        if (!ok) {
          return;
        }
        this.socket.close();
        return;
      }
      this.connect();
    },
    connect() {
      if (!this.playerId.trim()) {
        return;
      }
      const socket = new WebSocket(this.wsUrl);
      this.socket = socket;
      socket.addEventListener("open", () => {
        socket.send(
          JSON.stringify({
            type: "join",
            data: { player_id: this.playerId.trim(), name: this.playerName.trim() },
          })
        );
      });
      socket.addEventListener("message", (event) => {
        const payload = JSON.parse(event.data);
        if (payload.type === "game_update") {
          this.lastState = payload.data;
          this.connected = true;
        } else if (payload.type === "join_ok") {
          this.connected = true;
        } else if (payload.type === "error") {
          const details = this.formatDetails(payload.data.details);
          this.log(`Error: ${payload.data.message} ${details}`.trim());
        } else if (payload.type === "system") {
          this.log(this.formatSystemMessage(payload.data || {}));
        }
      });
      socket.addEventListener("close", () => {
        this.connected = false;
        this.socket = null;
      });
    },
    toggleReady() {
      if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
        return;
      }
      const nextReady = this.me ? !this.me.ready : true;
      this.socket.send(JSON.stringify({ type: "ready", data: { ready: nextReady } }));
    },
    sendAction(action) {
      if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
        return;
      }
      const amount = action === "raise" ? Number(this.raiseAmount || 0) : 0;
      this.socket.send(
        JSON.stringify({
          type: "action",
          data: { action, amount },
        })
      );
    },
    addAi() {
      const id = this.aiId.trim();
      const name = this.aiName.trim() || "AI";
      if (!id) {
        return;
      }
      fetch("/ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player_id: id, name }),
      })
        .then((response) => response.json())
        .then((payload) => {
          this.log(payload.ok ? `AI ${id} added` : `AI add failed: ${payload.message}`);
        });
    },
    removeAi(aiId) {
      if (this.handInProgress) {
        this.log("AI remove failed: game already started");
        return;
      }
      fetch("/ai/remove", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player_id: aiId }),
      })
        .then((response) => response.json())
        .then((payload) => {
          this.log(payload.ok ? `AI ${aiId} removed` : `AI remove failed: ${payload.message}`);
        });
    },
    actionEnabled(action) {
      if (!this.isMyTurn || !this.canAct) {
        return false;
      }
      if (action === "check") {
        return this.toCall === 0;
      }
      if (action === "call") {
        return this.toCall > 0;
      }
      if (action === "raise") {
        return this.toCall >= 0;
      }
      return true;
    },
    suitSymbol(suit) {
      if (suit === "h") {
        return {
          svg: "<svg class='suit-icon' viewBox='0 0 64 64'><use href='/static/suits.svg#suit-heart'></use></svg>",
          isRed: true,
        };
      }
      if (suit === "d") {
        return {
          svg: "<svg class='suit-icon' viewBox='0 0 64 64'><use href='/static/suits.svg#suit-diamond'></use></svg>",
          isRed: true,
        };
      }
      if (suit === "c") {
        return {
          svg: "<svg class='suit-icon' viewBox='0 0 64 64'><use href='/static/suits.svg#suit-club'></use></svg>",
          isRed: false,
        };
      }
      return {
        svg: "<svg class='suit-icon' viewBox='0 0 64 64'><use href='/static/suits.svg#suit-spade'></use></svg>",
        isRed: false,
      };
    },
    cardClass(card, mini) {
      if (!card) {
        return { mini, empty: true };
      }
      const suit = card.slice(1, 2);
      const suitInfo = this.suitSymbol(suit);
      return { mini, red: suitInfo.isRed };
    },
    handDisplay(player) {
      if (!player.hand || !player.hand.length) {
        return ["", ""];
      }
      return player.hand;
    },
    seatClass(player) {
      return {
        current: player.id === this.lastState?.current_player_id,
        active: player.status === "PLAYING",
      };
    },
    playerRowClass(player) {
      return {
        current: player.id === this.lastState?.current_player_id,
        active: player.status === "PLAYING",
      };
    },
    seatStyle(index) {
      return this.seatPositions[index % this.seatPositions.length];
    },
    readyLabel(player) {
      return player.ready ? "Ready" : "Not Ready";
    },
    formatDetails(details) {
      const entries = Object.entries(details || {});
      if (!entries.length) {
        return "";
      }
      const items = entries
        .map(([key, value]) => `<span>${key}: ${value}</span>`)
        .join(" | ");
      return `<span class="detail-line">${items}</span>`;
    },
    formatSystemMessage(data) {
      const event = data.event || "system";
      const playerId = data.player_id ? ` ${data.player_id}` : "";
      if (event === "player_joined") {
        const status = data.waiting ? "waiting" : "seated";
        return `System: ${event}${playerId} (${status})`;
      }
      return `System: ${event}${playerId}`;
    },
  },
}).mount("#app");
