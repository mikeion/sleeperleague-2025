// Sleeper API Configuration
let CURRENT_LEAGUE_ID = '1257482235834028032'; // 2025 season
const SPORT = 'nfl';

// API Endpoints - these will be dynamic based on selected season
const API_BASE = 'https://api.sleeper.app/v1';
const NFL_STATE_URL = `${API_BASE}/state/nfl`;

// Dynamic URL builders
const getLeagueUrl = (leagueId) => `${API_BASE}/league/${leagueId}`;
const getRostersUrl = (leagueId) => `${API_BASE}/league/${leagueId}/rosters`;
const getUsersUrl = (leagueId) => `${API_BASE}/league/${leagueId}/users`;
const getMatchupsUrl = (leagueId, week) => `${API_BASE}/league/${leagueId}/matchups/${week}`;
const getTransactionsUrl = (leagueId, week) => `${API_BASE}/league/${leagueId}/transactions/${week}`;

// Global data storage
let leagueData = {};
let rostersData = [];
let usersData = [];
let currentWeek = 9;
let playersData = {}; // Cache for player names
let availableSeasons = []; // Store all available seasons and their league IDs

// Username to real name mapping
const USERNAME_TO_NAME = {
    'rpthorp': 'Ryan',
    'robertwneal2': 'Robert',
    'robbbbbbbb': 'Robb',
    'fishy11': 'Vince',
    'dakodiacbear': 'Dakota',
    'spaceman917': 'Nick',
    'sambam805': 'Sam',
    'mikeion': 'Mike',
    'caseyforeverunclean': 'Casey',
    'gordonulus': 'Gordon',
    'captainbigcup': 'Colin',
    'bigdog11': 'Daniel',
    'otterboi': 'Josh',
    'buddygalletti': 'Buddy',
    'elliottkaser': 'Elliott',
    'not_in_league_chris': 'Chris',
    'not_in_league_archie': 'Archie',
    'not_in_league_shane': 'Shane',
    'not_in_league_lorna': 'Lorna',
    'not_in_league_matt': 'Matt',
    'not_in_league_ben': 'Ben',
    'not_in_league': 'Trevor'
};

// Helper function to get display name for a manager
function getDisplayName(manager) {
    if (!manager) return 'Unknown';
    // Try username mapping first
    if (manager.userId && USERNAME_TO_NAME[manager.userId]) {
        return USERNAME_TO_NAME[manager.userId];
    }
    if (manager.username && USERNAME_TO_NAME[manager.username]) {
        return USERNAME_TO_NAME[manager.username];
    }
    // Fallback to the name from data
    return manager.name || 'Unknown';
}

// Load all available seasons for this league
async function loadAvailableSeasons() {
    const seasons = [];
    let currentLeagueId = CURRENT_LEAGUE_ID;
    let currentLeague = await fetchData(getLeagueUrl(currentLeagueId));

    // Start with current season
    seasons.push({
        season: currentLeague.season,
        leagueId: currentLeagueId,
        name: `${currentLeague.season} Season`
    });

    // Walk backwards through previous seasons
    let previousLeagueId = currentLeague.previous_league_id;
    while (previousLeagueId) {
        try {
            const prevLeague = await fetchData(getLeagueUrl(previousLeagueId));
            seasons.push({
                season: prevLeague.season,
                leagueId: previousLeagueId,
                name: `${prevLeague.season} Season`
            });
            previousLeagueId = prevLeague.previous_league_id;
        } catch (e) {
            break; // No more previous seasons
        }
    }

    return seasons;
}

// Populate season selector dropdown
function populateSeasonSelector(seasons) {
    const select = document.getElementById('season-select');
    if (!select) return; // Season selector doesn't exist on all pages

    select.innerHTML = seasons.map((s, index) =>
        `<option value="${s.leagueId}" ${index === 0 ? 'selected' : ''}>${s.name}</option>`
    ).join('');

    // Add change listener
    select.addEventListener('change', async (e) => {
        CURRENT_LEAGUE_ID = e.target.value;
        await loadDashboardData();
    });
}

// Initialize dashboard
async function initDashboard() {
    try {
        // Load all available seasons first
        availableSeasons = await loadAvailableSeasons();
        populateSeasonSelector(availableSeasons);

        // Load data for current season
        await loadDashboardData();

    } catch (error) {
        console.error('Error initializing dashboard:', error);
    }
}

