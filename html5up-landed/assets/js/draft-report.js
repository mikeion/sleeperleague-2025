/* Draft report page. Reads assets/data/draft_report.json, built by
   data-extraction/draft_report.py. No API calls at runtime. */

const ACCENT = '#e44c65';
const DARK = '#1c1d26';
const MUTED = '#b8bcc9';

let REPORT = null;
let byUser = {};

const fmt1 = (x) => (x === null || x === undefined) ? '—' : Number(x).toFixed(1);
const signed = (x) => (x > 0 ? '+' : '') + Number(x).toFixed(0);
const avatar = (m) => m.avatar || 'https://sleepercdn.com/images/v2/icons/player_default.webp';

async function init() {
	Chart.defaults.color = '#c9cbd3';
	Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.08)';
	const res = await fetch('assets/data/draft_report.json');
	REPORT = await res.json();
	REPORT.managers.forEach(m => { byUser[m.username] = m; });

	document.getElementById('report-title').textContent = `${REPORT.season} Draft Report`;
	document.getElementById('report-subtitle').textContent =
		`${REPORT.league}. Built ${REPORT.generated.replace('T', ' ')} from Sleeper picks, ADP, and projections.`;
	document.getElementById('projection-title').textContent = `Projected Week ${REPORT.week}`;
	document.getElementById('matchup-title').textContent = `Week ${REPORT.week} Win Probabilities`;

	renderCards();
	renderProjectionChart();
	renderMatchups();
	renderReachChart();
	renderHistory();
	renderPositions();
	renderLineups();
	renderMethod();
}

function renderCards() {
	const grid = document.getElementById('card-grid');
	grid.innerHTML = REPORT.cards.map(c => {
		const m = c.manager ? byUser[c.manager] : null;
		const img = m ? `<img src="${avatar(m)}" alt="">` : '';
		const name = m ? `${m.name} <small style="color:#7a7b85">@${m.handle}</small>` : 'Matchup';
		return `<div class="report-card">${img}
			<div class="card-body">
				<p class="card-title">${c.title}</p>
				<p class="card-name">${name}</p>
				<p class="card-blurb">${c.blurb}</p>
			</div>
			<div class="card-value">${c.value}</div>
		</div>`;
	}).join('');
}

function renderProjectionChart() {
	const ms = [...REPORT.managers].sort((a, b) => b.week_p50 - a.week_p50);
	const labels = ms.map(m => m.name);
	new Chart(document.getElementById('projection-chart'), {
		type: 'bar',
		data: {
			labels,
			datasets: [
				{
					label: '80% interval',
					data: ms.map(m => [m.week_p10, m.week_p90]),
					backgroundColor: 'rgba(228, 76, 101, 0.35)',
					borderColor: ACCENT,
					borderWidth: 1,
					borderSkipped: false,
					barPercentage: 0.6
				},
				{
					label: 'Median',
					type: 'line',
					data: ms.map(m => m.week_p50),
					showLine: false,
					pointStyle: 'rectRot',
					pointRadius: 7,
					pointHoverRadius: 9,
					backgroundColor: '#ffffff',
					borderColor: '#ffffff'
				}
			]
		},
		options: {
			indexAxis: 'y',
			responsive: true,
			maintainAspectRatio: false,
			scales: {
				x: { min: 60, title: { display: true, text: 'Projected points' } },
				y: { grid: { display: false } }
			},
			plugins: {
				legend: { position: 'bottom' },
				tooltip: {
					callbacks: {
						label: (ctx) => {
							const m = ms[ctx.dataIndex];
							return ctx.datasetIndex === 0
								? ` 10th–90th: ${fmt1(m.week_p10)} – ${fmt1(m.week_p90)}`
								: ` Median ${fmt1(m.week_p50)} (sum of projections ${fmt1(m.week_proj)})`;
						}
					}
				}
			}
		}
	});
}

function renderMatchups() {
	const list = document.getElementById('matchup-list');
	const games = [...REPORT.matchups].sort((a, b) => Math.abs(a.p_a - 0.5) - Math.abs(b.p_a - 0.5));
	list.innerHTML = games.map(g => {
		const a = byUser[g.a], b = byUser[g.b];
		const pa = Math.round(g.p_a * 100), pb = 100 - pa;
		return `<div class="matchup">
			<div class="side"><img src="${avatar(a)}" alt=""><div class="who">${a.name}<small>${fmt1(a.week_p50)} proj · ${fmt1(a.week_p10)}–${fmt1(a.week_p90)}</small></div></div>
			<div class="prob-bar"><div class="fill" style="width:${pa}%"></div>
				<span class="label left">${pa}%</span><span class="label right">${pb}%</span></div>
			<div class="side right"><div class="who">${b.name}<small>${fmt1(b.week_p50)} proj · ${fmt1(b.week_p10)}–${fmt1(b.week_p90)}</small></div><img src="${avatar(b)}" alt=""></div>
		</div>`;
	}).join('');
}

function renderReachChart() {
	const ms = [...REPORT.managers].sort((a, b) => a.reach.avg_abs - b.reach.avg_abs);
	new Chart(document.getElementById('reach-chart'), {
		type: 'bar',
		data: {
			labels: ms.map(m => [m.name, `${m.reach.biggest_reach.name.split(' ').slice(-1)[0]} ${signed(m.reach.biggest_reach.diff)}`]),
			datasets: [
				{ label: 'Average picks off ADP', data: ms.map(m => m.reach.avg_abs), backgroundColor: ACCENT },
				{ label: 'Median picks off ADP', data: ms.map(m => m.reach.median_abs), backgroundColor: MUTED }
			]
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			scales: { y: { beginAtZero: true, title: { display: true, text: 'Picks' } } },
			plugins: {
				legend: { position: 'bottom' },
				tooltip: {
					callbacks: {
						afterBody: (items) => {
							const m = ms[items[0].dataIndex];
							const r = m.reach.biggest_reach, s = m.reach.biggest_steal;
							return [`Biggest reach: ${r.name} at ${r.pick}, ADP ${fmt1(r.adp)}`,
								`Best value: ${s.name} at ${s.pick}, ADP ${fmt1(s.adp)}`];
						}
					}
				}
			}
		}
	});
}

