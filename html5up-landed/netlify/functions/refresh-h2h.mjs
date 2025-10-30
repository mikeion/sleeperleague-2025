import { getStore } from '@netlify/blobs';

const API_BASE = 'https://api.sleeper.app/v1';
const LEAGUE_ID = '1257482235834028032';

// List of all season league IDs (add new seasons as they come)
const SEASONS = [
    { season: '2022', leagueId: '784850758166863872' },
    { season: '2023', leagueId: '918746033135255552' },
    { season: '2024', leagueId: LEAGUE_ID }
];

async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) return null;
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        return null;
    }
}

async function calculateH2HData() {
    console.log('Starting H2H calculation...');

    const h2hMatrix = {};
    const userNames = {};

    for (const season of SEASONS) {
        try {
            const leagueData = await fetchData(`${API_BASE}/league/${season.leagueId}`);
            const rosters = await fetchData(`${API_BASE}/league/${season.leagueId}/rosters`);
            const users = await fetchData(`${API_BASE}/league/${season.leagueId}/users`);

            if (!leagueData || !rosters || !users) continue;

            // Store user names
            users.forEach(u => {
                userNames[u.user_id] = u.display_name || u.metadata?.team_name || 'Unknown';
            });

            // Fetch matchups for regular season only
            const maxWeek = leagueData.settings.playoff_week_start - 1 || 13;
            for (let week = 1; week <= maxWeek; week++) {
                const matchups = await fetchData(`${API_BASE}/league/${season.leagueId}/matchups/${week}`);
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
            console.error(`Error processing ${season.season}:`, error);
        }
    }

    return { h2hMatrix, userNames, lastUpdated: new Date().toISOString() };
}

// Export as both a regular function and a scheduled function
export const handler = async (event, context) => {
    try {
        console.log('Running H2H refresh at:', new Date().toISOString());

        const h2hData = await calculateH2HData();

        // Store in Netlify Blobs using context
        const store = getStore({
            name: 'fantasy-stats',
            siteID: context.site?.id,
            token: context.token
        });
        await store.set('h2h-data', JSON.stringify(h2hData));

        console.log('H2H data calculated and stored successfully');

        return {
            statusCode: 200,
            body: JSON.stringify({
                message: 'H2H data refreshed successfully',
                timestamp: h2hData.lastUpdated,
                userCount: Object.keys(h2hData.userNames).length
            })
        };
    } catch (error) {
        console.error('Error in function:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message })
        };
    }
};

// Schedule to run every Tuesday at midnight UTC
export const config = {
    schedule: '0 0 * * 2'
};
