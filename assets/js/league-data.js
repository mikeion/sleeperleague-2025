// Sleeper API Configuration
const LEAGUE_ID = '1257482235834028032';
const SEASON = '2025';
const SPORT = 'nfl';

// API Endpoints
const API_BASE = 'https://api.sleeper.app/v1';
const LEAGUE_URL = `${API_BASE}/league/${LEAGUE_ID}`;
const ROSTERS_URL = `${API_BASE}/league/${LEAGUE_ID}/rosters`;
const USERS_URL = `${API_BASE}/league/${LEAGUE_ID}/users`;
const MATCHUPS_URL = (week) => `${API_BASE}/league/${LEAGUE_ID}/matchups/${week}`;
const NFL_STATE_URL = `${API_BASE}/state/nfl`;

// Global data storage
let leagueData = {};
let rostersData = [];
let usersData = [];
let currentWeek = 9;
let playersData = {}; // Cache for player names

// Initialize dashboard
async function initDashboard() {
    try {
        // Fetch NFL state to get current week
        const nflState = await fetchData(NFL_STATE_URL);
        currentWeek = nflState.week;

        // Fetch league data
        leagueData = await fetchData(LEAGUE_URL);

        // Fetch rosters, users, and players in parallel
        [rostersData, usersData, playersData] = await Promise.all([
            fetchData(ROSTERS_URL),
            fetchData(USERS_URL),
            fetchData(`${API_BASE}/players/nfl`)
        ]);

        // Combine roster and user data
        const teamsData = combineTeamData(rostersData, usersData);

        // Determine the last completed week by checking for matchup data
        let lastCompletedWeek = currentWeek;
        for (let week = currentWeek; week >= 1; week--) {
            try {
                const weekMatchups = await fetchData(MATCHUPS_URL(week));
                // Check if matchups have actual scores (week has been played)
                if (weekMatchups && weekMatchups.length > 0 && weekMatchups[0].points !== undefined && weekMatchups[0].points > 0) {
                    lastCompletedWeek = week;
                    break;
                }
            } catch (e) {
                // Week doesn't exist yet, continue
                continue;
            }
        }

        document.getElementById('current-week').textContent = currentWeek;
        document.getElementById('matchup-week').textContent = lastCompletedWeek;

        // Render all sections
        renderStandings(teamsData);
        renderPowerRankings(teamsData);
        await renderWeeklyStats(teamsData, lastCompletedWeek);
        await renderManagerAnalysis(teamsData, lastCompletedWeek);
        await renderWaiverAnalysis(teamsData, lastCompletedWeek);
        await renderCurrentMatchups(lastCompletedWeek);

    } catch (error) {
        console.error('Error initializing dashboard:', error);
    }
}