// Load dashboard data for selected season
async function loadDashboardData() {
    try {
        // Fetch NFL state to get current week
        const nflState = await fetchData(NFL_STATE_URL);
        currentWeek = nflState.week;

        // Fetch league data for selected season
        leagueData = await fetchData(getLeagueUrl(CURRENT_LEAGUE_ID));

        // Update season title if it exists
        const seasonTitle = document.getElementById('season-title');
        if (seasonTitle) {
            seasonTitle.textContent = `${leagueData.season} Season`;
        }

        // Check if this is current season or historical
        const isCurrentSeason = leagueData.season === nflState.season;

        // Fetch rosters, users, and players in parallel
        [rostersData, usersData, playersData] = await Promise.all([
            fetchData(getRostersUrl(CURRENT_LEAGUE_ID)),
            fetchData(getUsersUrl(CURRENT_LEAGUE_ID)),
            playersData && Object.keys(playersData).length > 0
                ? Promise.resolve(playersData) // Use cached players
                : fetchData(`${API_BASE}/players/nfl`)
        ]);

        // Combine roster and user data
        const teamsData = combineTeamData(rostersData, usersData);

        // Determine the last completed week by checking for matchup data
        // For historical seasons, check up to week 18, for current season use current week
        const maxWeek = isCurrentSeason ? currentWeek : 18;
        let lastCompletedWeek = maxWeek;

        for (let week = maxWeek; week >= 1; week--) {
            try {
                const weekMatchups = await fetchData(getMatchupsUrl(CURRENT_LEAGUE_ID, week));
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

        // Update week display based on whether this is current season or historical (only if elements exist)
        const currentWeekEl = document.getElementById('current-week');
        if (currentWeekEl) {
            if (isCurrentSeason) {
                currentWeekEl.textContent = `Week ${currentWeek}`;
            } else {
                // For historical seasons, show the season year and completed status
                currentWeekEl.textContent = `${leagueData.season} Season (${lastCompletedWeek} weeks)`;
            }
        }

        const matchupWeekEl = document.getElementById('matchup-week');
        if (matchupWeekEl) {
            matchupWeekEl.textContent = lastCompletedWeek;
        }

        // Update tab visibility (show/hide Weekly Recap based on current season)
        updateTabVisibility(isCurrentSeason);

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
            teamName: user?.display_name || user?.metadata?.team_name || 'Unknown Team',
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
    if (!tbody) return; // Skip if standings table doesn't exist on this page
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

// Store chart instance to destroy on reload
let powerRankingsChart = null;

// Render power rankings
function renderPowerRankings(teams) {
    const canvas = document.getElementById('power-rankings-chart');
    if (!canvas) return; // Skip if chart doesn't exist on this page

    const rankedTeams = calculatePowerRankings(teams);

    // Create gradient colors based on rank
    const colors = rankedTeams.map((_, index) => {
        const ratio = index / (rankedTeams.length - 1);
        // Gradient from green (best) to red (worst)
        const r = Math.round(255 * ratio);
        const g = Math.round(200 * (1 - ratio));
        return `rgba(${r}, ${g}, 50, 0.7)`;
    });

    const ctx = canvas.getContext('2d');

    // Destroy existing chart if it exists
    if (powerRankingsChart) {
        powerRankingsChart.destroy();
    }

    powerRankingsChart = new Chart(ctx, {
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

// Store chart instance to destroy on reload
let weeklyChart = null;

// Render weekly scoring trends with heatmap and line chart
async function renderWeeklyStats(teams, lastCompletedWeek) {
    // Fetch matchups for all completed weeks
    const weeks = Array.from({length: lastCompletedWeek}, (_, i) => i + 1);
    const allMatchups = await Promise.all(
        weeks.map(week => fetchData(getMatchupsUrl(CURRENT_LEAGUE_ID, week)))
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
    const canvas = document.getElementById('weekly-chart');
    if (!canvas) return; // Skip if chart doesn't exist on this page
    const ctx = canvas.getContext('2d');

    // Destroy existing chart if it exists
    if (weeklyChart) {
        weeklyChart.destroy();
    }

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

    weeklyChart = new Chart(ctx, {
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
    if (!container) return; // Skip if heatmap doesn't exist on this page

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
        html += `<td style="padding: 8px; text-align: center; border: 1px solid #ddd; background-color: #e0e0e0; font-weight: bold; color: #333;">
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
        weeks.map(week => fetchData(getMatchupsUrl(CURRENT_LEAGUE_ID, week)))
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

    // Update stat cards (only if they exist on this page)
    const bestManagerEl = document.getElementById('best-manager');
    const mostPFEl = document.getElementById('most-pf');
    const highestScoreEl = document.getElementById('highest-score');
    const mostConsistentEl = document.getElementById('most-consistent');
    const luckiestEl = document.getElementById('luckiest');

    if (bestManagerEl) bestManagerEl.textContent = bestRecord.teamName;
    if (mostPFEl) mostPFEl.textContent = mostPF.teamName;
    if (highestScoreEl) highestScoreEl.textContent = `${highestScore.teamName} (${highestScore.highScore.toFixed(1)})`;
    if (mostConsistentEl) mostConsistentEl.textContent = mostConsistent.teamName;
    if (luckiestEl) luckiestEl.textContent = `${luckiest.teamName} (+${luckiest.luckIndex.toFixed(1)})`;

    // Render detailed table
    const tbody = document.querySelector('#manager-details-table tbody');
    if (!tbody) return; // Skip if table doesn't exist on this page
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
    const matchups = await fetchData(getMatchupsUrl(CURRENT_LEAGUE_ID, week));

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
    if (!container) return; // Skip if matchups grid doesn't exist on this page
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
        // Fetch ALL transactions by fetching each week
        const weeks = Array.from({length: lastCompletedWeek}, (_, i) => i + 1);
        const allTransactions = await Promise.all(
            weeks.map(week => fetchData(getTransactionsUrl(CURRENT_LEAGUE_ID, week)).catch(() => []))
        );
        const transactions = allTransactions.flat();

        console.log('Total raw transactions:', transactions.length);
        console.log('Sample transaction:', transactions[0]);

        // Track stats per team
        const teamStats = {};
        teams.forEach(team => {
            teamStats[team.rosterId] = {
                teamName: team.teamName,
                username: team.username,
                rosterId: team.rosterId,
                totalSpent: 0,
                remainingFaab: rostersData.find(r => r.roster_id === team.rosterId)?.settings?.waiver_budget_used || 0,
                waiverPickups: 0,      // Number of players added via waivers
                waiverClaims: 0,       // Number of waiver transactions
                freeAgentMoves: 0,
                trades: 0
            };
        });

        console.log('Team stats mapping:', teamStats);

        // Process transactions - deduplicate by transaction ID
        const waiverTransactions = [];
        const tradeTransactions = [];
        const seenTransactions = new Set();

        transactions.forEach(tx => {
            // Skip duplicate transactions
            if (seenTransactions.has(tx.transaction_id)) {
                return;
            }
            seenTransactions.add(tx.transaction_id);

            if (!tx.roster_ids || tx.roster_ids.length === 0) return;

            const rosterId = tx.roster_ids[0];
            if (!teamStats[rosterId]) {
                console.log('Roster ID not found in teamStats:', rosterId, 'Transaction:', tx);
                return;
            }

            if (tx.type === 'waiver') {
                // Count both claims (transactions) and pickups (players added)
                const addedPlayers = tx.adds ? Object.keys(tx.adds) : [];
                const droppedPlayers = tx.drops ? Object.keys(tx.drops) : [];

                if (addedPlayers.length > 0) {
                    // Count the claim (1 per transaction)
                    teamStats[rosterId].waiverClaims++;
                    // Count the pickups (number of players added)
                    teamStats[rosterId].waiverPickups += addedPlayers.length;

                    waiverTransactions.push({
                        week: tx.leg || 'N/A',
                        rosterId: rosterId,
                        added: addedPlayers,
                        dropped: droppedPlayers,
                        bid: tx.settings?.waiver_bid || 0,
                        timestamp: tx.created
                    });
                }
            } else if (tx.type === 'free_agent') {
                // Count actual players added (not just number of transactions)
                const addedPlayers = tx.adds ? Object.keys(tx.adds) : [];
                if (addedPlayers.length > 0) {
                    // Add the number of players added, not just 1
                    teamStats[rosterId].freeAgentMoves += addedPlayers.length;
                }
            } else if (tx.type === 'trade') {
                // For trades, count players received by each team
                tx.roster_ids.forEach(rid => {
                    if (teamStats[rid]) {
                        // Count how many players this roster received in the trade
                        const playersReceived = tx.adds ? Object.entries(tx.adds).filter(([playerId, receivingRosterId]) => receivingRosterId === rid).length : 0;
                        teamStats[rid].trades += playersReceived;
                    }
                });
                tradeTransactions.push(tx);
            }
        });

        console.log('After processing - unique transactions:', seenTransactions.size);
        console.log('Final team stats:', teamStats);

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
        if (!faabTbody) return; // Skip if table doesn't exist on this page
        const sortedBySpending = Object.values(teamStats).sort((a, b) => b.totalSpent - a.totalSpent);
        faabTbody.innerHTML = sortedBySpending.map(team => `
            <tr>
                <td><strong>${team.teamName}</strong></td>
                <td>$${team.totalSpent}</td>
                <td style="color: ${team.remainingFaab < 20 ? '#f44336' : '#4CAF50'};">$${team.remainingFaab}</td>
                <td>${team.waiverClaims}</td>
                <td>${team.waiverPickups}</td>
            </tr>
        `).join('');

        // Render activity table
        const activityTbody = document.querySelector('#activity-table tbody');
        if (!activityTbody) return; // Skip if table doesn't exist on this page
        const sortedByActivity = Object.values(teamStats).sort((a, b) =>
            (b.waiverPickups + b.freeAgentMoves) - (a.waiverPickups + a.freeAgentMoves)
        );
        activityTbody.innerHTML = sortedByActivity.map(team => `
            <tr>
                <td><strong>${team.teamName}</strong></td>
                <td>${team.waiverPickups}</td>
                <td>${team.freeAgentMoves}</td>
                <td>${team.trades}</td>
                <td><strong>${team.waiverPickups + team.freeAgentMoves + team.trades}</strong></td>
            </tr>
        `).join('');

        // Render recent waivers (last 15)
        const recentWaivers = waiverTransactions
            .sort((a, b) => b.timestamp - a.timestamp)
            .slice(0, 15);

        const waiversTbody = document.querySelector('#recent-waivers-table tbody');
        if (!waiversTbody) return; // Skip if table doesn't exist on this page
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

// Tab switching functionality
function setupViewTabs() {
    const tabs = document.querySelectorAll('.view-tab');
    const views = document.querySelectorAll('.view-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            tabs.forEach(t => {
                t.classList.remove('active');
                t.style.background = 'transparent';
                t.style.border = '2px solid rgba(255,255,255,0.3)';
                t.style.boxShadow = 'none';
            });

            // Hide all views
            views.forEach(v => v.style.display = 'none');

            // Activate clicked tab
            tab.classList.add('active');
            tab.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            tab.style.border = '2px solid transparent';
            tab.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';

            // Show corresponding view
            const viewId = tab.id.replace('tab-', 'view-');
            const view = document.getElementById(viewId);
            if (view) {
                view.style.display = 'block';

                // Load data if needed
                if (viewId === 'view-alltime' && !view.dataset.loaded) {
                    renderAllTimeStats();
                    view.dataset.loaded = 'true';
                } else if (viewId === 'view-weekly' && !view.dataset.loaded) {
                    renderWeeklyRecap();
                    view.dataset.loaded = 'true';
                }
            }
        });
    });
}

// Show/hide Weekly Recap tab based on current season
function updateTabVisibility(isCurrentSeason) {
    const weeklyTab = document.getElementById('tab-weekly');
    if (!weeklyTab) return; // Element doesn't exist on this page

    if (isCurrentSeason) {
        weeklyTab.style.display = 'inline-block';
    } else {
        weeklyTab.style.display = 'none';
        // If weekly tab is active, switch to season view
        if (weeklyTab.classList.contains('active')) {
            const seasonTab = document.getElementById('tab-season');
            if (seasonTab) seasonTab.click();
        }
    }
}

// Fetch head-to-head data from Netlify function with fallback to local calculation
async function getHeadToHeadData(seasons) {
    try {
        // Try to fetch from Netlify function first
        console.log('Fetching H2H data from server...');
        const response = await fetch('/api/h2h');

        if (response.ok) {
            const data = await response.json();
            console.log('Using server-calculated H2H data from:', data.lastUpdated);
            return data;
        } else {
            console.log('Server data not available, falling back to local calculation');
        }
    } catch (error) {
        console.log('Error fetching server data, falling back to local calculation:', error);
    }

    // Fallback: Calculate locally with localStorage caching
    const CACHE_KEY = 'h2h_data';
    const CACHE_DURATION = 7 * 24 * 60 * 60 * 1000; // 7 days in milliseconds

    // Check cache
    const cached = localStorage.getItem(CACHE_KEY);
    if (cached) {
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < CACHE_DURATION) {
            console.log('Using cached H2H data');
            return data;
        }
    }

    console.log('Calculating H2H data locally (this may take a moment)...');

    // Build H2H matrix: { userId1: { userId2: { wins: 0, losses: 0 } } }
    const h2hMatrix = {};
    const userNames = {}; // Map userId to display name

    // Fetch all matchups for all seasons
    for (const season of seasons) {
        try {
            const leagueData = await fetchData(getLeagueUrl(season.leagueId));
            const rosters = await fetchData(getRostersUrl(season.leagueId));
            const users = await fetchData(getUsersUrl(season.leagueId));

            // Store user names
            users.forEach(u => {
                userNames[u.user_id] = u.display_name || u.metadata?.team_name || 'Unknown';
            });

            // Fetch matchups for regular season only
            const maxWeek = leagueData.settings.playoff_week_start - 1 || 13;
            for (let week = 1; week <= maxWeek; week++) {
                const matchups = await fetchData(getMatchupsUrl(season.leagueId, week));
                if (!matchups) continue;

                // Group by matchup_id
                const matchupPairs = {};
                matchups.forEach(m => {
                    if (!matchupPairs[m.matchup_id]) matchupPairs[m.matchup_id] = [];
                    matchupPairs[m.matchup_id].push(m);
                });

                // Process each matchup
                Object.values(matchupPairs).forEach(pair => {
                    if (pair.length !== 2) return;

                    const [m1, m2] = pair;
                    const roster1 = rosters.find(r => r.roster_id === m1.roster_id);
                    const roster2 = rosters.find(r => r.roster_id === m2.roster_id);

                    if (!roster1 || !roster2) return;

                    const user1 = roster1.owner_id;
                    const user2 = roster2.owner_id;

                    // Initialize if needed
                    if (!h2hMatrix[user1]) h2hMatrix[user1] = {};
                    if (!h2hMatrix[user2]) h2hMatrix[user2] = {};
                    if (!h2hMatrix[user1][user2]) h2hMatrix[user1][user2] = { wins: 0, losses: 0 };
                    if (!h2hMatrix[user2][user1]) h2hMatrix[user2][user1] = { wins: 0, losses: 0 };

                    // Record result
                    if (m1.points > m2.points) {
                        h2hMatrix[user1][user2].wins++;
                        h2hMatrix[user2][user1].losses++;
                    } else if (m2.points > m1.points) {
                        h2hMatrix[user2][user1].wins++;
                        h2hMatrix[user1][user2].losses++;
                    }
                });
            }
        } catch (error) {
            console.error(`Error fetching H2H for ${season.season}:`, error);
        }
    }

    const data = { h2hMatrix, userNames };

    // Cache the results
    localStorage.setItem(CACHE_KEY, JSON.stringify({
        data,
        timestamp: Date.now()
    }));

    console.log('H2H data calculated and cached locally');
    return data;
}

// All-Time Stats - aggregate data across all seasons
async function renderAllTimeStats() {
    const container = document.getElementById('alltime-content');
    container.innerHTML = '<p style="text-align: center;">Loading all-time statistics...</p>';

    try {
        // Load MFL historical data
        let mflData = null;
        try {
            const mflResponse = await fetch('/assets/data/mfl_dashboard_data.json');
            if (mflResponse.ok) {
                mflData = await mflResponse.json();
                console.log('MFL data loaded:', mflData);
            }
        } catch (mflError) {
            console.log('No MFL data available:', mflError);
        }

        // Load Yahoo historical data
        let yahooData = null;
        try {
            const yahooResponse = await fetch('/assets/data/yahoo_dashboard_data.json');
            if (yahooResponse.ok) {
                yahooData = await yahooResponse.json();
                console.log('Yahoo data loaded:', yahooData);
            }
        } catch (yahooError) {
            console.log('No Yahoo data available:', yahooError);
        }

        // Load MFL playoff results
        let mflPlayoffs = null;
        try {
            const mflPlayoffsResponse = await fetch('/assets/data/mfl_playoff_results.json');
            if (mflPlayoffsResponse.ok) {
                mflPlayoffs = await mflPlayoffsResponse.json();
                console.log('MFL playoff results loaded:', mflPlayoffs);
            }
        } catch (mflPlayoffsError) {
            console.log('No MFL playoff results:', mflPlayoffsError);
        }

        // Load Sleeper playoff results
        let sleeperPlayoffs = null;
        try {
            const playoffsResponse = await fetch('/assets/data/sleeper_playoff_results.json');
            if (playoffsResponse.ok) {
                sleeperPlayoffs = await playoffsResponse.json();
                console.log('Sleeper playoff results loaded:', sleeperPlayoffs);
            }
        } catch (playoffsError) {
            console.log('No Sleeper playoff results:', playoffsError);
        }

        // Get all available seasons
        const sleeperSeasons = await loadAvailableSeasons();

        // Create combined seasons array (MFL + Sleeper)
        const seasons = [];

        // Manager stats structure: { userId: { name, seasons: [], championships: 0, etc } }
        const managerStats = {};
        const seasonResults = []; // Track champion/runner-up by year

        // Add MFL data to seasonResults and managerStats
        if (mflData) {
            // Add MFL years to seasons array
            mflData.years.forEach(year => {
                seasons.push({
                    season: year,
                    platform: 'MFL',
                    name: `${year} Season (MFL)`
                });
            });
            // Add MFL champions to season results
            mflData.champions.forEach(champ => {
                // Find playoff data for this year
                const playoffData = mflPlayoffs?.find(p => p.year === champ.year);

                seasonResults.push({
                    season: champ.year,
                    champion: champ.champion.display_name,
                    runnerUp: champ.runner_up.display_name,
                    thirdPlace: playoffData?.third_place || null,
                    sacko: playoffData?.sacko || null,
                    platform: 'MFL'
                });
            });

            // Initialize manager stats from MFL data
            mflData.manager_stats.forEach(mflManager => {
                // Use username as key (will match with Sleeper data)
                const userId = mflManager.username;

                managerStats[userId] = {
                    name: mflManager.display_name,
                    userId: userId,
                    seasons: [],
                    championships: mflManager.totals.championships,
                    runnerUps: 0,
                    sackos: 0,
                    playoffAppearances: 0,
                    totalWins: mflManager.totals.wins,
                    totalLosses: mflManager.totals.losses,
                    totalTies: mflManager.totals.ties,
                    totalPointsFor: mflManager.totals.points_for,
                    totalPointsAgainst: mflManager.totals.points_against,
                    seasonFinishes: [],
                    bestFinish: null,
                    worstFinish: null
                };

                // Add MFL seasons
                Object.entries(mflManager.years).forEach(([year, yearData]) => {
                    managerStats[userId].seasons.push({
                        year: parseInt(year),
                        wins: yearData.wins,
                        losses: yearData.losses,
                        ties: yearData.ties,
                        pointsFor: yearData.points_for,
                        pointsAgainst: yearData.points_against,
                        finish: null,
                        platform: 'MFL'
                    });
                });
            });

            // Track Sackos from MFL playoff results
            if (mflPlayoffs) {
                mflPlayoffs.forEach(playoff => {
                    if (playoff.sacko) {
                        // Find the manager by display name (MFL uses display names)
                        const manager = Object.values(managerStats).find(m => m.name === playoff.sacko);
                        if (manager) {
                            manager.sackos++;
                        }
                    }
                });
            }
        }

        // Add Yahoo data to seasonResults and managerStats
        if (yahooData) {
            // Add Yahoo years to seasons array
            yahooData.years.forEach(year => {
                seasons.push({
                    season: year,
                    platform: 'Yahoo',
                    name: `${year} Season (Yahoo)`
                });
            });
            // Add Yahoo champions to season results
            yahooData.champions.forEach(champ => {
                seasonResults.push({
                    season: champ.year,
                    champion: champ.champion.display_name,
                    runnerUp: champ.runner_up.display_name,
                    platform: 'Yahoo'
                });
            });

            // Initialize manager stats from Yahoo data
            yahooData.manager_stats.forEach(yahooManager => {
                const userId = yahooManager.username;

                // Check if manager already exists (from MFL data)
                if (!managerStats[userId]) {
                    managerStats[userId] = {
                        name: yahooManager.display_name,
                        userId: userId,
                        username: userId,
                        seasons: [],
                        championships: 0,
                        runnerUps: 0,
                        sackos: 0,
                        playoffAppearances: 0,
                        totalWins: 0,
                        totalLosses: 0,
                        totalTies: 0,
                        totalPointsFor: 0,
                        totalPointsAgainst: 0,
                        seasonFinishes: [],
                        bestFinish: null,
                        worstFinish: null
                    };
                }

                // Add to existing stats
                managerStats[userId].championships += yahooManager.totals.championships;
                managerStats[userId].totalWins += yahooManager.totals.wins;
                managerStats[userId].totalLosses += yahooManager.totals.losses;
                managerStats[userId].totalTies += yahooManager.totals.ties;
                managerStats[userId].totalPointsFor += yahooManager.totals.points_for;
                managerStats[userId].totalPointsAgainst += yahooManager.totals.points_against;

                // Add Yahoo seasons
                Object.entries(yahooManager.years).forEach(([year, yearData]) => {
                    managerStats[userId].seasons.push({
                        year: parseInt(year),
                        wins: yearData.wins,
                        losses: yearData.losses,
                        ties: yearData.ties,
                        pointsFor: yearData.points_for,
                        pointsAgainst: yearData.points_against,
                        finish: null,
                        platform: 'Yahoo'
                    });
                });
            });
        }

        // Add Sleeper seasons to combined array
        seasons.push(...sleeperSeasons);

        // Sort seasons by year (oldest to newest)
        seasons.sort((a, b) => a.season - b.season);

        // Fetch Sleeper data for each season
        for (const season of sleeperSeasons) {
            try {
                const leagueData = await fetchData(getLeagueUrl(season.leagueId));
                const rosters = await fetchData(getRostersUrl(season.leagueId));
                const users = await fetchData(getUsersUrl(season.leagueId));

                // Fetch user profiles to get actual usernames (league users don't include username)
                const userProfiles = {};
                for (const user of users) {
                    try {
                        const profile = await fetchData(`${API_BASE}/user/${user.user_id}`);
                        if (profile && profile.username) {
                            userProfiles[user.user_id] = profile.username.toLowerCase();
                        }
                    } catch (e) {
                        console.log(`Could not fetch profile for user ${user.user_id}`);
                    }
                }

                // Process each manager
                for (const roster of rosters) {
                    const user = users.find(u => u.user_id === roster.owner_id);
                    if (!user) continue;

                    // Use username from profile, fallback to user_id if not available
                    // Normalize to lowercase for case-insensitive matching
                    const username = userProfiles[user.user_id] || user.user_id.toString().toLowerCase();
                    const displayName = user.display_name || user.metadata?.team_name || 'Unknown';

                    // Check if this user already has MFL data
                    let existingManager = managerStats[username];

                    // Initialize manager if not exists
                    if (!existingManager) {
                        managerStats[username] = {
                            name: displayName,
                            userId: username,
                            username: username,
                            seasons: [],
                            championships: 0,
                            runnerUps: 0,
                            sackos: 0,
                            playoffAppearances: 0,
                            totalWins: 0,
                            totalLosses: 0,
                            totalTies: 0,
                            totalPointsFor: 0,
                            totalPointsAgainst: 0,
                            seasonFinishes: [],
                            bestFinish: null,
                            worstFinish: null
                        };
                        existingManager = managerStats[username];
                    }

                    // Update display name if Sleeper has a better one
                    if (displayName && displayName !== 'Unknown') {
                        existingManager.name = displayName;
                    }

                    // Get season stats from roster settings (includes playoffs)
                    const seasonWins = roster.settings?.wins || 0;
                    const seasonLosses = roster.settings?.losses || 0;
                    const seasonTies = roster.settings?.ties || 0;
                    const seasonPointsFor = roster.settings?.fpts || 0;
                    const seasonPointsAgainst = roster.settings?.fpts_against || 0;

                    // Store season data
                    existingManager.seasons.push({
                        year: season.season,
                        wins: seasonWins,
                        losses: seasonLosses,
                        ties: seasonTies,
                        pointsFor: seasonPointsFor,
                        pointsAgainst: seasonPointsAgainst,
                        finish: null,
                        platform: 'Sleeper'
                    });

                    existingManager.totalWins += seasonWins;
                    existingManager.totalLosses += seasonLosses;
                    existingManager.totalTies += seasonTies;
                    existingManager.totalPointsFor += seasonPointsFor;
                    existingManager.totalPointsAgainst += seasonPointsAgainst;
                }

                // Use pre-extracted playoff results
                if (sleeperPlayoffs) {
                    // Convert season to number for comparison (Sleeper API returns season as string)
                    const seasonYear = parseInt(season.season);
                    const yearPlayoffs = sleeperPlayoffs.find(p => p.year === seasonYear);
                    if (yearPlayoffs) {
                        let championName = null;
                        let runnerUpName = null;

                        // Track champion
                        if (yearPlayoffs.champion) {
                            if (managerStats[yearPlayoffs.champion]) {
                                managerStats[yearPlayoffs.champion].championships++;
                                championName = getDisplayName(managerStats[yearPlayoffs.champion]);
                            } else {
                                // Manager not in managerStats yet, use username as fallback
                                championName = yearPlayoffs.champion;
                            }
                        }

                        // Track runner-up
                        if (yearPlayoffs.runner_up) {
                            if (managerStats[yearPlayoffs.runner_up]) {
                                managerStats[yearPlayoffs.runner_up].runnerUps++;
                                runnerUpName = getDisplayName(managerStats[yearPlayoffs.runner_up]);
                            } else {
                                // Manager not in managerStats yet, use username as fallback
                                runnerUpName = yearPlayoffs.runner_up;
                            }
                        }

                        // Track third place
                        let thirdPlaceName = null;
                        if (yearPlayoffs.third_place) {
                            if (managerStats[yearPlayoffs.third_place]) {
                                thirdPlaceName = getDisplayName(managerStats[yearPlayoffs.third_place]);
                            } else {
                                // Manager not in managerStats yet, use username as fallback
                                thirdPlaceName = yearPlayoffs.third_place;
                            }
                        }

                        // Track Sacko
                        let sackoName = null;
                        if (yearPlayoffs.sacko) {
                            if (managerStats[yearPlayoffs.sacko]) {
                                managerStats[yearPlayoffs.sacko].sackos++;
                                sackoName = getDisplayName(managerStats[yearPlayoffs.sacko]);
                            } else {
                                // Manager not in managerStats yet, use username as fallback
                                sackoName = yearPlayoffs.sacko;
                            }
                        }

                        // Store in seasonResults for League History display
                        seasonResults.push({
                            season: season.season,
                            champion: championName,
                            runnerUp: runnerUpName,
                            thirdPlace: thirdPlaceName,
                            sacko: sackoName
                        });
                    }
                }

            } catch (error) {
                console.error(`Error fetching data for ${season.season}:`, error);
            }
        }

        // Filter to managers with at least 3 seasons
        const qualifiedManagers = Object.values(managerStats).filter(m => m.seasons.length >= 3);

        // Calculate derived stats
        qualifiedManagers.forEach(manager => {
            const numSeasons = manager.seasons.length;
            if (numSeasons > 0) {
                manager.avgPointsPerSeason = manager.totalPointsFor / numSeasons;
                manager.avgPointsPerGame = manager.totalPointsFor / (manager.totalWins + manager.totalLosses + manager.totalTies);
                manager.winPct = (manager.totalWins / (manager.totalWins + manager.totalLosses + manager.totalTies)) * 100;
            }
        });

        // Render the stats
        renderDynastyRankings(qualifiedManagers, seasons, seasonResults);

    } catch (error) {
        console.error('Error rendering all-time stats:', error);
        container.innerHTML = '<p>Error loading all-time statistics. Please try again.</p>';
    }
}

// Dynasty Rankings Section
function renderDynastyRankings(managerStats, seasons, seasonResults) {
    const container = document.getElementById('alltime-content');
    const managers = Object.values(managerStats);

    // Calculate additional stats for records section
    const allTimeHighScore = Math.max(...managers.flatMap(m => m.seasons.map(s => s.pointsFor / (s.wins + s.losses + s.ties))));
    const highScorer = managers.find(m => m.seasons.some(s => s.pointsFor / (s.wins + s.losses + s.ties) === allTimeHighScore));

    let html = `
        <div style="max-width: 1400px; margin: 0 auto;">
            <p style="text-align: center; color: #666; margin-bottom: 40px;">
                Career stats across ${seasons.length} season${seasons.length > 1 ? 's' : ''}
                (${seasons[0].season} - ${seasons[seasons.length - 1].season})
            </p>

            <!-- Dynasty Rankings -->
            <div style="margin-bottom: 60px;">
                <h3 style="text-align: center; margin-bottom: 20px;">🏆 Dynasty Rankings</h3>
                <p style="text-align: center; color: #666; font-size: 0.9em; margin-bottom: 10px;">
                    Managers with at least 3 seasons (click column headers to sort)
                </p>
                <p style="text-align: center; margin-bottom: 20px;">
                    <strong>Sort by:</strong>
                    <button onclick="sortDynastyTable('championships')" class="button small">Championships</button>
                    <button onclick="sortDynastyTable('winPct')" class="button small">Win %</button>
                    <button onclick="sortDynastyTable('avgPts')" class="button small">Avg PPG</button>
                </p>

                <div class="table-wrapper">
                    <table id="dynasty-rankings-table">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Manager</th>
                                <th style="cursor: pointer;" onclick="sortDynastyTable('championships')" id="sort-champs">Championships</th>
                                <th style="cursor: pointer;" onclick="sortDynastyTable('sackos')" id="sort-sackos">Sackos</th>
                                <th style="cursor: pointer;" onclick="sortDynastyTable('winPct')" id="sort-winpct">Win %</th>
                                <th>Record</th>
                                <th style="cursor: pointer;" onclick="sortDynastyTable('avgPts')" id="sort-avgpts">Avg PPG</th>
                                <th>Seasons</th>
                            </tr>
                        </thead>
                        <tbody id="dynasty-rankings-tbody">
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- League History Timeline -->
            <div style="margin-bottom: 60px;">
                <h3 style="text-align: center; margin-bottom: 20px;">📅 League History</h3>
                <p style="text-align: center; color: #666; font-size: 0.9em; margin-bottom: 20px;">
                    Championship results by year
                </p>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
    `;

    // Show champions by year
    seasons.forEach(season => {
        const result = seasonResults.find(r => r.season === season.season);
        const championName = result?.champion || 'TBD';
        const hasChampion = result && result.champion;

        html += `
            <div style="padding: 20px; background: linear-gradient(135deg, ${hasChampion ? '#FFD700' : '#667eea'} 0%, ${hasChampion ? '#FFA500' : '#764ba2'} 100%); border-radius: 8px; color: white; text-align: center;">
                <div style="font-size: 1.5em; font-weight: bold; margin-bottom: 10px;">${season.season}</div>
                <div style="font-size: 1.1em; opacity: 0.95; margin-bottom: 5px;">${hasChampion ? '🏆 ' : ''}${championName}</div>
                ${result?.runnerUp ? `<div style="font-size: 0.85em; opacity: 0.8; margin-bottom: 5px;">🥈 Runner-up: ${result.runnerUp}</div>` : ''}
                ${result?.thirdPlace ? `<div style="font-size: 0.85em; opacity: 0.8; margin-bottom: 5px;">🥉 3rd: ${result.thirdPlace}</div>` : ''}
                ${result?.sacko ? `<div style="font-size: 0.85em; opacity: 0.8;">💩 Sacko: ${result.sacko}</div>` : ''}
            </div>
        `;
    });

    html += `
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;

    // Store managers data globally for sorting
    window.dynastyManagers = managers;

    // Initial render with win percentage sort
    sortDynastyTable('winPct');
}

// Sort dynasty table by different criteria
function sortDynastyTable(sortBy) {
    if (!window.dynastyManagers) return;

    const managers = [...window.dynastyManagers];

    // Sort based on criteria
    let sortedManagers;
    switch(sortBy) {
        case 'championships':
            sortedManagers = managers.sort((a, b) => {
                if (b.championships !== a.championships) return b.championships - a.championships;
                if (b.winPct !== a.winPct) return b.winPct - a.winPct;
                return b.totalPointsFor - a.totalPointsFor;
            });
            break;
        case 'sackos':
            sortedManagers = managers.sort((a, b) => {
                if (b.sackos !== a.sackos) return b.sackos - a.sackos;
                if (b.winPct !== a.winPct) return a.winPct - b.winPct; // reverse - lower win% is "better" for Sacko
                return a.totalPointsFor - b.totalPointsFor; // reverse - fewer points is "better" for Sacko
            });
            break;
        case 'winPct':
            sortedManagers = managers.sort((a, b) => {
                if (b.winPct !== a.winPct) return b.winPct - a.winPct;
                return b.championships - a.championships;
            });
            break;
        case 'totalPoints':
            sortedManagers = managers.sort((a, b) => b.totalPointsFor - a.totalPointsFor);
            break;
        case 'avgPts':
            sortedManagers = managers.sort((a, b) => b.avgPointsPerGame - a.avgPointsPerGame);
            break;
        default:
            sortedManagers = managers;
    }

    // Update sort indicators in headers
    document.getElementById('sort-champs').innerHTML = 'Championships' + (sortBy === 'championships' ? ' ▼' : '');
    document.getElementById('sort-sackos').innerHTML = 'Sackos' + (sortBy === 'sackos' ? ' ▼' : '');
    document.getElementById('sort-winpct').innerHTML = 'Win %' + (sortBy === 'winPct' ? ' ▼' : '');
    document.getElementById('sort-avgpts').innerHTML = 'Avg PPG' + (sortBy === 'avgPts' ? ' ▼' : '');

    // Update button styles to show active sort
    const buttons = document.querySelectorAll('.view-content button.small');
    buttons.forEach(btn => {
        btn.style.background = '';
        btn.style.borderColor = '';
    });

    // Render table rows
    const tbody = document.getElementById('dynasty-rankings-tbody');
    tbody.innerHTML = sortedManagers.map((manager, index) => {
        const medal = index === 0 ? '👑' : index === 1 ? '🥈' : index === 2 ? '🥉' : '';
        const displayName = getDisplayName(manager);
        const userLink = `user.html?username=${encodeURIComponent(manager.username || manager.userId)}`;
        return `
            <tr>
                <td><strong>${medal} ${index + 1}</strong></td>
                <td><strong><a href="${userLink}" style="color: inherit; text-decoration: none; border-bottom: 1px dotted currentColor;">${displayName}</a></strong></td>
                <td style="font-size: 1.2em; color: ${manager.championships > 0 ? '#FFD700' : 'inherit'};">
                    ${manager.championships > 0 ? '🏆 ' : ''}${manager.championships}
                </td>
                <td style="font-size: 1.2em; color: ${manager.sackos > 0 ? '#8B4513' : 'inherit'};">
                    ${manager.sackos > 0 ? '💩 ' : ''}${manager.sackos}
                </td>
                <td>${manager.winPct.toFixed(1)}%</td>
                <td>${manager.totalWins}-${manager.totalLosses}${manager.totalTies > 0 ? '-' + manager.totalTies : ''}</td>
                <td>${manager.avgPointsPerGame.toFixed(1)}</td>
                <td>${manager.seasons.length}</td>
            </tr>
        `;
    }).join('');
}

// Helper function to generate record cards
function generateRecordCard(title, manager, value, emoji) {
    return `
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 25px; border-radius: 12px; color: white; text-align: center;">
            <div style="font-size: 2.5em; margin-bottom: 10px;">${emoji}</div>
            <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 5px;">${title}</div>
            <div style="font-size: 1.3em; font-weight: bold; margin-bottom: 5px;">${manager}</div>
            <div style="font-size: 1.1em;">${value}</div>
        </div>
    `;
}

// Weekly Recap - show highlights from most recent completed week
async function renderWeeklyRecap(selectedWeek = null) {
    const container = document.getElementById('weekly-content');

    try {
        // Get the most recent completed week
        const nflState = await fetchData(NFL_STATE_URL);
        let recapWeek = selectedWeek || nflState.week;

        // If no week selected, find last completed week with scores
        if (!selectedWeek) {
            for (let week = nflState.week; week >= 1; week--) {
                try {
                    const weekMatchups = await fetchData(getMatchupsUrl(CURRENT_LEAGUE_ID, week));
                    if (weekMatchups && weekMatchups.length > 0 && weekMatchups[0].points > 0) {
                        recapWeek = week;
                        break;
                    }
                } catch (e) {
                    continue;
                }
            }
        }

        // Populate week selector (only once)
        const weekSelect = document.getElementById('week-select');
        if (weekSelect && weekSelect.options.length === 1) {
            weekSelect.innerHTML = '';
            for (let week = 1; week <= nflState.week; week++) {
                const option = document.createElement('option');
                option.value = week;
                option.textContent = `Week ${week}`;
                if (week === recapWeek) option.selected = true;
                weekSelect.appendChild(option);
            }

            // Add change listener
            weekSelect.addEventListener('change', (e) => {
                renderWeeklyRecap(parseInt(e.target.value));
            });
        } else if (weekSelect) {
            // Update selected week
            weekSelect.value = recapWeek;
        }

        // Update subtitle
        const subtitle = document.getElementById('weekly-subtitle');
        if (subtitle) {
            subtitle.textContent = `Week ${recapWeek} highlights`;
        }

        // Fetch matchups for the recap week
        const weekMatchups = await fetchData(getMatchupsUrl(CURRENT_LEAGUE_ID, recapWeek));

        if (!weekMatchups || weekMatchups.length === 0) {
            container.innerHTML = '<p>No matchup data available for this week yet.</p>';
            return;
        }

        // Fetch rosters and users if not already loaded
        if (!rostersData || !usersData || rostersData.length === 0 || usersData.length === 0) {
            rostersData = await fetchData(getRostersUrl(CURRENT_LEAGUE_ID));
            usersData = await fetchData(getUsersUrl(CURRENT_LEAGUE_ID));
        }

        // Get team names using display names (first names)
        const getTeamName = (rosterId) => {
            const roster = rostersData.find(r => r.roster_id === rosterId);
            if (!roster) return 'Unknown Team';
            const user = usersData.find(u => u.user_id === roster.owner_id);
            if (!user) return 'Unknown Team';

            // Use getDisplayName to get first name instead of username
            return getDisplayName({
                username: user.display_name?.toLowerCase() || user.user_id.toString(),
                name: user.display_name
            });
        };

        // Calculate week stats
        const teamScores = weekMatchups.map(m => ({
            rosterId: m.roster_id,
            teamName: getTeamName(m.roster_id),
            points: m.points || 0,
            starters: m.starters || [],
            startersPoints: m.starters_points || []
        }));

        // Find highest and lowest scores
        const sortedByScore = [...teamScores].sort((a, b) => b.points - a.points);
        const highestScore = sortedByScore[0];
        const lowestScore = sortedByScore[sortedByScore.length - 1];

        // Find closest matchup and biggest blowout
        const matchupPairs = {};
        weekMatchups.forEach(m => {
            if (!matchupPairs[m.matchup_id]) matchupPairs[m.matchup_id] = [];
            matchupPairs[m.matchup_id].push(m);
        });

        const completedMatchups = Object.values(matchupPairs)
            .filter(pair => pair.length === 2)
            .map(pair => {
                const team1 = pair[0];
                const team2 = pair[1];
                const diff = Math.abs(team1.points - team2.points);
                return {
                    team1: getTeamName(team1.roster_id),
                    team2: getTeamName(team2.roster_id),
                    score1: team1.points,
                    score2: team2.points,
                    difference: diff
                };
            });

        const closestMatchup = completedMatchups.sort((a, b) => a.difference - b.difference)[0];
        const biggestBlowout = completedMatchups.sort((a, b) => b.difference - a.difference)[0];

        // Build HTML
        let html = `
            <div style="max-width: 1200px; margin: 0 auto;">
                <h2 style="text-align: center; margin-bottom: 10px;">Week ${recapWeek} Recap</h2>
                <p style="text-align: center; color: #666; margin-bottom: 40px;">Highlights from the week that was</p>

                <!-- Top Performers -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 40px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px; color: white; text-align: center;">
                        <h3 style="margin: 0 0 10px 0; font-size: 1.2em;">🏆 Highest Score</h3>
                        <div style="font-size: 2.5em; font-weight: bold; margin: 10px 0;">${highestScore.points.toFixed(2)}</div>
                        <div style="font-size: 1.2em;">${highestScore.teamName}</div>
                    </div>

                    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 30px; border-radius: 12px; color: white; text-align: center;">
                        <h3 style="margin: 0 0 10px 0; font-size: 1.2em;">😬 Lowest Score</h3>
                        <div style="font-size: 2.5em; font-weight: bold; margin: 10px 0;">${lowestScore.points.toFixed(2)}</div>
                        <div style="font-size: 1.2em;">${lowestScore.teamName}</div>
                    </div>

                    <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 30px; border-radius: 12px; color: white; text-align: center;">
                        <h3 style="margin: 0 0 10px 0; font-size: 1.2em;">😰 Closest Game</h3>
                        <div style="font-size: 2em; font-weight: bold; margin: 10px 0;">${closestMatchup.difference.toFixed(2)} pts</div>
                        <div style="font-size: 0.9em;">${closestMatchup.team1} vs ${closestMatchup.team2}</div>
                        <div style="font-size: 0.9em; margin-top: 5px;">${closestMatchup.score1.toFixed(2)} - ${closestMatchup.score2.toFixed(2)}</div>
                    </div>
                </div>

                <!-- All Matchups -->
                <div style="margin-bottom: 40px;">
                    <h3 style="text-align: center; margin-bottom: 20px;">All Matchups</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px;">
        `;

        completedMatchups
            .sort((a, b) => b.difference - a.difference)
            .forEach(matchup => {
                const winner = matchup.score1 > matchup.score2 ? matchup.team1 : matchup.team2;
                const winnerScore = Math.max(matchup.score1, matchup.score2);
                const loserScore = Math.min(matchup.score1, matchup.score2);
                const isBlowout = matchup.difference > 30;

                html += `
                    <div style="border: 2px solid ${isBlowout ? '#f5576c' : '#ddd'}; padding: 20px; border-radius: 8px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <div style="flex: 1;">
                                <div style="font-weight: ${matchup.score1 > matchup.score2 ? 'bold' : 'normal'}; font-size: 1.1em; color: #333;">
                                    ${matchup.team1}
                                </div>
                                <div style="font-size: 1.5em; color: ${matchup.score1 > matchup.score2 ? '#4CAF50' : '#999'}; font-weight: bold;">
                                    ${matchup.score1.toFixed(2)}
                                </div>
                            </div>
                            <div style="font-size: 1.2em; color: #999; padding: 0 15px;">vs</div>
                            <div style="flex: 1; text-align: right;">
                                <div style="font-weight: ${matchup.score2 > matchup.score1 ? 'bold' : 'normal'}; font-size: 1.1em; color: #333;">
                                    ${matchup.team2}
                                </div>
                                <div style="font-size: 1.5em; color: ${matchup.score2 > matchup.score1 ? '#4CAF50' : '#999'}; font-weight: bold;">
                                    ${matchup.score2.toFixed(2)}
                                </div>
                            </div>
                        </div>
                        <div style="text-align: center; font-size: 0.9em; color: #666; margin-top: 10px;">
                            ${isBlowout ? '💥 BLOWOUT - ' : ''}Margin: ${matchup.difference.toFixed(2)} pts
                        </div>
                    </div>
                `;
            });

        html += `
                    </div>
                </div>

                <!-- Scoreboard -->
                <div style="margin-bottom: 40px;">
                    <h3 style="text-align: center; margin-bottom: 20px;">Complete Scoreboard</h3>
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Team</th>
                                    <th>Score</th>
                                </tr>
                            </thead>
                            <tbody>
        `;

        sortedByScore.forEach((team, index) => {
            const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '';
            html += `
                <tr>
                    <td>${medal} ${index + 1}</td>
                    <td><strong>${team.teamName}</strong></td>
                    <td style="font-size: 1.2em; font-weight: bold; color: ${index === 0 ? '#4CAF50' : index === sortedByScore.length - 1 ? '#f44336' : 'inherit'};">
                        ${team.points.toFixed(2)}
                    </td>
                </tr>
            `;
        });

        html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;

    } catch (error) {
        console.error('Error rendering weekly recap:', error);
        container.innerHTML = '<p>Error loading weekly recap. Please try again.</p>';
    }
}

// Initialize homepage with preview data
async function initHomePage() {
    try {
        // Fetch basic league data
        const [leagueData, rostersData, usersData, nflState] = await Promise.all([
            fetchData(getLeagueUrl(CURRENT_LEAGUE_ID)),
            fetchData(getRostersUrl(CURRENT_LEAGUE_ID)),
            fetchData(getUsersUrl(CURRENT_LEAGUE_ID)),
            fetchData(NFL_STATE_URL)
        ]);

        // Update league name in banner
        document.getElementById('league-name').textContent = leagueData.name || 'Fantasy League Dashboard';

        // Get current week
        let currentWeek = nflState.week;
        document.getElementById('current-week-display').textContent = `Week ${currentWeek}`;
        document.getElementById('weekly-subtitle').textContent = `Week ${currentWeek} matchups and highlights`;

        // Create standings preview (top 5)
        const standings = rostersData
            .map(roster => {
                const user = usersData.find(u => u.user_id === roster.owner_id);
                const teamName = user?.metadata?.team_name || user?.display_name || 'Unknown';
                return {
                    teamName,
                    wins: roster.settings?.wins || 0,
                    losses: roster.settings?.losses || 0,
                    ties: roster.settings?.ties || 0,
                    pointsFor: roster.settings?.fpts || 0
                };
            })
            .sort((a, b) => {
                const aWinPct = a.wins / (a.wins + a.losses + a.ties);
                const bWinPct = b.wins / (b.wins + b.losses + b.ties);
                if (bWinPct !== aWinPct) return bWinPct - aWinPct;
                return b.pointsFor - a.pointsFor;
            });

        const standingsHtml = `
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Team</th>
                            <th>Record</th>
                            <th>PF</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${standings.map((team, idx) => `
                            <tr>
                                <td><strong>${idx + 1}</strong></td>
                                <td>${team.teamName}</td>
                                <td>${team.wins}-${team.losses}${team.ties > 0 ? '-' + team.ties : ''}</td>
                                <td>${team.pointsFor.toFixed(1)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        document.getElementById('standings-preview').innerHTML = standingsHtml;

        // Weekly preview - find last completed week
        for (let week = currentWeek; week >= 1; week--) {
            try {
                const weekMatchups = await fetchData(getMatchupsUrl(CURRENT_LEAGUE_ID, week));
                if (weekMatchups && weekMatchups.length > 0 && weekMatchups[0].points > 0) {
                    // Found last completed week
                    const getTeamName = (rosterId) => {
                        const roster = rostersData.find(r => r.roster_id === rosterId);
                        const user = usersData.find(u => u.user_id === roster?.owner_id);
                        return user?.metadata?.team_name || user?.display_name || 'Unknown';
                    };

                    const scores = weekMatchups.map(m => ({ team: getTeamName(m.roster_id), score: m.points }));
                    scores.sort((a, b) => b.score - a.score);

                    const weeklyHtml = `
                        <p style="margin-bottom: 20px;"><strong>Week ${week} Results</strong></p>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                            <div>
                                <p style="font-size: 0.9em; color: #666;">Highest Score</p>
                                <p style="font-size: 1.5em; font-weight: bold; color: #4CAF50;">${scores[0].score.toFixed(2)}</p>
                                <p>${scores[0].team}</p>
                            </div>
                            <div>
                                <p style="font-size: 0.9em; color: #666;">Lowest Score</p>
                                <p style="font-size: 1.5em; font-weight: bold; color: #f44336;">${scores[scores.length - 1].score.toFixed(2)}</p>
                                <p>${scores[scores.length - 1].team}</p>
                            </div>
                        </div>
                    `;
                    document.getElementById('weekly-preview').innerHTML = weeklyHtml;
                    break;
                }
            } catch (e) {
                continue;
            }
        }

        // All-time preview
        const alltimeHtml = `
            <p style="margin-bottom: 15px;">Career statistics spanning multiple seasons</p>
            <ul style="text-align: left; margin: 0 auto; max-width: 400px;">
                <li>Dynasty Rankings</li>
                <li>Championship History</li>
                <li>Career Win-Loss Records</li>
                <li>All-Time Scoring Leaders</li>
            </ul>
        `;
        document.getElementById('alltime-preview').innerHTML = alltimeHtml;

    } catch (error) {
        console.error('Error initializing homepage:', error);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setupViewTabs();
    initDashboard();
});

// User Profile Page
async function renderUserProfile(username) {
    const container = document.getElementById('user-content');
    const nameHeader = document.getElementById('user-name');
    const subtitle = document.getElementById('user-subtitle');
    
    container.innerHTML = '<p style="text-align: center;">Loading user profile...</p>';

    try {
        // Normalize username to lowercase
        const normalizedUsername = username.toLowerCase();

        // Load historical data
        let mflData = null;
        let yahooData = null;

        try {
            const mflResponse = await fetch('/assets/data/mfl_dashboard_data.json');
            if (mflResponse.ok) mflData = await mflResponse.json();
        } catch (e) { console.log('No MFL data'); }

        try {
            const yahooResponse = await fetch('/assets/data/yahoo_dashboard_data.json');
            if (yahooResponse.ok) yahooData = await yahooResponse.json();
        } catch (e) { console.log('No Yahoo data'); }

        // Load Sleeper playoff results
        let sleeperPlayoffs = null;
        try {
            const playoffsResponse = await fetch('/assets/data/sleeper_playoff_results.json');
            if (playoffsResponse.ok) sleeperPlayoffs = await playoffsResponse.json();
        } catch (e) { console.log('No Sleeper playoff data'); }

        // Load Sleeper draft positions
        let sleeperDrafts = null;
        try {
            const draftsResponse = await fetch('/assets/data/sleeper_draft_positions.json');
            if (draftsResponse.ok) sleeperDrafts = await draftsResponse.json();
        } catch (e) { console.log('No Sleeper draft data'); }

        // Get Sleeper data
        const sleeperSeasons = await loadAvailableSeasons();
        
        // Find user data across all platforms
        let userData = {
            username: normalizedUsername,
            displayName: getDisplayName({ username: normalizedUsername }),
            seasons: [],
            totalWins: 0,
            totalLosses: 0,
            totalTies: 0,
            totalPointsFor: 0,
            totalPointsAgainst: 0,
            championships: 0,
            runnerUps: 0,
            sackos: 0,
            playoffAppearances: 0
        };

        // Collect MFL data
        if (mflData && mflData.manager_stats) {
            const mflUser = mflData.manager_stats.find(m => m.username === normalizedUsername);
            if (mflUser) {
                userData.totalWins += mflUser.totals.wins;
                userData.totalLosses += mflUser.totals.losses;
                userData.totalTies += mflUser.totals.ties;
                userData.totalPointsFor += mflUser.totals.points_for;
                userData.totalPointsAgainst += mflUser.totals.points_against;
                userData.championships += mflUser.totals.championships;

                Object.entries(mflUser.years).forEach(([year, yearData]) => {
                    userData.seasons.push({
                        year: parseInt(year),
                        platform: 'MFL',
                        wins: yearData.wins,
                        losses: yearData.losses,
                        ties: yearData.ties,
                        pointsFor: yearData.points_for,
                        pointsAgainst: yearData.points_against,
                        champion: yearData.champion,
                        runnerUp: yearData.runner_up || false,
                        finish: yearData.finish || null,
                        totalTeams: yearData.total_teams || null,
                        draftPick: yearData.draft_pick || null
                    });
                });
            }
        }

        // Collect Yahoo data
        if (yahooData && yahooData.manager_stats) {
            const yahooUser = yahooData.manager_stats.find(m => m.username === normalizedUsername);
            if (yahooUser) {
                userData.totalWins += yahooUser.totals.wins;
                userData.totalLosses += yahooUser.totals.losses;
                userData.totalTies += yahooUser.totals.ties;
                userData.totalPointsFor += yahooUser.totals.points_for;
                userData.totalPointsAgainst += yahooUser.totals.points_against;
                userData.championships += yahooUser.totals.championships;

                Object.entries(yahooUser.years).forEach(([year, yearData]) => {
                    userData.seasons.push({
                        year: parseInt(year),
                        platform: 'Yahoo',
                        wins: yearData.wins,
                        losses: yearData.losses,
                        ties: yearData.ties,
                        pointsFor: yearData.points_for,
                        pointsAgainst: yearData.points_against,
                        champion: yearData.champion,
                        runnerUp: yearData.runner_up || false,
                        finish: yearData.finish || null,
                        totalTeams: yearData.total_teams || null
                    });
                });
            }
        }

        // Collect Sleeper data
        for (const season of sleeperSeasons) {
            try {
                const rosters = await fetchData(getRostersUrl(season.leagueId));
                const users = await fetchData(getUsersUrl(season.leagueId));

                // Fetch user profiles for usernames
                const userProfiles = {};
                for (const user of users) {
                    try {
                        const profile = await fetchData(`${API_BASE}/user/${user.user_id}`);
                        if (profile && profile.username) {
                            userProfiles[user.user_id] = profile.username.toLowerCase();
                        }
                    } catch (e) {}
                }

                // Calculate standings for this season
                const standings = rosters
                    .map(r => ({
                        owner_id: r.owner_id,
                        wins: r.settings?.wins || 0,
                        losses: r.settings?.losses || 0,
                        ties: r.settings?.ties || 0,
                        fpts: r.settings?.fpts || 0
                    }))
                    .sort((a, b) => {
                        if (b.wins !== a.wins) return b.wins - a.wins;
                        return b.fpts - a.fpts;
                    });

                const totalTeams = rosters.length;

                // Find this user's roster
                const userEntry = Object.entries(userProfiles).find(([userId, uname]) => uname === normalizedUsername);
                if (userEntry) {
                    const [userId, uname] = userEntry;
                    const roster = rosters.find(r => r.owner_id === userId);

                    if (roster) {
                        const wins = roster.settings?.wins || 0;
                        const losses = roster.settings?.losses || 0;
                        const ties = roster.settings?.ties || 0;
                        const pointsFor = roster.settings?.fpts || 0;
                        const pointsAgainst = roster.settings?.fpts_against || 0;

                        // Get team name
                        const user = users.find(u => u.user_id === userId);
                        const teamName = user?.metadata?.team_name || null;

                        // Find placement
                        const finish = standings.findIndex(s => s.owner_id === userId) + 1;

                        // Check playoff results
                        let isChampion = false;
                        let isRunnerUp = false;
                        let isThirdPlace = false;
                        let isFourthPlace = false;
                        let isFifthPlace = false;
                        let isSixthPlace = false;
                        let isSeventhPlace = false;
                        let isEighthPlace = false;
                        let isSacko = false;
                        if (sleeperPlayoffs) {
                            const yearPlayoffs = sleeperPlayoffs.find(p => p.year === season.season);
                            if (yearPlayoffs) {
                                isChampion = yearPlayoffs.champion === normalizedUsername;
                                isRunnerUp = yearPlayoffs.runner_up === normalizedUsername;
                                isThirdPlace = yearPlayoffs.third_place === normalizedUsername;
                                isFourthPlace = yearPlayoffs.fourth_place === normalizedUsername;
                                isFifthPlace = yearPlayoffs.fifth_place === normalizedUsername;
                                isSixthPlace = yearPlayoffs.sixth_place === normalizedUsername;
                                isSeventhPlace = yearPlayoffs.seventh_place === normalizedUsername;
                                isEighthPlace = yearPlayoffs.eighth_place === normalizedUsername;
                                isSacko = yearPlayoffs.sacko === normalizedUsername;
                            }
                        }

                        // Get draft position
                        let draftPick = null;
                        if (sleeperDrafts && sleeperDrafts[season.season]) {
                            const yearDrafts = sleeperDrafts[season.season];
                            if (yearDrafts[normalizedUsername]) {
                                draftPick = yearDrafts[normalizedUsername].pick;
                            }
                        }

                        userData.totalWins += wins;
                        userData.totalLosses += losses;
                        userData.totalTies += ties;
                        userData.totalPointsFor += pointsFor;
                        userData.totalPointsAgainst += pointsAgainst;

                        if (isChampion) {
                            userData.championships++;
                        }
                        if (isRunnerUp) {
                            userData.runnerUps++;
                        }
                        if (isSacko) {
                            userData.sackos++;
                        }

                        userData.seasons.push({
                            year: season.season,
                            platform: 'Sleeper',
                            teamName,
                            wins,
                            losses,
                            ties,
                            pointsFor,
                            pointsAgainst,
                            champion: isChampion,
                            runnerUp: isRunnerUp,
                            thirdPlace: isThirdPlace,
                            fourthPlace: isFourthPlace,
                            fifthPlace: isFifthPlace,
                            sixthPlace: isSixthPlace,
                            seventhPlace: isSeventhPlace,
                            eighthPlace: isEighthPlace,
                            sacko: isSacko,
                            finish,
                            totalTeams,
                            draftPick
                        });
                    }
                }
            } catch (error) {
                console.error(`Error loading Sleeper data for ${season.season}:`, error);
            }
        }

        // Sort seasons by year
        userData.seasons.sort((a, b) => a.year - b.year);

        // Check if user exists
        if (userData.seasons.length === 0) {
            container.innerHTML = `
                <p style="text-align: center; color: #f44336;">
                    User "${username}" not found in league data.
                </p>
                <p style="text-align: center;">
                    <a href="alltime.html">Back to Dynasty Rankings</a>
                </p>
            `;
            return;
        }

        // Update header
        nameHeader.textContent = userData.displayName;
        const totalGames = userData.totalWins + userData.totalLosses + userData.totalTies;
        const winPct = totalGames > 0 ? (userData.totalWins / totalGames * 100).toFixed(1) : '0.0';
        subtitle.textContent = `${userData.totalWins}-${userData.totalLosses}${userData.totalTies > 0 ? '-' + userData.totalTies : ''} (${winPct}%) • ${userData.championships} Championship${userData.championships !== 1 ? 's' : ''}`;

        // Render profile
        renderUserProfileContent(userData);

    } catch (error) {
        console.error('Error rendering user profile:', error);
        container.innerHTML = '<p style="text-align: center; color: #f44336;">Error loading user profile. Please try again.</p>';
    }
}

function renderUserProfileContent(userData) {
    const container = document.getElementById('user-content');

    const totalGames = userData.totalWins + userData.totalLosses + userData.totalTies;
    const winPct = totalGames > 0 ? (userData.totalWins / totalGames * 100).toFixed(1) : '0.0';
    const avgPointsPerGame = totalGames > 0 ? (userData.totalPointsFor / totalGames).toFixed(1) : '0.0';

    let html = `
        <div style="max-width: 1200px; margin: 0 auto;">
            <!-- Back Navigation -->
            <p style="margin-bottom: 30px;">
                <a href="alltime.html">← Back to Dynasty Rankings</a>
            </p>

            <!-- Career Overview Cards -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; color: white; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold;">${userData.seasons.length}</div>
                    <div style="opacity: 0.9;">Seasons</div>
                </div>
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 8px; color: white; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold;">${winPct}%</div>
                    <div style="opacity: 0.9;">Win Percentage</div>
                </div>
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 8px; color: white; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold;">${userData.totalPointsFor.toFixed(0)}</div>
                    <div style="opacity: 0.9;">Total Points</div>
                </div>
                <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 8px; color: white; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold;">${avgPointsPerGame}</div>
                    <div style="opacity: 0.9;">Avg PPG</div>
                </div>
            </div>

            <!-- Performance Chart -->
            <div style="margin-bottom: 40px; background: white; padding: 20px; border-radius: 8px;">
                <h3 style="text-align: center; margin-bottom: 20px;">Performance Over Time</h3>
                <p style="text-align: center; color: #666; font-size: 0.9em; margin-bottom: 15px;">Points per game (normalized across different league formats)</p>
                <canvas id="pointsChart" style="max-height: 400px;"></canvas>
            </div>

            <!-- Year-by-Year Table -->
            <div style="margin-bottom: 40px;">
                <h3 style="text-align: center; margin-bottom: 20px;">Season-by-Season Performance</h3>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Year</th>
                                <th>Platform</th>
                                <th>Team Name</th>
                                <th>Draft</th>
                                <th>Record</th>
                                <th>Win %</th>
                                <th>PPG</th>
                                <th>Points For</th>
                                <th>Points Against</th>
                                <th>Diff</th>
                                <th>Reg. Season</th>
                                <th>Playoffs</th>
                            </tr>
                        </thead>
                        <tbody>
    `;

    userData.seasons.forEach(season => {
        const games = season.wins + season.losses + season.ties;
        const seasonWinPct = games > 0 ? (season.wins / games * 100).toFixed(1) : '0.0';
        const ppg = games > 0 ? (season.pointsFor / games).toFixed(1) : '0.0';
        const diff = season.pointsFor - season.pointsAgainst;
        const diffColor = diff > 0 ? '#4CAF50' : '#f44336';

        const platformBadge = {
            'MFL': '<span style="background: #2196F3; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">MFL</span>',
            'Yahoo': '<span style="background: #6001D2; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">Yahoo</span>',
            'Sleeper': '<span style="background: #00CCCB; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">Sleeper</span>'
        };

        // Regular season finish
        let regularSeasonFinish = '';
        if (season.finish && season.totalTeams) {
            regularSeasonFinish = `${season.finish}/${season.totalTeams}`;
        }

        // Playoff result
        let playoffResult = '';
        if (season.champion) {
            playoffResult = '🏆 1st';
        } else if (season.runnerUp) {
            playoffResult = '🥈 2nd';
        } else if (season.thirdPlace) {
            playoffResult = '🥉 3rd';
        } else if (season.fourthPlace) {
            playoffResult = '4th';
        } else if (season.fifthPlace) {
            playoffResult = '5th';
        } else if (season.sixthPlace) {
            playoffResult = '6th';
        } else if (season.seventhPlace) {
            playoffResult = '7th';
        } else if (season.eighthPlace) {
            playoffResult = '8th';
        } else if (season.sacko) {
            playoffResult = '💩 Sacko';
        } else {
            playoffResult = '-';
        }

        const draftDisplay = season.draftPick ? season.draftPick : '-';
        const teamNameDisplay = season.teamName ? `<em>${season.teamName}</em>` : '-';

        html += `
            <tr>
                <td><strong>${season.year}</strong></td>
                <td>${platformBadge[season.platform]}</td>
                <td>${teamNameDisplay}</td>
                <td>${draftDisplay}</td>
                <td>${season.wins}-${season.losses}${season.ties > 0 ? '-' + season.ties : ''}</td>
                <td>${seasonWinPct}%</td>
                <td>${ppg}</td>
                <td>${season.pointsFor.toFixed(1)}</td>
                <td>${season.pointsAgainst.toFixed(1)}</td>
                <td style="color: ${diffColor};">${diff > 0 ? '+' : ''}${diff.toFixed(1)}</td>
                <td>${regularSeasonFinish}</td>
                <td>${playoffResult}</td>
            </tr>
        `;
    });

    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;

    // Render chart
    renderPointsChart(userData);
}

function renderPointsChart(userData) {
    const ctx = document.getElementById('pointsChart');
    if (!ctx) return;

    const years = userData.seasons.map(s => s.year);
    // Calculate points per game for fair comparison across eras
    const pointsPerGame = userData.seasons.map(s => {
        const games = s.wins + s.losses + s.ties;
        return games > 0 ? s.pointsFor / games : 0;
    });
    const championYears = userData.seasons.filter(s => s.champion).map(s => s.year);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [{
                label: 'Points Per Game',
                data: pointsPerGame,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: years.map(y => championYears.includes(y) ? 8 : 4),
                pointBackgroundColor: years.map(y => championYears.includes(y) ? '#FFD700' : '#667eea'),
                pointBorderColor: years.map(y => championYears.includes(y) ? '#FFA500' : '#667eea'),
                pointBorderWidth: years.map(y => championYears.includes(y) ? 3 : 2)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const year = parseInt(context.label);
                            const seasonData = userData.seasons.find(s => s.year === year);
                            const isChampion = championYears.includes(year);
                            const ppg = context.parsed.y.toFixed(1);
                            const total = seasonData ? seasonData.pointsFor.toFixed(1) : '?';
                            const platform = seasonData ? seasonData.platform : '';
                            return `${ppg} PPG (${total} total)${isChampion ? ' 🏆' : ''} [${platform}]`;
                        }
                    }
                },
                annotation: {
                    annotations: {
                        mflYahoo: {
                            type: 'line',
                            xMin: years.indexOf(2020) - 0.5,
                            xMax: years.indexOf(2020) - 0.5,
                            borderColor: 'rgba(255, 99, 132, 0.5)',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            label: {
                                display: true,
                                content: 'Format Change',
                                position: 'start'
                            }
                        },
                        yahooSleeper: {
                            type: 'line',
                            xMin: years.indexOf(2022) - 0.5,
                            xMax: years.indexOf(2022) - 0.5,
                            borderColor: 'rgba(75, 192, 192, 0.5)',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            label: {
                                display: true,
                                content: 'Yahoo→Sleeper',
                                position: 'start'
                            }
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Points Per Game'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Season'
                    }
                }
            }
        }
    });
}