function renderHistory() {
	const h = REPORT.history_league;
	const blurb = document.getElementById('history-blurb');
	if (!h) {
		blurb.textContent = 'No draft history available.';
		return;
	}
	blurb.innerHTML = `A reach is a pick taken at least ${REPORT.reach_threshold} spots before its ADP. ` +
		`Return is a player's regular-season points above replacement at his position, minus what players drafted near the same ADP returned. ` +
		`Across ${h.seasons.join(', ')}: reaches returned <strong>${signed(h.reach_surplus)}</strong> per pick (${h.n_reaches} of them) against <strong>${signed(h.other_surplus)}</strong> for everything else. ` +
		`Zero means the ADP was right. Positive means the manager saw something the market did not.`;

	const rows = REPORT.managers
		.filter(m => m.history)
		.sort((a, b) => (b.history.reach_surplus ?? -999) - (a.history.reach_surplus ?? -999));
	document.querySelector('#history-table tbody').innerHTML = rows.map(m => {
		const hh = m.history;
		let verdict = '<span class="verdict-meh">Too few reaches to say</span>';
		if (hh.n_reaches >= 5) {
			const gap = hh.reach_surplus - (hh.other_surplus ?? 0);
			verdict = gap > 15 ? '<span class="verdict-good">Reaches beat the board</span>'
				: gap < -15 ? '<span class="verdict-bad">Should have trusted ADP</span>'
				: '<span class="verdict-meh">No different from the board</span>';
		}
		return `<tr><td>${m.name}</td><td>${hh.n_reaches}</td><td>${hh.reach_surplus === null ? '—' : signed(hh.reach_surplus)}</td>` +
			`<td>${hh.n_others}</td><td>${hh.other_surplus === null ? '—' : signed(hh.other_surplus)}</td><td>${verdict}</td></tr>`;
	}).join('');
}

function renderPositions() {
	const positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'];
	const ms = [...REPORT.managers].sort((a, b) => {
		const ra = Object.values(a.position_rank).reduce((s, r) => s + r, 0);
		const rb = Object.values(b.position_rank).reduce((s, r) => s + r, 0);
		return ra - rb;
	});
	const n = ms.length;
	document.querySelector('#position-table thead').innerHTML =
		'<tr><th></th>' + ms.map(m => `<th><img src="${avatar(m)}" alt="">${m.name}</th>`).join('') + '</tr>';
	document.querySelector('#position-table tbody').innerHTML = positions.map(pos =>
		`<tr><th>${pos}</th>` + ms.map(m => {
			const rank = m.position_rank[pos];
			const t = 1 - (rank - 1) / (n - 1);
			const bg = `rgba(228, 76, 101, ${0.15 + 0.85 * t})`;
			const color = t > 0.45 ? '#fff' : DARK;
			return `<td class="cell" style="background:${bg};color:${color}">${Math.round(m.position_pts[pos])}<small>${ordinal(rank)}</small></td>`;
		}).join('') + '</tr>'
	).join('');
}

function ordinal(n) {
	const s = ['th', 'st', 'nd', 'rd'], v = n % 100;
	return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

function renderLineups() {
	const select = document.getElementById('lineup-select');
	const ms = [...REPORT.managers].sort((a, b) => a.name.localeCompare(b.name));
	select.innerHTML = ms.map(m => `<option value="${m.username}">${m.name} (${m.team})</option>`).join('');
	const params = new URLSearchParams(window.location.search);
	if (params.get('manager') && byUser[params.get('manager').toLowerCase()]) {
		select.value = params.get('manager').toLowerCase();
	}
	const draw = () => {
		const m = byUser[select.value];
		document.querySelector('#lineup-table tbody').innerHTML = m.week_lineup.map(p =>
			`<tr><td>${p.slot}</td><td>${p.name}</td><td>${p.team || ''}</td><td>${p.bye || ''}</td><td>${fmt1(p.proj)}</td></tr>`
		).join('') + `<tr><th colspan="4">Total</th><th>${fmt1(m.week_proj)}</th></tr>`;
		document.querySelector('#picks-table tbody').innerHTML = m.picks.map(p =>
			`<tr><td>${p.round}.${String(p.pick - (p.round - 1) * REPORT.managers.length)}</td><td>${p.name}</td><td>${p.pos}</td>` +
			`<td>${p.adp === null ? '—' : fmt1(p.adp)}</td><td>${p.diff === null ? '—' : signed(p.diff)}</td><td>${fmt1(p.season_proj)}</td></tr>`
		).join('');
	};
	select.addEventListener('change', draw);
	draw();
}

function renderMethod() {
	const m = REPORT.method;
	const counts = Object.entries(m.residual_counts).map(([k, v]) => `${k}: ${v}`).join(', ');
	document.getElementById('method-text').innerHTML =
		`Projections and ADP are Sleeper's (RotoWire). Each starter's outcome is drawn from the empirical distribution of ` +
		`RotoWire's misses in ${m.calibration_seasons.join(' and ')}, grouped by position and projection band, and the lineup is summed ` +
		`${m.sims.toLocaleString()} times. ${m.note} <span style="color:#7a7b85">Player-weeks per group: ${counts}.</span>`;
}

document.addEventListener('DOMContentLoaded', init);