// Fetch data from API
async function fetchData(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// Combine roster and user data into team objects
function combineTeamData(rosters, users) {
    return rosters.map(roster => {
        const user = users.find(u => u.user_id === roster.owner_id);
        return {
            rosterId: roster.roster_id,
            userId: roster.owner_id,
            username: user?.display_name || user?.username || 'Unknown',
            teamName: user?.metadata?.team_name || user?.display_name || 'Unknown Team',
            wins: roster.settings.wins,
            losses: roster.settings.losses,
            ties: roster.settings.ties || 0,
            pointsFor: roster.settings.fpts + (roster.settings.fpts_decimal / 100),
            pointsAgainst: roster.settings.fpts_against + (roster.settings.fpts_against_decimal / 100),
            players: roster.players || []
        };
    }).sort((a, b) => {
        // Sort by wins, then by points for
        if (b.wins !== a.wins) return b.wins - a.wins;
        return b.pointsFor - a.pointsFor;
    });
}

// Render standings table
function renderStandings(teams) {
    const tbody = document.querySelector('#standings-table tbody');
    tbody.innerHTML = teams.map((team, index) => {
        const record = `${team.wins}-${team.losses}${team.ties > 0 ? `-${team.ties}` : ''}`;
        const differential = (team.pointsFor - team.pointsAgainst).toFixed(2);
        const diffClass = differential > 0 ? 'positive' : 'negative';

        return `
            <tr>
                <td>${index + 1}</td>
                <td><strong>${team.teamName}</strong></td>
                <td>${team.username}</td>
                <td>${record}</td>
                <td>${team.pointsFor.toFixed(2)}</td>
                <td>${team.pointsAgainst.toFixed(2)}</td>
                <td class="${diffClass}">${differential > 0 ? '+' : ''}${differential}</td>
            </tr>
        `;
    }).join('');
}

// Calculate power rankings
function calculatePowerRankings(teams) {
    return teams.map(team => {
        const winPct = team.wins / (team.wins + team.losses + team.ties);
        const avgPF = team.pointsFor / (team.wins + team.losses + team.ties);
        const avgPA = team.pointsAgainst / (team.wins + team.losses + team.ties);

        // Power ranking formula: 40% win%, 35% avg PF, 25% avg PA (inverse)
        const maxAvgPF = Math.max(...teams.map(t => t.pointsFor / (t.wins + t.losses + t.ties)));
        const minAvgPA = Math.min(...teams.map(t => t.pointsAgainst / (t.wins + t.losses + t.ties)));

        const powerScore = (
            (winPct * 0.4) +
            ((avgPF / maxAvgPF) * 0.35) +
            ((minAvgPA / avgPA) * 0.25)
        ) * 100;

        return {
            ...team,
            powerScore: powerScore.toFixed(2)
        };
    }).sort((a, b) => b.powerScore - a.powerScore);
}

// Render power rankings
function renderPowerRankings(teams) {
    const rankedTeams = calculatePowerRankings(teams);

    // Create gradient colors based on rank
    const colors = rankedTeams.map((_, index) => {
        const ratio = index / (rankedTeams.length - 1);
        // Gradient from green (best) to red (worst)
        const r = Math.round(255 * ratio);
        const g = Math.round(200 * (1 - ratio));
        return `rgba(${r}, ${g}, 50, 0.7)`;
    });

    const ctx = document.getElementById('power-rankings-chart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: rankedTeams.map(t => t.teamName),
            datasets: [{
                label: 'Power Score',
                data: rankedTeams.map(t => t.powerScore),
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.7', '1')),
                borderWidth: 2
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Formula: 40% Win Rate + 35% Avg Points + 25% Points Against',
                    font: {
                        size: 11
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Power Score: ${context.parsed.x.toFixed(1)}/100`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Power Score (0-100)'
                    }
                }
            }
        }
    });
}

// Render weekly scoring trends with heatmap and line chart
async function renderWeeklyStats(teams, lastCompletedWeek) {
    // Fetch matchups for all completed weeks
    const weeks = Array.from({length: lastCompletedWeek}, (_, i) => i + 1);
    const allMatchups = await Promise.all(
        weeks.map(week => fetchData(MATCHUPS_URL(week)))
    );

    // Organize scores by team and week
    const teamScores = {};
    teams.forEach(team => {
        teamScores[team.rosterId] = {
            name: team.teamName,
            scores: []
        };
    });

    allMatchups.forEach((weekMatchups, weekIndex) => {
        weekMatchups.forEach(matchup => {
            if (teamScores[matchup.roster_id]) {
                const points = matchup.points || 0;
                teamScores[matchup.roster_id].scores.push(points);
            }
        });
    });

    // Create heatmap
    renderHeatmap(teamScores, weeks);

    // Create interactive line chart
    const ctx = document.getElementById('weekly-chart').getContext('2d');

    // Generate distinct colors for each team
    const colors = generateColors(teams.length);

    const datasets = Object.values(teamScores).map((team, index) => ({
        label: team.name,
        data: team.scores,
        borderColor: colors[index],
        backgroundColor: colors[index] + '20',
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
        hidden: index >= 5 // Hide all but top 5 teams by default
    }));

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: weeks.map(w => `Week ${w}`),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        font: {
                            size: 10
                        }
                    },
                    onClick: function(e, legendItem, legend) {
                        const index = legendItem.datasetIndex;
                        const ci = legend.chart;
                        const meta = ci.getDatasetMeta(index);

                        // Toggle visibility
                        meta.hidden = meta.hidden === null ? !ci.data.datasets[index].hidden : null;
                        ci.update();
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} pts`;
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Click team names in legend to show/hide. First 5 teams shown by default.',
                    font: {
                        size: 11,
                        style: 'italic'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Points'
                    }
                }
            }
        }
    });
}

