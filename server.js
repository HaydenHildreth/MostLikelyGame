const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// Serve static files
app.use(express.static('public'));

// Game state management
const rooms = new Map();

class GameRoom {
  constructor(roomId) {
    this.roomId = roomId;
    this.players = new Map();
    this.gameState = 'waiting'; // waiting, submitting, voting, results, finished
    this.currentRound = 0;
    this.prompts = [];
    this.currentPromptIndex = 0;
    this.votes = new Map();
    this.scores = new Map();
    this.timer = null;
    this.timeLeft = 0;
    this.lobbyLeader = null; // First player to join becomes leader
    this.lastActivity = Date.now(); // Track room activity for cleanup
  }

  addPlayer(socketId, playerName) {
    // Set first player as lobby leader
    if (this.players.size === 0) {
      this.lobbyLeader = socketId;
    }

    this.players.set(socketId, {
      id: socketId,
      name: playerName,
      ready: false,
      submitted: false,
      voted: false,
      isLeader: socketId === this.lobbyLeader
    });
    this.scores.set(socketId, 0);
    this.lastActivity = Date.now();
  }

  removePlayer(socketId) {
    this.players.delete(socketId);
    this.scores.delete(socketId);
    this.votes.delete(socketId);
    
    // If leader leaves, assign new leader
    if (socketId === this.lobbyLeader && this.players.size > 0) {
      const newLeader = this.players.keys().next().value;
      this.lobbyLeader = newLeader;
      this.players.get(newLeader).isLeader = true;
    }
    
    this.lastActivity = Date.now();
  }

  startGame() {
    if (this.players.size < 2) return false;
    
    this.gameState = 'submitting';
    this.currentRound = 1;
    this.prompts = [];
    this.currentPromptIndex = 0;
    
    // Reset player states
    this.players.forEach(player => {
      player.submitted = false;
      player.voted = false;
    });
    
    // Reset scores
    this.scores.forEach((score, playerId) => {
      this.scores.set(playerId, 0);
    });
    
    this.lastActivity = Date.now();
    this.startSubmissionTimer();
    return true;
  }

  startSubmissionTimer() {
    this.timeLeft = 60; // 60 seconds to submit
    this.timer = setInterval(() => {
      this.timeLeft--;
      if (this.timeLeft <= 0) {
        this.endSubmissionPhase();
      }
    }, 1000);
  }

  startVotingTimer() {
    this.timeLeft = 30; // 30 seconds to vote
    this.timer = setInterval(() => {
      this.timeLeft--;
      if (this.timeLeft <= 0) {
        this.endVotingPhase();
      }
    }, 1000);
  }

  submitPrompt(socketId, prompt) {
    if (this.gameState !== 'submitting') return false;
    
    const player = this.players.get(socketId);
    if (!player || player.submitted) return false;
    
    // Automatically add "Most likely to" if not present
    const formattedPrompt = prompt.toLowerCase().startsWith('most likely to') ? 
      prompt : `Most likely to ${prompt}`;
    
    this.prompts.push({
      playerId: socketId,
      playerName: player.name,
      prompt: formattedPrompt
    });
    
    player.submitted = true;
    this.lastActivity = Date.now();
    
    // Check if all players have submitted
    if ([...this.players.values()].every(p => p.submitted)) {
      this.endSubmissionPhase();
    }
    
    return true;
  }

  endSubmissionPhase() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    
    // If no prompts were submitted, end the game
    if (this.prompts.length === 0) {
      this.gameState = 'finished';
      io.to(this.roomId).emit('game-state', this.getGameState());
      return;
    }
    
    this.gameState = 'voting';
    this.votes.clear();
    
    // Reset voted status for all players
    this.players.forEach(player => {
      player.voted = false;
    });
    
    // Emit the voting state first
    io.to(this.roomId).emit('game-state', this.getGameState());
    
