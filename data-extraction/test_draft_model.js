/* Offline harness for the draft.html recommendation model.

   The draft hasn't happened yet, so this simulates one: opponents pick by ADP
   with noise, we follow the model's advice at our slot, and we check the roster
   it builds is legal and sensible. Run: node data-extraction/test_draft_model.js
*/
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const ROOT = path.join(__dirname, '..', 'html5up-landed');
const src = fs.readFileSync(path.join(ROOT, 'assets/js/draft.js'), 'utf8');
const board = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets/data/draft_board.json'), 'utf8')).players;

// load draft.js with the browser bits stubbed out
const sandbox = { module: { exports: {} }, console, setInterval() {}, fetch() {}, document: undefined };
sandbox.window = sandbox;
vm.createContext(sandbox);
vm.runInContext(src, sandbox);
const M = sandbox.module.exports;

const TEAMS = 14, ROUNDS = 14, MY_SLOT = 9;
let fails = 0;
const check = (name, cond, detail = '') => {
	console.log(`  ${cond ? 'PASS' : 'FAIL'}  ${name}${detail ? '  — ' + detail : ''}`);
	if (!cond) fails++;
};

function gauss() {
	let u = 0, v = 0;
	while (!u) u = Math.random();
	while (!v) v = Math.random();
	return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

function simulate(seedShuffle) {
	const drafted = new Map();
	const remaining = new Set(board.map(p => p.id));
	const byId = new Map(board.map(p => [p.id, p]));
	const myTaken = [];

	for (let pick = 1; pick <= TEAMS * ROUNDS; pick++) {
		const round = Math.ceil(pick / TEAMS);
		const i = pick - (round - 1) * TEAMS;
		const slot = round % 2 ? i : TEAMS - i + 1;

		let chosen;
		if (slot === MY_SLOT) {
			M.load(board, drafted, MY_SLOT);
			const { scored } = M.recommend();
			if (!scored.length) break;
			chosen = scored[0].p;
			myTaken.push({ round, pick, p: chosen });
		} else {
			// opponents draft by ADP with noise, roughly respecting roster sanity
			const pool = [...remaining].map(id => byId.get(id))
				.filter(p => p.pos !== 'K' && p.pos !== 'DEF' || round >= 12);
			pool.sort((a, b) => ((a.adp || 260) + gauss() * (1.5 + 0.2 * (a.adp || 260)))
				- ((b.adp || 260) + gauss() * (1.5 + 0.2 * (b.adp || 260))));
			chosen = pool[0];
		}
		if (!chosen) break;
		remaining.delete(chosen.id);
		drafted.set(chosen.id, { player_id: chosen.id, pick_no: pick, round, draft_slot: slot });
	}
	return myTaken;
}

console.log('\n=== unit checks ===');
check('slotOf maps round 1 straight', M.slotOf(9) === 9);
check('slotOf reverses round 2', M.slotOf(20) === 9, `slotOf(20)=${M.slotOf(20)}`);
check('slotOf reverses round 4', M.slotOf(48) === 9, `slotOf(48)=${M.slotOf(48)}`);
check('my pick numbers correct',
	M.pickNumbers(9).join(',') === '9,20,37,48,65,76,93,104,121,132,149,160,177,188',
	M.pickNumbers(9).join(','));
check('phi(0)=0.5', Math.abs(M.phi(0) - 0.5) < 1e-6);
check('phi is monotone', M.phi(-2) < M.phi(0) && M.phi(0) < M.phi(2));

const early = { adp: 5 }, late = { adp: 200 };
check('early-ADP player unlikely to last', M.survives(early, 40, 10) < 0.05,
	M.survives(early, 40, 10).toFixed(3));
check('late-ADP player likely to last', M.survives(late, 40, 10) > 0.95,
	M.survives(late, 40, 10).toFixed(3));
check('survival decreases with distance',
	M.survives({ adp: 50 }, 60, 40) > M.survives({ adp: 50 }, 90, 40));

console.log('\n=== need factor ===');
const none = { QB: 0, RB: 0, WR: 0, TE: 0, K: 0, DEF: 0 };
check('K worthless early', M.needFactor('K', none, 12) === 0);
check('K mandatory at the end', M.needFactor('K', none, 2) > 1);
check('2nd QB devalued', M.needFactor('QB', { ...none, QB: 1 }, 8) < 0.2);
check('5th RB devalued vs 1st',
	M.needFactor('RB', { ...none, RB: 5 }, 8) < M.needFactor('RB', none, 8));

console.log('\n=== full-draft simulation (200 runs) ===');
const shapes = [], firstPos = {}, legal = { ok: 0, bad: 0 };
for (let run = 0; run < 200; run++) {
	const taken = simulate();
	const c = { QB: 0, RB: 0, WR: 0, TE: 0, K: 0, DEF: 0 };
	taken.forEach(t => c[t.p.pos]++);
	shapes.push(c);
	const f = taken[0].p.pos;
	firstPos[f] = (firstPos[f] || 0) + 1;
	const startable = c.QB >= 1 && c.RB >= 2 && c.WR >= 2 && c.TE >= 1 && c.K >= 1 && c.DEF >= 1
		&& (c.RB + c.WR + c.TE) >= 7;
	startable ? legal.ok++ : legal.bad++;
}
const avg = k => (shapes.reduce((s, c) => s + c[k], 0) / shapes.length).toFixed(1);
console.log(`  avg roster shape: QB ${avg('QB')}  RB ${avg('RB')}  WR ${avg('WR')}  TE ${avg('TE')}  K ${avg('K')}  DEF ${avg('DEF')}`);
console.log(`  first pick position: ${Object.entries(firstPos).map(([k, v]) => k + ' ' + (v / 2) + '%').join('  ')}`);
check('every simulated roster can field a legal lineup', legal.bad === 0, `${legal.bad} bad of 200`);
check('never drafts 2 kickers', shapes.every(c => c.K <= 1));
check('never drafts 2 defenses', shapes.every(c => c.DEF <= 1));
check('always exactly one K and one DEF', shapes.every(c => c.K === 1 && c.DEF === 1));
check('does not hoard RB (avg < 6)', +avg('RB') < 6, `avg ${avg('RB')}`);
check('takes at least 4 WR on average', +avg('WR') >= 4, `avg ${avg('WR')}`);
check('takes exactly one QB usually', +avg('QB') <= 1.3, `avg ${avg('QB')}`);

console.log('\n=== one sample draft ===');
simulate().forEach(t => {
	const p = t.p;
	console.log(`  R${String(t.round).padStart(2)} pick ${String(t.pick).padStart(3)}  ` +
		`${p.name.padEnd(24)} ${p.pos.padEnd(4)} ${String(p.team || '').padEnd(4)} ` +
		`VBD ${String(p.vbd).padStart(6)}  ADP ${p.adp ? p.adp.toFixed(0) : '-'}`);
});

console.log(`\n${fails === 0 ? 'ALL CHECKS PASSED' : fails + ' CHECK(S) FAILED'}\n`);
process.exit(fails ? 1 : 0);