// Render heatmap visualization
function renderHeatmap(teamScores, weeks) {
    const container = document.getElementById('weekly-heatmap');

    // Get all scores to determine min/max for color scale
    const allScores = Object.values(teamScores).flatMap(team => team.scores);
    const minScore = Math.min(...allScores);
    const maxScore = Math.max(...allScores);

    // Create heatmap HTML
    let html = '<div style="display: inline-block; font-size: 12px;">';
    html += '<table style="border-collapse: collapse; margin: 0 auto;">';

    // Header row
    html += '<tr><th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Team</th>';
    weeks.forEach(week => {
        html += `<th style="padding: 8px; text-align: center; border: 1px solid #ddd; min-width: 60px;">W${week}</th>`;
    });
    html += '<th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Avg</th></tr>';

    // Sort teams by total points
    const sortedTeams = Object.values(teamScores).sort((a, b) => {
        const avgA = a.scores.reduce((sum, s) => sum + s, 0) / a.scores.length;
        const avgB = b.scores.reduce((sum, s) => sum + s, 0) / b.scores.length;
        return avgB - avgA;
    });

    // Data rows
    sortedTeams.forEach(team => {
        html += `<tr><td style="padding: 8px; border: 1px solid #ddd; white-space: nowrap;"><strong>${team.name}</strong></td>`;

        team.scores.forEach(score => {
            // Calculate color based on score (green = high, red = low)
            const ratio = (score - minScore) / (maxScore - minScore);
            const r = Math.round(255 * (1 - ratio));
            const g = Math.round(200 * ratio);
            const bgColor = `rgb(${r}, ${g}, 50)`;
            const textColor = ratio > 0.5 ? '#000' : '#fff';

            html += `<td style="padding: 8px; text-align: center; border: 1px solid #ddd; background-color: ${bgColor}; color: ${textColor}; font-weight: bold;">
                ${score.toFixed(1)}
            </td>`;
        });

        // Average column
        const avg = team.scores.reduce((sum, s) => sum + s, 0) / team.scores.length;
        html += `<td style="padding: 8px; text-align: center; border: 1px solid #ddd; background-color: #f0f0f0; font-weight: bold;">
            ${avg.toFixed(1)}
        </td>`;

        html += '</tr>';
    });

    html += '</table>';

    // Add legend
    html += '<div style="margin-top: 15px; text-align: center;">';
    html += '<div style="display: inline-block; margin: 0 10px;">';
    html += '<span style="display: inline-block; width: 20px; height: 20px; background: rgb(255, 0, 50); vertical-align: middle; border: 1px solid #999;"></span> ';
    html += '<span style="font-size: 11px;">Low Score</span>';
    html += '</div>';
    html += '<div style="display: inline-block; margin: 0 10px;">';
    html += '<span style="display: inline-block; width: 20px; height: 20px; background: rgb(128, 100, 50); vertical-align: middle; border: 1px solid #999;"></span> ';
    html += '<span style="font-size: 11px;">Average</span>';
    html += '</div>';
    html += '<div style="display: inline-block; margin: 0 10px;">';
    html += '<span style="display: inline-block; width: 20px; height: 20px; background: rgb(0, 200, 50); vertical-align: middle; border: 1px solid #999;"></span> ';
    html += '<span style="font-size: 11px;">High Score</span>';
    html += '</div>';
    html += '</div>';

    html += '</div>';
    container.innerHTML = html;
}