    this.startVotingTimer();
  }

  submitVote(socketId, votedPlayerId) {
    if (this.gameState !== 'voting') return false;
    
    const player = this.players.get(socketId);
    if (!player || player.voted) return false;
    
    this.votes.set(socketId, votedPlayerId);
    player.voted = true;
    this.lastActivity = Date.now();
    
    // Check if all players have voted
    if ([...this.players.values()].every(p => p.voted)) {
      this.endVotingPhase();
    }
    
    return true;
  }

  endVotingPhase() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    
    // Calculate votes (even if not everyone voted)
    const voteCount = new Map();
    this.votes.forEach(votedPlayerId => {
      voteCount.set(votedPlayerId, (voteCount.get(votedPlayerId) || 0) + 1);
    });
    
    // Award points
    voteCount.forEach((votes, playerId) => {
      this.scores.set(playerId, this.scores.get(playerId) + votes);
    });
    
    this.gameState = 'results';
    
    // Emit the results state first
    io.to(this.roomId).emit('game-state', this.getGameState());
    
    // Auto-proceed to next prompt after 3 seconds
    setTimeout(() => {
      this.nextPrompt();
    }, 3000);
  }

  nextPrompt() {
    this.currentPromptIndex++;
    
    if (this.currentPromptIndex >= this.prompts.length) {
      this.gameState = 'finished';
      // Emit the final state to all players
      io.to(this.roomId).emit('game-state', this.getGameState());
      return;
    }
    
    this.gameState = 'voting';
    this.votes.clear();
    
    // Reset voted status
    this.players.forEach(player => {
      player.voted = false;
    });
    
    // Emit the updated state before starting the timer
    io.to(this.roomId).emit('game-state', this.getGameState());
    
    this.startVotingTimer();
  }

  getCurrentPrompt() {
    if (this.currentPromptIndex < this.prompts.length) {
      return this.prompts[this.currentPromptIndex];
    }
    return null;
  }

  getGameState() {
    return {
      roomId: this.roomId,
      gameState: this.gameState,
      players: Array.from(this.players.values()),
      playerCount: this.players.size,
      currentRound: this.currentRound,
      currentPrompt: this.getCurrentPrompt(),
      timeLeft: this.timeLeft,
      scores: Object.fromEntries(this.scores),
      lobbyLeader: this.lobbyLeader,
      hasSubmitted: this.gameState === 'submitting' ? 
        Object.fromEntries([...this.players.entries()].map(([id, p]) => [id, p.submitted])) : {},
      hasVoted: this.gameState === 'voting' ? 
        Object.fromEntries([...this.players.entries()].map(([id, p]) => [id, p.voted])) : {},
      submissionCount: this.gameState === 'submitting' ? 
        [...this.players.values()].filter(p => p.submitted).length : 0,
      voteCount: this.gameState === 'voting' ? 
        [...this.players.values()].filter(p => p.voted).length : 0,
      voteResults: this.gameState === 'results' ? this.getVoteResults() : null
    };
  }

  getVoteResults() {
    const voteCount = new Map();
    const voteDetails = new Map();
    
    this.votes.forEach((votedPlayerId, voterId) => {
      voteCount.set(votedPlayerId, (voteCount.get(votedPlayerId) || 0) + 1);
      
      if (!voteDetails.has(votedPlayerId)) {
        voteDetails.set(votedPlayerId, []);
      }
      voteDetails.get(votedPlayerId).push(this.players.get(voterId).name);
    });
    
    return {
      voteCount: Object.fromEntries(voteCount),
      voteDetails: Object.fromEntries(voteDetails)
    };
  }
}

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log('User connected:', socket.id);

  socket.on('join-room', (data) => {
    const { roomId, playerName } = data;
    
    if (!roomId || !playerName) {
      socket.emit('error', { message: 'Room ID and player name are required' });
      return;
    }

    // Leave any existing rooms
    const currentRooms = Array.from(socket.rooms).filter(room => room !== socket.id);
    currentRooms.forEach(room => socket.leave(room));

    // Create room if it doesn't exist
    if (!rooms.has(roomId)) {
      rooms.set(roomId, new GameRoom(roomId));
    }

    const room = rooms.get(roomId);
    
    // Check if player name is already taken in this room
    const existingPlayer = [...room.players.values()].find(p => p.name === playerName);
    if (existingPlayer) {
      socket.emit('error', { message: 'Player name already taken in this room' });
      return;
    }

    // Add player to room (can join mid-game)
    room.addPlayer(socket.id, playerName);
    socket.join(roomId);
    socket.roomId = roomId;

    // If joining mid-game, set appropriate states
    if (room.gameState === 'submitting') {
      // New player hasn't submitted yet
      room.players.get(socket.id).submitted = false;
    } else if (room.gameState === 'voting') {
      // New player hasn't voted yet
      room.players.get(socket.id).voted = false;
    }

    // Emit updated game state to all players in room
    io.to(roomId).emit('game-state', room.getGameState());
    
    // Send welcome message to new player
    if (room.gameState !== 'waiting') {
      socket.emit('joined-ongoing-game', { 
        message: 'You joined a game in progress!' 
      });
    }
  });

  socket.on('start-game', () => {
    if (!socket.roomId) return;
    
    const room = rooms.get(socket.roomId);
    if (!room) return;
    
    // Only lobby leader can start the game
    if (socket.id !== room.lobbyLeader) {
      socket.emit('error', { message: 'Only the lobby leader can start the game' });
      return;
    }
    
    if (room.startGame()) {
      io.to(socket.roomId).emit('game-state', room.getGameState());
    } else {
      socket.emit('error', { message: 'Need at least 2 players to start' });
    }
  });

  socket.on('play-again', () => {
    if (!socket.roomId) return;
    
    const room = rooms.get(socket.roomId);
    if (!room) return;
    
    // Only lobby leader can start new game
    if (socket.id !== room.lobbyLeader) {
      socket.emit('error', { message: 'Only the lobby leader can start a new game' });
      return;
    }
    
    // Reset the room to waiting state
    room.gameState = 'waiting';
    room.currentRound = 0;
    room.prompts = [];
    room.currentPromptIndex = 0;
    room.votes.clear();
    room.lastActivity = Date.now();
    
    // Clear any active timer
    if (room.timer) {
      clearInterval(room.timer);
      room.timer = null;
    }
    
    // Reset player states but keep scores for reference
    room.players.forEach(player => {
      player.submitted = false;
      player.voted = false;
    });
    
    io.to(socket.roomId).emit('game-state', room.getGameState());
  });

  socket.on('submit-prompt', (data) => {
    if (!socket.roomId) return;
    
    const room = rooms.get(socket.roomId);
    if (!room) return;
    
    const { prompt } = data;
    if (room.submitPrompt(socket.id, prompt)) {
      io.to(socket.roomId).emit('game-state', room.getGameState());
    }
  });

  socket.on('submit-vote', (data) => {
    if (!socket.roomId) return;
    
    const room = rooms.get(socket.roomId);
    if (!room) return;
    
    const { playerId } = data;
    if (room.submitVote(socket.id, playerId)) {
      io.to(socket.roomId).emit('game-state', room.getGameState());
    }
  });

  socket.on('disconnect', () => {
    console.log('User disconnected:', socket.id);
    
    if (socket.roomId) {
      const room = rooms.get(socket.roomId);
      if (room) {
        room.removePlayer(socket.id);
        
        // If room is empty, delete it
        if (room.players.size === 0) {
          if (room.timer) clearInterval(room.timer);
          rooms.delete(socket.roomId);
        } else {
          io.to(socket.roomId).emit('game-state', room.getGameState());
        }
      }
    }
  });
});

// Send periodic updates for timer
setInterval(() => {
  rooms.forEach((room, roomId) => {
    if (room.gameState === 'submitting' || room.gameState === 'voting') {
      io.to(roomId).emit('timer-update', { timeLeft: room.timeLeft });
      
      // Force end phase if timer reaches 0 (safety check)
      if (room.timeLeft <= 0) {
        if (room.gameState === 'submitting') {
          room.endSubmissionPhase();
        } else if (room.gameState === 'voting') {
          room.endVotingPhase();
        }
      }
    }
  });
}, 1000);

// Room cleanup - remove inactive rooms every 5 minutes
setInterval(() => {
  const now = Date.now();
  const ROOM_TIMEOUT = 30 * 60 * 1000; // 30 minutes of inactivity
  
  rooms.forEach((room, roomId) => {
    if (now - room.lastActivity > ROOM_TIMEOUT) {
      console.log(`Cleaning up inactive room: ${roomId}`);
      if (room.timer) clearInterval(room.timer);
      rooms.delete(roomId);
    }
  });
}, 5 * 60 * 1000); // Check every 5 minutes

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
