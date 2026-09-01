/* Draft night board — live Sleeper draft + league-specific VBD.

   The recommendation answers one question: which player would cost me the most
   if I passed on him now? That is his value minus the value I'd expect to still
   find at the same position when I pick again, weighted by roster need.
*/

const DRAFT_ID = '1389689478104231937';
const MY_SLOT = 9;
const TEAMS = 14;
const ROUNDS = 14;
const POLL_MS = 5000;

// avg round each manager takes their first player at a position (2022-25 drafts)
const MANAGERS = {
	1:  { name: 'robbbbbbbb',   qb: 7.5, rb: 3.0, wr: 1.2, te: 6.0 },
	2:  { name: 'DakodiacBear', qb: 3.8, rb: 2.2, wr: 1.8, te: 8.0 },
	3:  { name: 'SamBam805',    qb: 7.0, rb: 2.0, wr: 1.5, te: 7.2 },
	4:  { name: 'robertwneal2', qb: 8.0, rb: 1.5, wr: 1.5, te: 7.8 },
	5:  { name: 'BigDog11',     qb: 6.0, rb: 1.2, wr: 2.0, te: 5.8 },
	6:  { name: 'otterboi',     qb: 7.5, rb: 2.8, wr: 1.8, te: 8.0 },
	7:  { name: 'Spaceman917',  qb: 7.2, rb: 1.5, wr: 1.8, te: 6.2 },
	8:  { name: 'Casey',        qb: 5.5, rb: 1.5, wr: 1.5, te: 7.0 },
	9:  { name: 'YOU',          qb: 4.8, rb: 3.0, wr: 1.5, te: 4.8 },
	10: { name: 'Gordonulus',   qb: 6.8, rb: 1.5, wr: 1.5, te: 5.5 },
	11: { name: 'rpthorp',      qb: 4.8, rb: 2.5, wr: 2.0, te: 4.8 },
	12: { name: 'buddygalletti',qb: 2.5, rb: 1.0, wr: 3.8, te: 5.2 },
	13: { name: 'CaptainBigCup',qb: 4.7, rb: 1.0, wr: 4.3, te: 7.0 },
	14: { name: 'fishy11',      qb: 5.8, rb: 1.5, wr: 3.0, te: 7.5 }
};

let BOARD = [];
let byId = new Map();
let drafted = new Map();   // player_id -> pick object
let myPicks = [];
let posFilter = 'ALL';
let lastPickCount = -1;

const slotOf = (pickNo) => {
	const r = Math.ceil(pickNo / TEAMS);
	const i = pickNo - (r - 1) * TEAMS;
	return r % 2 ? i : TEAMS - i + 1;
};
const pickNumbers = (slot) => {
	const out = [];
	for (let r = 1; r <= ROUNDS; r++)
		out.push(r % 2 ? (r - 1) * TEAMS + slot : r * TEAMS - slot + 1);
	return out;
};

// normal CDF via Abramowitz-Stegun erf approximation
function phi(z) {
	const s = z < 0 ? -1 : 1;
	const x = Math.abs(z) / Math.SQRT2;
	const t = 1 / (1 + 0.3275911 * x);
	const y = 1 - ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t
		- 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
	return 0.5 * (1 + s * y);
}

// P(player lasts past pick n), conditioned on being available at pick `now`
function survives(p, n, now) {
	const adp = p.adp || 260;
	const sd = 1.5 + 0.20 * adp;
	const pastNow = 1 - phi((now - adp) / sd);
	const pastN = 1 - phi((n - adp) / sd);
	if (pastNow <= 1e-6) return pastN > 0.5 ? 1 : 0;
	return Math.max(0, Math.min(1, pastN / pastNow));
}

// expected VBD of the best player at this position still there at pick n
function expectedBest(pool, n, now) {
	let carry = 1, exp = 0;
	for (const p of pool) {
		const s = survives(p, n, now);
		exp += p.vbd * s * carry;
		carry *= (1 - s);
		if (carry < 1e-4) break;
	}
	return exp;
}

function myRoster() {
	const mine = [...drafted.values()].filter(p => p.draft_slot === MY_SLOT);
	const counts = { QB: 0, RB: 0, WR: 0, TE: 0, K: 0, DEF: 0 };
	const players = [];
	for (const pk of mine) {
		const p = byId.get(pk.player_id);
		if (p) { counts[p.pos] = (counts[p.pos] || 0) + 1; players.push(p); }
	}
	return { counts, players };
}