// Render manager analysis with weekly data
async function renderManagerAnalysis(teams, lastCompletedWeek) {
    // Fetch all weekly matchup data to calculate detailed stats
    const weeks = Array.from({length: lastCompletedWeek}, (_, i) => i + 1);
    const allMatchups = await Promise.all(
        weeks.map(week => fetchData(MATCHUPS_URL(week)))
    );

    // Calculate weekly stats for each team
    const teamStats = teams.map(team => {
        const weeklyScores = [];
        const benchPoints = [];

        allMatchups.forEach(weekMatchups => {
            const matchup = weekMatchups.find(m => m.roster_id === team.rosterId);
            if (matchup && matchup.points) {
                weeklyScores.push(matchup.points);

                // Note: Bench points calculation would require fetching individual player stats
                // which isn't available in Sleeper's matchup endpoint
                // Keeping this as 0 for now
            }
        });

        const gamesPlayed = weeklyScores.length;
        const avgScore = weeklyScores.reduce((sum, s) => sum + s, 0) / gamesPlayed;
        const highScore = Math.max(...weeklyScores);
        const lowScore = Math.min(...weeklyScores);

        // Calculate standard deviation for consistency
        const variance = weeklyScores.reduce((sum, score) => {
            return sum + Math.pow(score - avgScore, 2);
        }, 0) / gamesPlayed;
        const stdDev = Math.sqrt(variance);

        // Calculate luck index: compare actual wins to expected wins
        // Expected wins = if you played everyone each week, how many would you beat?
        let expectedWins = 0;
        allMatchups.forEach(weekMatchups => {
            const myMatchup = weekMatchups.find(m => m.roster_id === team.rosterId);
            if (myMatchup && myMatchup.points) {
                // Count how many teams this team would have beaten this week
                const beatenTeams = weekMatchups.filter(m =>
                    m.roster_id !== team.rosterId && m.points < myMatchup.points
                ).length;
                expectedWins += beatenTeams / (weekMatchups.length - 1);
            }
        });

        const luckIndex = team.wins - expectedWins;
        const avgBenchPoints = benchPoints.length > 0
            ? benchPoints.reduce((sum, p) => sum + p, 0) / benchPoints.length
            : 0;

        return {
            ...team,
            avgScore,
            highScore,
            lowScore,
            stdDev,
            luckIndex,
            avgBenchPoints,
            gamesPlayed
        };
    });

    // Find leaders
    const bestRecord = teams[0];
    const mostPF = [...teams].sort((a, b) => b.pointsFor - a.pointsFor)[0];
    const highestScore = [...teamStats].sort((a, b) => b.highScore - a.highScore)[0];
    const mostConsistent = [...teamStats].sort((a, b) => a.stdDev - b.stdDev)[0];
    const luckiest = [...teamStats].sort((a, b) => b.luckIndex - a.luckIndex)[0];

    // Update stat cards
    document.getElementById('best-manager').textContent = bestRecord.teamName;
    document.getElementById('most-pf').textContent = mostPF.teamName;
    document.getElementById('highest-score').textContent = `${highestScore.teamName} (${highestScore.highScore.toFixed(1)})`;
    document.getElementById('most-consistent').textContent = mostConsistent.teamName;
    document.getElementById('luckiest').textContent = `${luckiest.teamName} (+${luckiest.luckIndex.toFixed(1)})`;

    // Render detailed table
    const tbody = document.querySelector('#manager-details-table tbody');
    tbody.innerHTML = teamStats
        .sort((a, b) => b.avgScore - a.avgScore) // Sort by avg score
        .map(team => {
            const record = `${team.wins}-${team.losses}${team.ties > 0 ? `-${team.ties}` : ''}`;
            const luckClass = team.luckIndex > 0.5 ? 'style="color: #4CAF50;"' :
                            team.luckIndex < -0.5 ? 'style="color: #f44336;"' : '';

            return `
            <tr>
                <td><strong>${team.teamName}</strong></td>
                <td>${record}</td>
                <td>${team.avgScore.toFixed(2)}</td>
                <td style="color: #4CAF50;">${team.highScore.toFixed(2)}</td>
                <td style="color: #f44336;">${team.lowScore.toFixed(2)}</td>
                <td ${luckClass}>${team.luckIndex > 0 ? '+' : ''}${team.luckIndex.toFixed(1)}</td>
                <td>${team.stdDev.toFixed(1)}</td>
            </tr>
        `;
    }).join('');
}

