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
  }

  addPlayer(socketId, playerName) {
    this.players.set(socketId, {
      id: socketId,
      name: playerName,
      ready: false,
      submitted: false,
      voted: false
    });
    this.scores.set(socketId, 0);
  }

  removePlayer(socketId) {
    this.players.delete(socketId);
    this.scores.delete(socketId);
    this.votes.delete(socketId);
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
    
    if (this.prompts.length === 0) {
      this.gameState = 'finished';
      return;
    }
    
    this.gameState = 'voting';
    this.votes.clear();
    
    // Reset voted status
    this.players.forEach(player => {
      player.voted = false;
    });
    
    this.startVotingTimer();
  }

  submitVote(socketId, votedPlayerId) {
    if (this.gameState !== 'voting') return false;
    
    const player = this.players.get(socketId);
    if (!player || player.voted) return false;
    
    this.votes.set(socketId, votedPlayerId);
    player.voted = true;
    
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
    
    // Calculate votes
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
      hasSubmitted: this.gameState === 'submitting' ? 
        Object.fromEntries([...this.players.entries()].map(([id, p]) => [id, p.submitted])) : {},
      hasVoted: this.gameState === 'voting' ? 
        Object.fromEntries([...this.players.entries()].map(([id, p]) => [id, p.voted])) : {},
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
    
    // Check if game is already in progress
    if (room.gameState !== 'waiting' && !room.players.has(socket.id)) {
      socket.emit('error', { message: 'Game already in progress' });
      return;
    }

    // Add player to room
    room.addPlayer(socket.id, playerName);
    socket.join(roomId);
    socket.roomId = roomId;

    // Emit updated game state to all players in room
    io.to(roomId).emit('game-state', room.getGameState());
  });

  socket.on('start-game', () => {
    if (!socket.roomId) return;
    
    const room = rooms.get(socket.roomId);
    if (!room) return;
    
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
    
    // Reset the room to waiting state
    room.gameState = 'waiting';
    room.currentRound = 0;
    room.prompts = [];
    room.currentPromptIndex = 0;
    room.votes.clear();
    
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
    }
  });
}, 1000);

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