/* How much a position is still worth to this roster.

   The QB and TE curves are deliberately damped in the early rounds. Raw VBD
   overrates single-slot positions here: because you start only one, the scarcity
   drop-off at QB is steep enough to outrank a better RB/WR on pure value, but
   three independent sources say that is a trap in this league — Sleeper ADP has
   every QB going ahead of its VBD rank, the workbook's VBD flags Lamar (-24),
   Burrow (-15) and Maye (-14) as reaches, and in four years of this league's
   drafts QB1 has not gone before pick 21 while six managers have never taken one
   before round 7. So a QB has to clear a much higher bar to win an early pick.
*/
function needFactor(pos, counts, picksLeft) {
	const n = counts[pos] || 0;
	// Endgame: QB, TE, K and DEF each need exactly one body. Once the picks
	// remaining equal the number of those slots still empty, spend them there
	// and nowhere else, or we finish the draft unable to field a lineup.
	const unfilled = ['QB', 'TE', 'K', 'DEF'].filter(s => !(counts[s] || 0));
	if (picksLeft <= unfilled.length) return unfilled.includes(pos) ? 5.0 : 0;
	// K and DEF are worthless until the end, then mandatory
	if (pos === 'K' || pos === 'DEF') {
		if (n > 0) return 0;
		return picksLeft <= 2 ? 3.0 : (picksLeft <= 4 ? 0.8 : 0);
	}
	if (pos === 'QB') {
		if (n > 0) return 0.02;               // never a second QB with a 4-man bench
		if (picksLeft > 9) return 0.35;       // rounds 1-5: let the elite QBs pass
		if (picksLeft > 5) return 0.90;       // rounds 6-9: the sweet spot
		return 1.25;
	}
	if (pos === 'TE') {
		if (n === 1) return 0.28;
		if (n > 1) return 0.06;
		if (picksLeft > 10) return 0.55;
		if (picksLeft > 5) return 1.00;
		return 1.20;
	}
	if (n < 2) return 1.0;
	if (n < 4) return 0.85;
	if (n < 5) return 0.5;
	return 0.22;
}

function recommend() {
	const now = drafted.size + 1;
	const next = myPicks.find(p => p >= now);
	const later = myPicks.filter(p => p > (next || 999));
	const nextAfter = later.length ? later[0] : null;
	const picksLeft = myPicks.filter(p => p >= now).length;
	const { counts } = myRoster();

	const avail = BOARD.filter(p => !drafted.has(p.id));
	const pools = {};
	for (const p of avail) (pools[p.pos] = pools[p.pos] || []).push(p);
	for (const k in pools) pools[k].sort((a, b) => b.vbd - a.vbd);

	// baseline: what I'd expect to get at this position at my following pick
	const fallback = {};
	for (const k in pools)
		fallback[k] = nextAfter ? expectedBest(pools[k], nextAfter, now) : 0;

	// When it isn't our turn yet this is a preview, so weight every player by the
	// chance he is even still there when we pick. Otherwise the board happily
	// recommends the overall best player left while he is being drafted by
	// someone else eight picks ahead of us.
	const onClock = next === now;
	const horizon = onClock ? nextAfter : next;

	const scored = avail.map(p => {
		const drop = p.vbd - (fallback[p.pos] || 0);
		const nf = needFactor(p.pos, counts, picksLeft);
		// Scale by need, but keep the sign meaningful: damping a negative drop
		// would make an unwanted position look *better*, which is how a spare QB
		// used to win the last pick of the draft.
		let score = drop >= 0 ? drop * nf : drop / Math.max(nf, 0.05);
		const reachable = onClock ? 1 : survives(p, next, now);
		if (score > 0) score *= reachable;
		return {
			p,
			score,
			drop,
			nf,
			reachable,
			surv: horizon ? survives(p, horizon, now) : 1
		};
	}).filter(x => x.nf > 0);

	scored.sort((a, b) => b.score - a.score);
	return { scored, now, next, nextAfter, picksLeft, counts, onClock, horizon };
}

/* ---------- rendering ---------- */

