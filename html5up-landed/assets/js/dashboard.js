/* Home dashboard.

   Live data (scores, records) comes from the Sleeper API in the browser.
   Predictions come from the weekly snapshots in assets/data/weeks/, written
   by data-extraction/week_report.py every Thursday. A snapshot is never
   rewritten after the week is played, so the scorecard grades what we
   actually said beforehand. */

const API = 'https://api.sleeper.app/v1';
const LEAGUE_ID = '1389689478104231936';
const NAMES = {
	rpthorp: 'Ryan', robertwneal2: 'Robert', robbbbbbbb: 'Robb', fishy11: 'Vince',
	dakodiacbear: 'Dakota', spaceman917: 'Nick', sambam805: 'Sam', mikeion: 'Mike',
	caseyforeverunclean: 'Casey', gordonulus: 'Gordon', captainbigcup: 'Colin',
	bigdog11: 'Daniel', otterboi: 'Josh', buddygalletti: 'Buddy', elliottkaser: 'Elliott'
};
const DEFAULT_AVATAR = 'https://sleepercdn.com/images/v2/icons/player_default.webp';

let league, users, rosters, nflState, latestReport;
let currentWeek = 1;
let selectedWeek = 1;
const snapshotCache = {};
const matchupCache = {};

const fmt1 = (x) => Number(x).toFixed(1);
const pct = (p) => `${Math.round(p * 100)}%`;

async function getJSON(url) {
	const res = await fetch(url);
	if (!res.ok) throw new Error(`${res.status} ${url}`);
	return res.json();
}

async function snapshot(week) {
	if (!(week in snapshotCache)) {
		try {
			snapshotCache[week] = await getJSON(`assets/data/weeks/${league.season}_w${String(week).padStart(2, '0')}.json`);
		} catch (e) {
			snapshotCache[week] = null;
		}
	}
	return snapshotCache[week];
}

async function matchups(week) {
	// Past weeks are final; the current week changes while games are on
	if (!(week in matchupCache) || week >= currentWeek) {
		matchupCache[week] = await getJSON(`${API}/league/${LEAGUE_ID}/matchups/${week}`);
	}
	return matchupCache[week];
}

function teamInfo(rosterId) {
	const roster = rosters.find(r => r.roster_id === rosterId);
	const user = users.find(u => u.user_id === roster?.owner_id) || {};
	const handle = (user.display_name || 'unknown').toLowerCase();
	const s = roster?.settings || {};
	return {
		rosterId,
		username: handle,
		name: NAMES[handle] || user.display_name || 'Unknown',
		team: user.metadata?.team_name || user.display_name || 'Unknown',
		avatar: user.avatar ? `https://sleepercdn.com/avatars/thumbs/${user.avatar}` : DEFAULT_AVATAR,
		wins: s.wins || 0, losses: s.losses || 0, ties: s.ties || 0,
		pf: (s.fpts || 0) + (s.fpts_decimal || 0) / 100,
		pa: (s.fpts_against || 0) + (s.fpts_against_decimal || 0) / 100
	};
}

const record = (t) => `${t.wins}-${t.losses}${t.ties ? '-' + t.ties : ''}`;

async function init() {
	[league, users, rosters, nflState] = await Promise.all([
		getJSON(`${API}/league/${LEAGUE_ID}`),
		getJSON(`${API}/league/${LEAGUE_ID}/users`),
		getJSON(`${API}/league/${LEAGUE_ID}/rosters`),
		getJSON(`${API}/state/nfl`)
	]);
	try { latestReport = await getJSON('assets/data/week_report.json'); } catch (e) { latestReport = null; }

	const inSeason = nflState.season === league.season && nflState.season_type === 'regular';
	currentWeek = inSeason ? Math.max(1, Math.min(nflState.week, 18)) : (league.settings?.playoff_week_start || 15) - 1;
	selectedWeek = currentWeek;

	document.getElementById('league-name').textContent = league.name;
	document.getElementById('league-subtitle').textContent =
		`${league.season} · ${league.total_rosters} teams · half PPR · ${inSeason ? `Week ${currentWeek}` : 'Season complete'}`;

	const select = document.getElementById('week-select');
	select.innerHTML = Array.from({ length: currentWeek }, (_, i) => i + 1)
		.map(w => `<option value="${w}">Week ${w}</option>`).join('');
	select.value = selectedWeek;
	select.addEventListener('change', () => showWeek(parseInt(select.value)));
	document.getElementById('week-prev').addEventListener('click', () => showWeek(selectedWeek - 1));
	document.getElementById('week-next').addEventListener('click', () => showWeek(selectedWeek + 1));

	renderStandings();
	await showWeek(selectedWeek);
	await renderScorecard();
	renderPower();
}

