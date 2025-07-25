from bottle import route, run

@route('/')
def main():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Most Likely To - Multiplayer Game</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .game-container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            max-width: 800px;
            width: 100%;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }

        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .join-phase, .lobby-phase, .submission-phase, .voting-phase, .results-phase {
            display: none;
        }

        .join-phase.active, .lobby-phase.active, .submission-phase.active, .voting-phase.active, .results-phase.active {
            display: block;
        }

        .input-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
        }

        input[type="text"], input[type="number"] {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            font-size: 16px;
            backdrop-filter: blur(5px);
        }

        input[type="text"]::placeholder, input[type="number"]::placeholder {
            color: rgba(255, 255, 255, 0.7);
        }

        .btn {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease;
            margin: 10px 5px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .player-list {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
        }

        .player-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .player-item.host {
            border: 2px solid gold;
        }

        .timer {
            text-align: center;
            font-size: 3em;
            font-weight: bold;
            margin: 20px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }

        .submission-item, .voting-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            margin: 15px 0;
            border-radius: 15px;
            text-align: center;
        }

        .vote-buttons {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
            margin-top: 15px;
        }

        .vote-btn {
            background: rgba(255, 255, 255, 0.2);
            border: 2px solid transparent;
            padding: 8px 15px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .vote-btn:hover {
            border-color: white;
            background: rgba(255, 255, 255, 0.3);
        }

        .vote-btn.selected {
            background: #ff6b6b;
            border-color: white;
        }

        .results-list {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }

        .result-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            margin: 8px 0;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }

        .crown {
            color: gold;
            font-size: 1.5em;
        }

        .status-message {
            text-align: center;
            padding: 15px;
            margin: 15px 0;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }

        .submission-status {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
        }

        .submitted-indicator {
            color: #4CAF50;
            font-weight: bold;
        }

        .waiting-indicator {
            color: #FFC107;
            font-weight: bold;
        }

        @media (max-width: 600px) {
            .game-container {
                padding: 20px;
            }
            
            h1 {
                font-size: 2em;
            }
            
            .timer {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="game-container">
        <h1>🎉 Most Likely To 🎉</h1>

        <!-- Join Phase -->
        <div class="join-phase active">
            <div class="input-group">
                <label for="playerName">Enter your name to join:</label>
                <input type="text" id="playerName" placeholder="Your name">
                <button class="btn" onclick="joinGame()">Join Game</button>
            </div>
            
            <div class="input-group">
                <label for="gameCode">Game Code (leave empty to create new room):</label>
                <input type="text" id="gameCode" placeholder="Enter code to join existing game">
            </div>
            
            <div class="status-message" id="joinStatus"></div>
        </div>

        <!-- Lobby Phase -->
        <div class="lobby-phase">
            <h2>Game Lobby</h2>
            <div class="status-message">
                <strong>Game Code: <span id="currentGameCode">MAIN</span></strong><br>
                Share this code with other players!
            </div>
            
            <div class="player-list" id="playerList">
                <h3>Players in lobby:</h3>
            </div>
            
            <div id="hostControls" style="display: none;">
                <div class="input-group">
                    <label for="timeLimit">Time limit for submissions (seconds):</label>
                    <input type="number" id="timeLimit" value="60" min="30" max="300">
                </div>
                <button class="btn" onclick="startGame()">Start Game (min 3 players)</button>
            </div>
            
            <div id="playerWaiting" class="status-message">
                Waiting for host to start the game...
            </div>
        </div>

        <!-- Submission Phase -->
        <div class="submission-phase">
            <h2>Round <span id="roundNumber">1</span></h2>
            <div class="timer" id="submissionTimer">60</div>
            
            <div class="input-group" id="submissionInput">
                <label for="submission">Enter your "Most likely to..." prompt:</label>
                <input type="text" id="submission" placeholder="Most likely to... (complete the sentence)">
                <button class="btn" onclick="submitPrompt()">Submit</button>
            </div>
            
            <div class="submission-status" id="submissionStatus">
                <h3>Submission Status:</h3>
                <div id="submissionList"></div>
            </div>
        </div>

        <!-- Voting Phase -->
        <div class="voting-phase">
            <h2>Voting Time!</h2>
            <div id="votingContent"></div>
            <div class="status-message" id="votingStatus"></div>
        </div>

        <!-- Results Phase -->
        <div class="results-phase">
            <h2>Round Results!</h2>
            <div id="resultsContent"></div>
            <div id="hostResultsControls" style="display: none;">
                <button class="btn" onclick="nextRound()">Next Round</button>
                <button class="btn" onclick="endGame()">End Game</button>
            </div>
            <div id="playerResultsWaiting" class="status-message">
                Waiting for host to continue...
            </div>
        </div>
    </div>

    <script>
        let gameState = {
            gameCode: 'MAIN',
            playerName: '',
            isHost: false,
            gamePhase: 'join',
            hasSubmitted: false,
            hasVoted: false,
            currentVoteIndex: 0,
            selectedVote: null,
            submissionTimer: null
        };

        let updateInterval;

        // Use localStorage for cross-browser sharing with polling
        function getGameData() {
            try {
                const data = JSON.parse(localStorage.getItem(`mostLikelyGame_${gameState.gameCode}`) || '{}');
                return {
                    players: data.players || [],
                    host: data.host || '',
                    phase: data.phase || 'lobby',
                    round: data.round || 1,
                    timeLimit: data.timeLimit || 60,
                    submissions: data.submissions || [],
                    votes: data.votes || {},
                    currentVoteIndex: data.currentVoteIndex || 0,
                    startTime: data.startTime || 0,
                    lastUpdate: data.lastUpdate || Date.now(),
                    ...data
                };
            } catch (e) {
                console.error('Error reading game data:', e);
                return {
                    players: [],
                    host: '',
                    phase: 'lobby',
                    round: 1,
                    timeLimit: 60,
                    submissions: [],
                    votes: {},
                    currentVoteIndex: 0,
                    startTime: 0,
                    lastUpdate: Date.now()
                };
            }
        }

        function setGameData(data) {
            try {
                data.lastUpdate = Date.now();
                localStorage.setItem(`mostLikelyGame_${gameState.gameCode}`, JSON.stringify(data));
            } catch (e) {
                console.error('Error saving game data:', e);
            }
        }

        function joinGame() {
            const nameInput = document.getElementById('playerName');
            const codeInput = document.getElementById('gameCode');
            const name = nameInput.value.trim();
            let code = codeInput.value.trim();
            
            if (!name) {
                document.getElementById('joinStatus').innerHTML = 
                    '<span style="color: #f44336;">Please enter your name!</span>';
                return;
            }
            
            // Generate random game code if empty
            if (!code) {
                code = Math.random().toString(36).substring(2, 8).toUpperCase();
            }
            
            // Set game state BEFORE getting game data
            gameState.playerName = name;
            gameState.gameCode = code;
            
            const gameData = getGameData();
            
            // Check if name is already taken
            if (gameData.players.some(p => p.name === name)) {
                document.getElementById('joinStatus').innerHTML = 
                    '<span style="color: #f44336;">Name already taken! Please choose another.</span>';
                return;
            }
            
            // Add player to game
            const newPlayer = { name: name, hasSubmitted: false, hasVoted: false };
            gameData.players.push(newPlayer);
            
            // Set host if first player
            if (gameData.players.length === 1) {
                gameData.host = name;
                gameState.isHost = true;
            }
            
            setGameData(gameData);
            document.getElementById('currentGameCode').textContent = code;
            switchPhase('lobby');
            startGameUpdates();
        }

        function startGameUpdates() {
            updateInterval = setInterval(updateGameState, 500); // Faster updates for better sync
            updateGameState();
        }

        function updateGameState() {
            const gameData = getGameData();
            
            // Check if game still exists and player is still in it
            if (!gameData.players.some(p => p.name === gameState.playerName)) {
                // Player was removed or game ended
                return;
            }
            
            // Update player list
            updatePlayerList(gameData);
            
            // Handle phase transitions
            if (gameData.phase !== gameState.gamePhase) {
                gameState.gamePhase = gameData.phase;
                
                if (gameData.phase === 'submission') {
                    switchPhase('submission');
                    // Reset submission state properly for new rounds
                    const currentPlayer = gameData.players.find(p => p.name === gameState.playerName);
                    gameState.hasSubmitted = currentPlayer ? currentPlayer.hasSubmitted : false;
                    startSubmissionPhase(gameData);
                } else if (gameData.phase === 'voting') {
                    switchPhase('voting');
                    gameState.hasVoted = false;
                    gameState.currentVoteIndex = 0;
                    gameState.selectedVote = null;
                    startVotingPhase(gameData);
                } else if (gameData.phase === 'results') {
                    switchPhase('results');
                    showResults(gameData);
                }
            }
            
            // Update submission status
            if (gameData.phase === 'submission') {
                updateSubmissionStatus(gameData);
                updateSubmissionTimer(gameData);
            }
            
            // Update voting status
            if (gameData.phase === 'voting') {
                updateVotingPhase(gameData);
                // Host checks for vote progression every update cycle
                checkVoteProgression(gameData);
            }
        }

        function updatePlayerList(gameData) {
            const playerList = document.getElementById('playerList');
            if (!playerList) return;
            
            const playersHtml = gameData.players.map(player => 
                `<div class="player-item ${player.name === gameData.host ? 'host' : ''}">
                    <span>${player.name} ${player.name === gameData.host ? '👑' : ''}</span>
                    <span>${gameData.phase === 'submission' ? 
                        (player.hasSubmitted ? '✓' : '⏳') : ''}</span>
                </div>`
            ).join('');
            
            playerList.innerHTML = `<h3>Players (${gameData.players.length}):</h3>` + playersHtml;
            
            // Show/hide host controls
            const hostControls = document.getElementById('hostControls');
            const playerWaiting = document.getElementById('playerWaiting');
            if (hostControls && playerWaiting) {
                if (gameState.isHost) {
                    hostControls.style.display = 'block';
                    playerWaiting.style.display = 'none';
                } else {
                    hostControls.style.display = 'none';
                    playerWaiting.style.display = 'block';
                }
            }
        }

        function startGame() {
            const gameData = getGameData();
            if (gameData.players.length < 3) {
                alert('Need at least 3 players to start!');
                return;
            }
            
            gameData.phase = 'submission';
            gameData.round = 1;
            gameData.timeLimit = parseInt(document.getElementById('timeLimit').value);
            gameData.submissions = [];
            gameData.votes = {};
            gameData.startTime = Date.now();
            gameData.players.forEach(p => p.hasSubmitted = false);
            
            setGameData(gameData);
        }

        function startSubmissionPhase(gameData) {
            document.getElementById('roundNumber').textContent = gameData.round;
            gameData.startTime = gameData.startTime || Date.now();
            setGameData(gameData);
            
            // Clear the input field only when starting a new submission phase
            const submissionInputField = document.getElementById('submission');
            if (submissionInputField && !gameState.hasSubmitted) {
                submissionInputField.value = '';
            }
            
            // Start the submission timer only if we're the host
            if (gameState.isHost) {
                startSubmissionTimer(gameData);
            }
        }

        function startSubmissionTimer(gameData) {
            // Clear any existing timer
            if (gameState.submissionTimer) {
                clearInterval(gameState.submissionTimer);
            }
            
            gameState.submissionTimer = setInterval(() => {
                const updatedGameData = getGameData();
                
                // Check if we're still in submission phase
                if (updatedGameData.phase !== 'submission') {
                    clearInterval(gameState.submissionTimer);
                    gameState.submissionTimer = null;
                    return;
                }
                
                const timeElapsed = Math.floor((Date.now() - updatedGameData.startTime) / 1000);
                const timeLeft = Math.max(0, updatedGameData.timeLimit - timeElapsed);
                
                // Check if time is up or all players submitted
                const allSubmitted = updatedGameData.players.every(p => p.hasSubmitted);
                if (timeLeft === 0 || allSubmitted) {
                    clearInterval(gameState.submissionTimer);
                    gameState.submissionTimer = null;
                    
                    // Move to voting phase
                    updatedGameData.phase = 'voting';
                    updatedGameData.currentVoteIndex = 0;
                    updatedGameData.players.forEach(p => p.hasVoted = false);
                    setGameData(updatedGameData);
                }
            }, 1000);
        }

        function updateSubmissionTimer(gameData) {
            const timeElapsed = Math.floor((Date.now() - gameData.startTime) / 1000);
            const timeLeft = Math.max(0, gameData.timeLimit - timeElapsed);
            
            const timerEl = document.getElementById('submissionTimer');
            if (timerEl) {
                timerEl.textContent = timeLeft;
            }
        }

        function updateSubmissionStatus(gameData) {
            const submissionList = document.getElementById('submissionList');
            if (!submissionList) return;
            
            const statusHtml = gameData.players.map(player => 
                `<div style="display: flex; justify-content: space-between; margin: 5px 0;">
                    <span>${player.name}</span>
                    <span class="${player.hasSubmitted ? 'submitted-indicator' : 'waiting-indicator'}">
                        ${player.hasSubmitted ? '✓ Submitted' : '⏳ Waiting...'}
                    </span>
                </div>`
            ).join('');
            
            submissionList.innerHTML = statusHtml;
            
            // Show/hide submission input based on current player's submission status
            const submissionInput = document.getElementById('submissionInput');
            const submissionInputField = document.getElementById('submission');
            const currentPlayer = gameData.players.find(p => p.name === gameState.playerName);
            
            if (currentPlayer && currentPlayer.hasSubmitted) {
                submissionInput.style.display = 'none';
            } else {
                submissionInput.style.display = 'block';
                // Only clear the input if it's empty and we're in a new round
                // Don't clear if user is actively typing
                if (submissionInputField && submissionInputField.value === '' && !gameState.hasSubmitted) {
                    // Input is already empty, no need to clear
                }
            }
        }

        function submitPrompt() {
            if (gameState.hasSubmitted) return;
            
            const input = document.getElementById('submission');
            const prompt = input.value.trim();
            
            if (!prompt) {
                alert('Please enter a prompt!');
                return;
            }
            
            const gameData = getGameData();
            
            // Add submission
            gameData.submissions.push({
                prompt: prompt,
                submitter: gameState.playerName
            });
            
            // Mark player as submitted
            const player = gameData.players.find(p => p.name === gameState.playerName);
            if (player) {
                player.hasSubmitted = true;
            }
            
            gameState.hasSubmitted = true;
            setGameData(gameData);
            
            input.value = '';
            document.getElementById('submissionInput').style.display = 'none';
        }

        function startVotingPhase(gameData) {
            showCurrentVote(gameData);
        }

        function updateVotingPhase(gameData) {
            // Update vote count display
            const votedCount = Object.keys(gameData.votes).filter(key => 
                key.startsWith(`${gameData.currentVoteIndex}_`)
            ).length;
            
            const statusEl = document.getElementById('votingStatus');
            if (statusEl) {
                statusEl.innerHTML = `Votes submitted: ${votedCount}/${gameData.players.length}`;
            }
            
            // Handle vote index changes
            if (gameData.currentVoteIndex !== gameState.currentVoteIndex) {
                gameState.currentVoteIndex = gameData.currentVoteIndex;
                gameState.hasVoted = false;
                gameState.selectedVote = null;
                showCurrentVote(gameData);
            } else {
                // Check if this player has voted for the current question
                const hasVotedForCurrent = gameData.votes[`${gameData.currentVoteIndex}_${gameState.playerName}`];
                if (hasVotedForCurrent && !gameState.hasVoted) {
                    gameState.hasVoted = true;
                    gameState.selectedVote = hasVotedForCurrent;
                    // Update UI to reflect voted state
                    const selectedEl = document.getElementById('selectedVote');
                    const submitBtn = document.getElementById('submitVoteBtn');
                    if (selectedEl && submitBtn) {
                        selectedEl.textContent = `You voted for: ${hasVotedForCurrent}`;
                        submitBtn.textContent = 'Vote Submitted ✓';
                        submitBtn.disabled = true;
                    }
                }
            }
        }

        function showCurrentVote(gameData) {
            if (gameData.currentVoteIndex >= gameData.submissions.length) {
                if (gameState.isHost) {
                    gameData.phase = 'results';
                    setGameData(gameData);
                }
                return;
            }
            
            const submission = gameData.submissions[gameData.currentVoteIndex];
            const votingContent = document.getElementById('votingContent');
            
            // Allow voting for ALL players
            const playersButtons = gameData.players.map(player => 
                `<button class="vote-btn" onclick="selectVote('${player.name}')" id="vote-${player.name}">${player.name}</button>`
            ).join('');
            
            // Check if this player has already voted
            const existingVote = gameData.votes[`${gameData.currentVoteIndex}_${gameState.playerName}`];
            const hasVoted = !!existingVote;
            
            votingContent.innerHTML = `
                <div class="voting-item">
                    <h3>"${submission.prompt}"</h3>
                    <p style="font-style: italic; margin: 10px 0; opacity: 0.8;">
                        Submitted by: ${submission.submitter}
                    </p>
                    <div class="vote-buttons">
                        ${playersButtons}
                    </div>
                    <div style="margin-top: 20px;">
                        <div id="selectedVote" style="margin-bottom: 15px; font-weight: bold; color: #4CAF50;"></div>
                        <button class="btn" id="submitVoteBtn" onclick="submitVote()" disabled>
                            ${hasVoted ? 'Change Vote' : 'Submit Vote'}
                        </button>
                    </div>
                </div>
            `;
            
            // If player already voted, show their selection
            if (hasVoted) {
                document.getElementById('selectedVote').textContent = `You voted for: ${existingVote}`;
                document.getElementById(`vote-${existingVote}`).classList.add('selected');
                document.getElementById('submitVoteBtn').disabled = false;
                gameState.selectedVote = existingVote;
            }
            
            // Update voting status
            const votedCount = Object.keys(gameData.votes).filter(key => 
                key.startsWith(`${gameData.currentVoteIndex}_`)
            ).length;
            
            document.getElementById('votingStatus').innerHTML = 
                `Votes submitted: ${votedCount}/${gameData.players.length}`;
        }

        function selectVote(player) {
            // Visual feedback - remove previous selection
            document.querySelectorAll('.vote-btn').forEach(btn => btn.classList.remove('selected'));
            document.getElementById(`vote-${player}`).classList.add('selected');
            
            // Store selected vote locally (not submitted yet)
            gameState.selectedVote = player;
            
            // Update UI
            document.getElementById('selectedVote').textContent = `Selected: ${player}`;
            document.getElementById('submitVoteBtn').disabled = false;
        }

        function submitVote() {
            if (!gameState.selectedVote) return;
            
            const gameData = getGameData();
            
            // Store vote in game data
            gameData.votes[`${gameData.currentVoteIndex}_${gameState.playerName}`] = gameState.selectedVote;
            gameState.hasVoted = true;
            
            setGameData(gameData);
            
            // Update UI to show vote was submitted
            document.getElementById('selectedVote').textContent = `You voted for: ${gameState.selectedVote}`;
            document.getElementById('submitVoteBtn').textContent = 'Vote Submitted ✓';
            document.getElementById('submitVoteBtn').disabled = true;
            
            // Let the host check for progression in the next update cycle
            // This gives time for all localStorage updates to propagate
        }

        function checkVoteProgression(gameData) {
            if (!gameState.isHost || gameData.phase !== 'voting') return;
            
            const votedCount = Object.keys(gameData.votes).filter(key => 
                key.startsWith(`${gameData.currentVoteIndex}_`)
            ).length;
            
            if (votedCount >= gameData.players.length) {
                // All players have voted for this question
                if (gameData.currentVoteIndex < gameData.submissions.length - 1) {
                    // Move to next vote
                    gameData.currentVoteIndex++;
                    setGameData(gameData);
                } else {
                    // All votes done, move to results
                    gameData.phase = 'results';
                    setGameData(gameData);
                }
            }
        }

        function showResults(gameData) {
            // Calculate results for each submission
            const results = gameData.submissions.map((submission, index) => {
                const votesForThis = {};
                gameData.players.forEach(p => votesForThis[p.name] = 0);
                
                Object.entries(gameData.votes).forEach(([key, votedPlayer]) => {
                    if (key.startsWith(`${index}_`) && votesForThis[votedPlayer] !== undefined) {
                        votesForThis[votedPlayer]++;
                    }
                });
                
                const sortedVotes = Object.entries(votesForThis)
                    .sort(([,a], [,b]) => b - a)
                    .filter(([,votes]) => votes > 0);
                
                return {
                    submission,
                    votes: sortedVotes
                };
            });
            
            const resultsHtml = results.map(result => 
                `<div class="results-list">
                    <h4>"${result.submission.prompt}"</h4>
                    <p style="font-style: italic; margin-bottom: 10px; opacity: 0.8;">
                        Submitted by: ${result.submission.submitter}
                    </p>
                    ${result.votes.map(([player, votes], index) => 
                        `<div class="result-item">
                            <span>${index === 0 ? '<span class="crown">👑</span> ' : ''}${player}</span>
                            <span>${votes} vote${votes !== 1 ? 's' : ''}</span>
                        </div>`
                    ).join('')}
                </div>`
            ).join('');
            
            document.getElementById('resultsContent').innerHTML = resultsHtml;
            
            // Show host controls
            const hostControls = document.getElementById('hostResultsControls');
            const playerWaiting = document.getElementById('playerResultsWaiting');
            if (gameState.isHost) {
                hostControls.style.display = 'block';
                playerWaiting.style.display = 'none';
            } else {
                hostControls.style.display = 'none';
                playerWaiting.style.display = 'block';
            }
        }

        function nextRound() {
            const gameData = getGameData();
            gameData.round++;
            gameData.phase = 'submission';
            gameData.submissions = [];
            gameData.votes = {};
            gameData.currentVoteIndex = 0;
            gameData.startTime = Date.now();
            
            // Reset all player states for new round
            gameData.players.forEach(p => {
                p.hasSubmitted = false;
                p.hasVoted = false;
            });
            
            // Reset local game state
            gameState.hasSubmitted = false;
            gameState.hasVoted = false;
            gameState.selectedVote = null;
            
            // Clear any existing timer
            if (gameState.submissionTimer) {
                clearInterval(gameState.submissionTimer);
                gameState.submissionTimer = null;
            }
            
            setGameData(gameData);
        }

        function endGame() {
            if (confirm('Are you sure you want to end the game?')) {
                clearInterval(updateInterval);
                localStorage.removeItem(`mostLikelyGame_${gameState.gameCode}`);
                location.reload();
            }
        }

        function switchPhase(phase) {
            document.querySelectorAll('.join-phase, .lobby-phase, .submission-phase, .voting-phase, .results-phase')
                .forEach(el => el.classList.remove('active'));
            document.querySelector(`.${phase}-phase`).classList.add('active');
        }

        // Allow Enter key for inputs
        document.getElementById('playerName').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') joinGame();
        });

        document.getElementById('submission').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') submitPrompt();
        });

        // Clean up on page unload
        window.addEventListener('beforeunload', function() {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
            if (gameState.submissionTimer) {
                clearInterval(gameState.submissionTimer);
            }
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    run(host='0.0.0.0', port=6969, debug=True)