function gapManagers(from, to) {
	const seen = new Map();
	for (let i = from + 1; i < to; i++) {
		const s = slotOf(i);
		seen.set(s, (seen.get(s) || 0) + 1);
	}
	return [...seen.entries()].map(([s, c]) => ({ ...MANAGERS[s], slot: s, picks: c }));
}

const posClass = (p) => 'pos-' + p.toLowerCase();

function riskNote(p) {
	if (p.miss == null) return '';
	if (p.miss >= 3.0) return `<span class="warn">injury risk ${p.miss} gm</span>`;
	if (p.miss <= 2.0) return `<span class="good">durable ${p.miss} gm</span>`;
	return '';
}

function render() {
	const { scored, now, next, nextAfter, picksLeft, counts, onClock, horizon } = recommend();
	const clockSlot = slotOf(now);
	const isMine = onClock;
	const away = next ? next - now : null;

	document.getElementById('status').innerHTML = `
		<div class="status-row">
			<div><span class="lbl">Pick</span><b>${Math.min(now, TEAMS * ROUNDS)}</b> of ${TEAMS * ROUNDS}</div>
			<div><span class="lbl">Round</span><b>${Math.ceil(now / TEAMS)}</b></div>
			<div><span class="lbl">On the clock</span><b>${MANAGERS[clockSlot] ? MANAGERS[clockSlot].name : '-'}</b></div>
			<div><span class="lbl">Your next</span><b>${next ? '#' + next : 'done'}</b>
				${away !== null && away > 0 ? `<em>${away} away</em>` : ''}</div>
		</div>`;

	const banner = document.getElementById('turn-banner');
	banner.className = isMine ? 'turn-banner active' : 'turn-banner';
	banner.textContent = isMine ? "YOU'RE ON THE CLOCK" :
		(away !== null && away <= 3 ? `Get ready — ${away} pick${away === 1 ? '' : 's'} away` : '');

	// headline recommendation
	const top = scored[0];
	const rec = document.getElementById('rec');
	if (!next || !top) { rec.innerHTML = '<div class="rec-label">DRAFT COMPLETE</div>'; }
	else {
		const p = top.p;
		const why = [];
		if (horizon && top.surv < 0.35) why.push(`only <b>${Math.round(top.surv * 100)}%</b> to last to #${horizon}`);
		if (!isMine) why.push(`<b>${Math.round(top.reachable * 100)}%</b> he reaches your #${next}`);
		if (p.tier) why.push(`Chen ${p.pos} tier <b>${p.tier}</b>`);
		if (p.adp) why.push(`ADP <b>${p.adp.toFixed(0)}</b>`);
		why.push(`VBD <b>${p.vbd.toFixed(0)}</b>`);
		rec.innerHTML = `
			<div class="rec-label">${isMine ? 'TAKE' : 'LIKELY AT YOUR #' + next}</div>
			<div class="rec-name ${posClass(p.pos)}">${p.name}</div>
			<div class="rec-meta">${p.pos} · ${p.team || 'FA'}${p.bye ? ' · bye ' + p.bye : ''} ${riskNote(p)}</div>
			<div class="rec-why">${why.join(' &nbsp;·&nbsp; ')}</div>`;
	}

	// alternatives
	const rows = scored.filter(x => posFilter === 'ALL' || x.p.pos === posFilter).slice(0, 14);
	document.getElementById('alts').innerHTML = `
		<table>
			<thead><tr><th></th><th>Player</th><th>Pos</th><th>Tm</th>
				<th title="Chen tier">Tier</th><th>VBD</th><th>ADP</th>
				<th title="chance he is still on the board at that pick">${horizon ? 'To #' + horizon : 'Lasts'}</th>
				<th title="projected missed games">Inj</th></tr></thead>
			<tbody>${rows.map((x, i) => {
				const p = x.p;
				const s = Math.round(x.surv * 100);
				const cls = x.surv < 0.35 ? 'gone' : (x.surv > 0.75 ? 'safe' : '');
				return `<tr class="${i === 0 ? 'lead' : ''}">
					<td class="rank">${i + 1}</td>
					<td class="nm">${p.name}</td>
					<td><span class="tag ${posClass(p.pos)}">${p.pos}</span></td>
					<td>${p.team || '-'}</td>
					<td>${p.tier || '-'}</td>
					<td><b>${p.vbd.toFixed(0)}</b></td>
					<td>${p.adp ? p.adp.toFixed(0) : '-'}</td>
					<td class="${cls}">${horizon ? s + '%' : '-'}</td>
					<td>${p.miss != null ? p.miss.toFixed(1) : '-'}</td>
				</tr>`;
			}).join('')}</tbody>
		</table>`;

	// roster + gap
	const slots = [['QB', 1], ['RB', 2], ['WR', 2], ['TE', 1], ['K', 1], ['DEF', 1]];
	document.getElementById('roster').innerHTML = slots.map(([pos, need]) => {
		const have = counts[pos] || 0;
		const cls = have >= need ? 'filled' : 'empty';
		return `<div class="slot ${cls}"><span class="tag ${posClass(pos)}">${pos}</span>
			<b>${have}</b><em>/${need}</em></div>`;
	}).join('') + `<div class="slot"><span class="lbl">picks left</span><b>${picksLeft}</b></div>`;

	if (next && nextAfter) {
		const gap = gapManagers(next, nextAfter);
		const rd = Math.ceil(now / TEAMS);
		document.getElementById('gap').innerHTML =
			`<h4>Between your #${next} and #${nextAfter} — ${nextAfter - next - 1} picks</h4>` +
			`<div class="mgrs">${gap.map(m => {
				const hot = [];
				if (m.qb <= rd + 1) hot.push('QB');
				if (m.te <= rd + 1) hot.push('TE');
				if (m.rb <= rd + 0.5) hot.push('RB');
				if (m.wr <= rd + 0.5) hot.push('WR');
				return `<div class="mgr"><b>${m.name}</b><em>${m.picks}&times;</em>
					<span>${hot.length ? 'takes ' + hot.join('/') + ' by now' : ''}</span></div>`;
			}).join('')}</div>`;
	} else {
		document.getElementById('gap').innerHTML = '';
	}

	// recent picks
	const recent = [...drafted.values()].sort((a, b) => b.pick_no - a.pick_no).slice(0, 8);
	document.getElementById('recent').innerHTML = recent.map(pk => {
		const p = byId.get(pk.player_id);
		const m = MANAGERS[pk.draft_slot];
		return `<div class="pk"><em>#${pk.pick_no}</em>
			<b>${p ? p.name : pk.player_id}</b>
			<span>${m ? m.name : ''}</span></div>`;
	}).join('') || '<div class="pk"><span>no picks yet</span></div>';
}