async function showWeek(week) {
	if (week < 1 || week > currentWeek) return;
	selectedWeek = week;
	document.getElementById('week-select').value = week;
	document.getElementById('week-prev').disabled = week === 1;
	document.getElementById('week-next').disabled = week === currentWeek;
	document.getElementById('week-title').textContent = `Week ${week}${week === currentWeek ? '' : ' (final)'}`;

	const [games, snap] = await Promise.all([matchups(week), snapshot(week)]);
	const played = games.some(g => g.points > 0);
	const final = week < currentWeek || (played && league.status === 'complete');
	const note = document.getElementById('week-note');
	if (snap) {
		note.textContent = `Projections locked ${snap.generated.replace('T', ' ')} from each manager's starters. ` +
			(played ? (final ? 'Graded against the final scores.' : 'Scores update live.') : 'Nothing has kicked off yet.');
	} else {
		note.textContent = 'No projection snapshot for this week.';
	}

	const byId = {};
	games.forEach(g => { byId[g.roster_id] = g; });
	const pairs = {};
	games.forEach(g => { (pairs[g.matchup_id] = pairs[g.matchup_id] || []).push(g); });
	const snapBy = {};
	(snap?.managers || []).forEach(m => { snapBy[m.roster_id] = m; });

	const cards = Object.values(pairs).filter(p => p.length === 2).map(([ga, gb]) => {
		const a = teamInfo(ga.roster_id), b = teamInfo(gb.roster_id);
		const sa = snapBy[ga.roster_id], sb = snapBy[gb.roster_id];
		const pa = sa ? sa.win_prob : null;
		const aWon = played && ga.points > gb.points, bWon = played && gb.points > ga.points;
		let verdict = '';
		if (played && pa !== null) {
			const favA = pa >= 0.5;
			const favWon = (favA && aWon) || (!favA && bWon);
			const conf = Math.max(pa, 1 - pa);
			const inA = ga.points >= sa.p10 && ga.points <= sa.p90, inB = gb.points >= sb.p10 && gb.points <= sb.p90;
			verdict = `<div class="verdict ${favWon ? 'hit' : 'miss'}">` +
				(final ? (favWon ? `Favorite won (${pct(conf)}).` : `Upset: the ${pct(conf)} favorite lost.`) : `Favorite ${favWon ? 'leading' : 'trailing'}.`) +
				` Scores ${inA && inB ? 'both inside' : inA || inB ? 'one inside' : 'both outside'} the 80% bands.</div>`;
		}
		const probBar = pa === null ? '' :
			`<div class="prob-bar"><div class="fill" style="width:${Math.round(pa * 100)}%"></div>` +
			`<span class="label left">${pct(pa)}</span><span class="label right">${pct(1 - pa)}</span></div>` +
			`<div class="detail"><span>proj ${fmt1(sa.p50)} · ${fmt1(sa.p10)}–${fmt1(sa.p90)}</span><span>${fmt1(sb.p10)}–${fmt1(sb.p90)} · proj ${fmt1(sb.p50)}</span></div>`;
		const score = played
			? `${fmt1(ga.points)} – ${fmt1(gb.points)}<small>${final ? 'final' : 'live'}</small>`
			: `<small>vs</small>`;
		return `<div class="matchup-card">
			<div class="teams">
				<div class="team ${aWon ? 'winner' : ''}"><img src="${a.avatar}" alt=""><div class="who"><strong>${a.name}</strong><small>${a.team} · ${record(a)}</small></div></div>
				<div class="score">${score}</div>
				<div class="team right ${bWon ? 'winner' : ''}"><img src="${b.avatar}" alt=""><div class="who"><strong>${b.name}</strong><small>${b.team} · ${record(b)}</small></div></div>
			</div>
			${probBar}${verdict}
		</div>`;
	});
	document.getElementById('matchup-grid').innerHTML = cards.join('') || '<p>No matchups for this week.</p>';
}