// Render current week matchups
async function renderCurrentMatchups(week) {
    const matchups = await fetchData(MATCHUPS_URL(week));

    // Group matchups by matchup_id
    const matchupPairs = {};
    matchups.forEach(m => {
        if (!matchupPairs[m.matchup_id]) {
            matchupPairs[m.matchup_id] = [];
        }
        matchupPairs[m.matchup_id].push(m);
    });

    // Create matchup cards
    const container = document.getElementById('matchups-grid');
    let html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">';

    Object.values(matchupPairs).forEach(pair => {
        if (pair.length === 2) {
            const team1 = rostersData.find(r => r.roster_id === pair[0].roster_id);
            const team2 = rostersData.find(r => r.roster_id === pair[1].roster_id);
            const user1 = usersData.find(u => u.user_id === team1.owner_id);
            const user2 = usersData.find(u => u.user_id === team2.owner_id);

            const name1 = user1?.metadata?.team_name || user1?.display_name || 'Team 1';
            const name2 = user2?.metadata?.team_name || user2?.display_name || 'Team 2';
            const points1 = pair[0].points || 0;
            const points2 = pair[1].points || 0;

            html += `
                <div style="border: 1px solid #ccc; padding: 15px; border-radius: 8px;">
                    <div style="margin-bottom: 10px;">
                        <strong>${name1}</strong><br>
                        <span style="font-size: 1.5em; color: ${points1 > points2 ? '#4CAF50' : '#999'};">${points1.toFixed(2)}</span>
                    </div>
                    <div style="text-align: center; margin: 10px 0;">vs</div>
                    <div>
                        <strong>${name2}</strong><br>
                        <span style="font-size: 1.5em; color: ${points2 > points1 ? '#4CAF50' : '#999'};">${points2.toFixed(2)}</span>
                    </div>
                </div>
            `;
        }
    });

    html += '</div>';
    container.innerHTML = html;
}