async function poll() {
	try {
		const res = await fetch(`https://api.sleeper.app/v1/draft/${DRAFT_ID}/picks`);
		const picks = await res.json();
		if (picks.length !== lastPickCount) {
			drafted = new Map(picks.map(p => [p.player_id, p]));
			lastPickCount = picks.length;
			render();
		}
		document.getElementById('live').textContent = 'live · ' + new Date().toLocaleTimeString();
	} catch (e) {
		document.getElementById('live').textContent = 'connection lost — retrying';
	}
}

async function init() {
	const data = await (await fetch('assets/data/draft_board.json')).json();
	BOARD = data.players;
	byId = new Map(BOARD.map(p => [p.id, p]));
	myPicks = pickNumbers(MY_SLOT);
	document.getElementById('mypicks').textContent = myPicks.join('  ·  ');

	document.querySelectorAll('#filters button').forEach(b => {
		b.onclick = () => {
			posFilter = b.dataset.pos;
			document.querySelectorAll('#filters button').forEach(x => x.classList.remove('on'));
			b.classList.add('on');
			render();
		};
	});
	render();
	poll();
	setInterval(poll, POLL_MS);
}

if (typeof document !== 'undefined') document.addEventListener('DOMContentLoaded', init);

/* exposed for the node test harness in data-extraction/test_draft_model.js */
if (typeof module !== 'undefined' && module.exports) {
	module.exports = {
		slotOf, pickNumbers, phi, survives, expectedBest, needFactor, recommend, myRoster,
		load: (board, draftedMap, slot) => {
			BOARD = board;
			byId = new Map(board.map(p => [p.id, p]));
			drafted = draftedMap;
			myPicks = pickNumbers(slot);
		}
	};
}