function renderStandings() {
	const teams = rosters.map(r => teamInfo(r.roster_id))
		.sort((x, y) => (y.wins - x.wins) || (y.pf - x.pf));
	document.querySelector('#standings-table tbody').innerHTML = teams.map((t, i) =>
		`<tr><td>${i + 1}</td><td><a href="user.html?username=${encodeURIComponent(t.username)}">${t.name}</a> <small style="color:#7a7b85">${t.team}</small></td>` +
		`<td>${record(t)}</td><td>${fmt1(t.pf)}</td><td>${fmt1(t.pa)}</td></tr>`).join('');
}

function renderPower() {
	// Blend of realized points per game and this week's projected median.
	// Before any games are played it is projection alone.
	const snapBy = {};
	(latestReport?.managers || []).forEach(m => { snapBy[m.roster_id] = m; });
	const rows = rosters.map(r => {
		const t = teamInfo(r.roster_id);
		const games = t.wins + t.losses + t.ties;
		const ppg = games ? t.pf / games : null;
		const proj = snapBy[r.roster_id]?.p50 ?? null;
		const w = Math.min(games, 6) / 6;   // realized play earns weight over six weeks
		const score = ppg === null ? proj : proj === null ? ppg : w * ppg + (1 - w) * proj;
		return { t, ppg, proj, score };
	}).filter(r => r.score !== null).sort((x, y) => y.score - x.score);
	document.querySelector('#power-table tbody').innerHTML = rows.map((r, i) =>
		`<tr><td>${i + 1}</td><td>${r.t.name}</td><td>${r.ppg === null ? '—' : fmt1(r.ppg)}</td>` +
		`<td>${r.proj === null ? '—' : fmt1(r.proj)}</td><td>${fmt1(r.score)}</td></tr>`).join('');
}

async function renderScorecard() {
	const el = document.getElementById('scorecard');
	let games = 0, favWins = 0, brier = 0, teamWeeks = 0, covered = 0, absErr = 0;
	for (let w = 1; w < currentWeek; w++) {
		const snap = await snapshot(w);
		if (!snap) continue;
		const ms = await matchups(w);
		if (!ms.some(g => g.points > 0)) continue;
		const pts = {};
		ms.forEach(g => { pts[g.roster_id] = g.points; });
		snap.managers.forEach(m => {
			if (!(m.roster_id in pts)) return;
			teamWeeks++;
			if (pts[m.roster_id] >= m.p10 && pts[m.roster_id] <= m.p90) covered++;
			absErr += Math.abs(pts[m.roster_id] - m.p50);
		});
		snap.matchups.forEach(g => {
			const a = snap.managers.find(m => m.username === g.a), b = snap.managers.find(m => m.username === g.b);
			if (!a || !b || !(a.roster_id in pts) || !(b.roster_id in pts)) return;
			const aWon = pts[a.roster_id] > pts[b.roster_id] ? 1 : 0;
			games++;
			brier += (g.p_a - aWon) ** 2;
			if ((g.p_a >= 0.5) === (aWon === 1)) favWins++;
		});
	}
	if (!games) {
		el.innerHTML = `<div class="stat-tile" style="grid-column: 1 / -1"><div class="value">—</div>` +
			`<div class="label">Scorecard starts after Week 1</div><div class="sub">Week ${currentWeek} predictions are locked. Grading happens when the scores are final.</div></div>`;
		return;
	}
	const tile = (v, l, s) => `<div class="stat-tile"><div class="value">${v}</div><div class="label">${l}</div><div class="sub">${s}</div></div>`;
	el.innerHTML =
		tile(`${favWins}–${games - favWins}`, 'Favorites', `record of the projected favorite over ${games} games`) +
		tile((brier / games).toFixed(3), 'Brier score', 'coin flips score 0.250, lower is better') +
		tile(pct(covered / teamWeeks), '80% band coverage', `${covered} of ${teamWeeks} team-weeks landed inside`) +
		tile(fmt1(absErr / teamWeeks), 'Median miss', 'average points between projection and actual');
}

document.addEventListener('DOMContentLoaded', () => { init().catch(e => {
	console.error(e);
	document.getElementById('matchup-grid').innerHTML = `<p>Could not load league data: ${e.message}</p>`;
}); });