// Render waiver wire and transaction analysis
async function renderWaiverAnalysis(teams, lastCompletedWeek) {
    try {
        // Fetch all transactions for all weeks
        const weeks = Array.from({length: lastCompletedWeek}, (_, i) => i + 1);
        const allTransactions = await Promise.all(
            weeks.map(week => fetchData(`${API_BASE}/league/${LEAGUE_ID}/transactions/${week}`).catch(() => []))
        );

        // Flatten and process transactions
        const transactions = allTransactions.flat();

        // Track stats per team
        const teamStats = {};
        teams.forEach(team => {
            teamStats[team.rosterId] = {
                teamName: team.teamName,
                username: team.username,
                rosterId: team.rosterId,
                totalSpent: 0,
                remainingFaab: rostersData.find(r => r.roster_id === team.rosterId)?.settings?.waiver_budget_used || 0,
                waiverMoves: 0,
                freeAgentMoves: 0,
                trades: 0
            };
        });

        // Process transactions - deduplicate by transaction ID
        const waiverTransactions = [];
        const tradeTransactions = [];
        const seenTransactions = new Set();

        transactions.forEach(tx => {
            // Skip duplicate transactions
            if (seenTransactions.has(tx.transaction_id)) return;
            seenTransactions.add(tx.transaction_id);

            if (!tx.roster_ids || tx.roster_ids.length === 0) return;

            const rosterId = tx.roster_ids[0];
            if (!teamStats[rosterId]) return;

            if (tx.type === 'waiver') {
                teamStats[rosterId].waiverMoves++;
                // Don't add up bids here - we'll get total from roster settings

                // Get player names
                const addedPlayers = tx.adds ? Object.keys(tx.adds) : [];
                const droppedPlayers = tx.drops ? Object.keys(tx.drops) : [];

                waiverTransactions.push({
                    week: tx.leg || 'N/A',
                    rosterId: rosterId,
                    added: addedPlayers,
                    dropped: droppedPlayers,
                    bid: tx.settings?.waiver_bid || 0,
                    timestamp: tx.created
                });
            } else if (tx.type === 'free_agent') {
                teamStats[rosterId].freeAgentMoves++;
            } else if (tx.type === 'trade') {
                tx.roster_ids.forEach(rid => {
                    if (teamStats[rid]) teamStats[rid].trades++;
                });
                tradeTransactions.push(tx);
            }
        });

        // Get actual remaining FAAB from roster settings
        Object.values(teamStats).forEach(stats => {
            const roster = rostersData.find(r => r.roster_id === stats.rosterId);
            // waiver_budget_used is actually the amount SPENT
            const budgetUsed = roster?.settings?.waiver_budget_used || 0;
            stats.totalSpent = budgetUsed; // Use the actual spent amount from roster
            stats.remainingFaab = 100 - budgetUsed; // $100 starting budget
        });

        // Render FAAB table
        const faabTbody = document.querySelector('#faab-table tbody');
        const sortedBySpending = Object.values(teamStats).sort((a, b) => b.totalSpent - a.totalSpent);
        faabTbody.innerHTML = sortedBySpending.map(team => `
            <tr>
                <td><strong>${team.teamName}</strong></td>
                <td>$${team.totalSpent}</td>
                <td style="color: ${team.remainingFaab < 20 ? '#f44336' : '#4CAF50'};">$${team.remainingFaab}</td>
                <td>${team.waiverMoves}</td>
            </tr>
        `).join('');

        // Render activity table
        const activityTbody = document.querySelector('#activity-table tbody');
        const sortedByActivity = Object.values(teamStats).sort((a, b) =>
            (b.waiverMoves + b.freeAgentMoves) - (a.waiverMoves + a.freeAgentMoves)
        );
        activityTbody.innerHTML = sortedByActivity.map(team => `
            <tr>
                <td><strong>${team.teamName}</strong></td>
                <td>${team.waiverMoves + team.freeAgentMoves}</td>
                <td>${team.trades}</td>
                <td><strong>${team.waiverMoves + team.freeAgentMoves + team.trades}</strong></td>
            </tr>
        `).join('');

        // Render recent waivers (last 15)
        const recentWaivers = waiverTransactions
            .sort((a, b) => b.timestamp - a.timestamp)
            .slice(0, 15);

        const waiversTbody = document.querySelector('#recent-waivers-table tbody');
        if (recentWaivers.length === 0) {
            waiversTbody.innerHTML = '<tr><td colspan="5">No waiver activity yet</td></tr>';
        } else {
            waiversTbody.innerHTML = recentWaivers.map(tx => {
                const team = teamStats[tx.rosterId];

                // Get player names
                const addedNames = tx.added.map(playerId => getPlayerName(playerId)).join(', ');
                const droppedNames = tx.dropped.map(playerId => getPlayerName(playerId)).join(', ');

                return `
                    <tr>
                        <td>${tx.week}</td>
                        <td><strong>${team?.teamName || 'Unknown'}</strong></td>
                        <td style="font-size: 0.9em;">${addedNames || '-'}</td>
                        <td style="font-size: 0.9em;">${droppedNames || '-'}</td>
                        <td style="color: ${tx.bid > 20 ? '#f44336' : '#666'};"><strong>$${tx.bid}</strong></td>
                    </tr>
                `;
            }).join('');
        }

        // Render trades
        const tradesContainer = document.getElementById('trades-container');
        if (tradeTransactions.length === 0) {
            tradesContainer.innerHTML = '<p>No trades completed yet this season</p>';
        } else {
            let tradesHtml = `<p>Total trades this season: <strong>${tradeTransactions.length}</strong></p>`;
            tradesHtml += '<div class="table-wrapper"><table><thead><tr><th>Week</th><th>Teams Involved</th><th>Trade Details</th></tr></thead><tbody>';

            tradeTransactions.slice(0, 10).forEach(trade => {
                const teamNames = trade.roster_ids
                    .map(rid => teamStats[rid]?.teamName || 'Unknown')
                    .join(' ↔ ');

                // Build trade details for each team
                let tradeDetails = '<div style="font-size: 0.9em;">';

                // Debug: log trade structure
                console.log('Trade structure:', trade);

                trade.roster_ids.forEach(rosterId => {
                    const team = teamStats[rosterId];
                    if (!team) return;

                    tradeDetails += `<div style="margin-bottom: 8px;"><strong>${team.teamName}:</strong><br>`;

                    // Check if adds exists and is an object
                    if (trade.adds && typeof trade.adds === 'object') {
                        // adds is structured as { player_id: roster_id }
                        // Find players that were added TO this roster
                        const acquiredPlayerIds = Object.keys(trade.adds).filter(
                            playerId => trade.adds[playerId] === rosterId
                        );

                        if (acquiredPlayerIds.length > 0) {
                            const acquiredNames = acquiredPlayerIds.map(pid => getPlayerName(pid));
                            tradeDetails += `&nbsp;&nbsp;↓ Received: ${acquiredNames.join(', ')}<br>`;
                        }
                    }

                    // Check if drops exists
                    if (trade.drops && typeof trade.drops === 'object') {
                        // drops is structured as { player_id: roster_id }
                        // Find players that were dropped BY this roster
                        const droppedPlayerIds = Object.keys(trade.drops).filter(
                            playerId => trade.drops[playerId] === rosterId
                        );

                        if (droppedPlayerIds.length > 0) {
                            const droppedNames = droppedPlayerIds.map(pid => getPlayerName(pid));
                            tradeDetails += `&nbsp;&nbsp;↑ Gave up: ${droppedNames.join(', ')}<br>`;
                        }
                    }

                    // Get draft picks
                    if (trade.draft_picks && trade.draft_picks.length > 0) {
                        const picksAcquired = trade.draft_picks.filter(pick => pick.owner_id === rosterId && pick.previous_owner_id !== rosterId);
                        const picksGaveUp = trade.draft_picks.filter(pick => pick.previous_owner_id === rosterId && pick.owner_id !== rosterId);

                        if (picksAcquired.length > 0) {
                            const picksList = picksAcquired.map(p => `${p.season} Rd ${p.round}`).join(', ');
                            tradeDetails += `&nbsp;&nbsp;↓ Received: ${picksList}<br>`;
                        }
                        if (picksGaveUp.length > 0) {
                            const picksList = picksGaveUp.map(p => `${p.season} Rd ${p.round}`).join(', ');
                            tradeDetails += `&nbsp;&nbsp;↑ Gave up: ${picksList}<br>`;
                        }
                    }

                    tradeDetails += '</div>';
                });

                tradeDetails += '</div>';

                tradesHtml += `
                    <tr>
                        <td>${trade.leg || 'N/A'}</td>
                        <td><strong>${teamNames}</strong></td>
                        <td>${tradeDetails}</td>
                    </tr>
                `;
            });

            tradesHtml += '</tbody></table></div>';
            tradesContainer.innerHTML = tradesHtml;
        }

    } catch (error) {
        console.error('Error rendering waiver analysis:', error);
    }
}

// Helper function to get player name from ID
function getPlayerName(playerId) {
    if (!playerId || !playersData[playerId]) {
        return 'Unknown Player';
    }
    const player = playersData[playerId];
    const fullName = `${player.first_name || ''} ${player.last_name || ''}`.trim();
    const position = player.position ? ` (${player.position})` : '';
    return fullName + position || 'Unknown Player';
}

// Generate distinct colors for charts
function generateColors(count) {
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384',
        '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'
    ];
    return colors.slice(0, count);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initDashboard);
