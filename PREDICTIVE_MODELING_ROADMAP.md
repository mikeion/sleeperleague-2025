# Fantasy Football Predictive Modeling Roadmap

## Vision
Build statistical models to understand what separates successful fantasy football managers from unsuccessful ones. Is it skill, luck, or a combination? What specific behaviors (draft strategy, waiver moves, trades) correlate with success?

## Research Questions

### Primary Questions
1. **Skill vs. Luck**: How much of fantasy football success is skill vs. random variance?
   - Measure consistency across seasons
   - Expected wins vs. actual wins (strength of schedule)
   - Points scored vs. opponent points (luck factor)

2. **Draft Impact**: Does draft position matter? Do early picks outperform late picks?
   - Correlation between draft position and final standings
   - Does "best available player" vs. "positional need" matter?
   - Early RB vs. early WR strategies

3. **In-Season Management**: What separates good managers from great ones?
   - Waiver wire activity vs. success
   - Trade frequency and quality
   - Starting lineup optimization (benching the wrong players)

4. **Consistency**: Are some managers consistently good/bad, or is it random year-to-year?
   - Repeat champions
   - Sacko Bowl winners (last place)
   - Dynasty rankings stability

### Secondary Questions
5. **Format Changes**: How did the switch from MFL (2016-2019) to Yahoo (2020-2021) to Sleeper (2022-2025) affect competitive balance?
6. **Points Per Game Trends**: Are teams scoring more/less over time? League-wide inflation/deflation?
7. **Playoff Predictability**: Can we predict playoff outcomes from regular season performance?

## Data We Have

### Historical Data (10 Years: 2016-2025)
- ✅ Season records (wins, losses, ties)
- ✅ Points for and against
- ✅ Draft positions (MFL 2016-2019, Sleeper 2022-2025)
- ✅ Regular season finish
- ✅ Playoff finish (champion, runner-up)
- ✅ Platform changes (MFL → Yahoo → Sleeper)

### Missing Data (Need to Extract)
- ⏳ 3rd/4th place finishers
- ⏳ Sacko (last place) tracking
- ❌ Weekly matchup data
- ❌ Waiver wire moves
- ❌ Trade data
- ❌ Roster composition (positions drafted)
- ❌ Starting lineup decisions (who was benched)
- ❌ Player performance vs. projections

## Leveraging Existing Tools

### fantasy-football-wrapped (https://github.com/kt474/fantasy-football-wrapped)
**What it provides:**
- Power rankings algorithm
- Expected wins calculation (luck metric)
- Strength of schedule analysis
- Weekly performance tracking
- Trade rankings
- Waiver wire analysis
- AI-generated insights

**How we can use it:**
1. **Fork/Clone**: Start with their codebase as foundation
2. **Extract Components**: Use their algorithms for:
   - Power rankings calculation
   - Expected wins (actual vs. expected based on points)
   - Strength of schedule normalization
3. **Extend**: Add our historical data (2016-2025) to their analysis
4. **Custom Models**: Build on top with our own predictive models

**Integration Strategy:**
```
Option 1: Fork their repo
- Keep their Sleeper-specific features
- Add our 10-year historical analysis
- Merge our dashboard with their weekly insights

Option 2: Extract their algorithms
- Copy power ranking logic
- Copy expected wins calculation
- Implement in our existing codebase

Option 3: Hybrid
- Use their tool for current season analysis
- Our dashboard for historical trends
- Link the two together
```

## Phased Implementation

### Phase 1: Enhanced Playoff Tracking (Current Sprint)
- [ ] Extract 3rd/4th place finishers from playoff brackets
- [ ] Track Sacko winner (last place / consolation bracket loser)
- [ ] Update user profiles to show all playoff placements
- [ ] Add Sacko count to Dynasty Rankings

### Phase 2: Weekly Data Collection (Sleeper Years Only)
- [ ] Extract weekly matchup results (2022-2025)
- [ ] Calculate expected wins vs. actual wins
- [ ] Track strength of schedule
- [ ] Identify "unlucky" losses (high points but faced higher scorer)

### Phase 3: In-Season Management Metrics
- [ ] Extract waiver wire moves from Sleeper API
- [ ] Extract trade data from Sleeper API
- [ ] Calculate "roster churn" (adds/drops per week)
- [ ] Measure trade activity and success

### Phase 4: Draft Analysis
- [ ] Extract full draft results (all rounds, not just Round 1)
- [ ] Categorize draft strategies (RB-heavy, WR-heavy, etc.)
- [ ] Calculate "draft value" vs. ADP
- [ ] Measure draft pick success rate

### Phase 5: Predictive Modeling
- [ ] Build regression models for season success
  - Features: draft position, waiver activity, trade frequency, previous year finish
  - Target: final playoff placement
- [ ] Consistency analysis (variance across seasons)
- [ ] Luck quantification (expected wins model)
- [ ] Identify "skill" factors (reproducible success metrics)

### Phase 6: Interactive Tools
- [ ] "What-if" calculator: "If I had drafted X instead of Y..."
- [ ] Season predictor: Based on first N weeks, predict final standings
- [ ] Manager comparison: Compare your stats to league average
- [ ] "Skill score": Weighted metric of controllable factors

## Technical Considerations

### Data Storage
- Continue using JSON files for historical data
- Consider SQLite or PostgreSQL for weekly/granular data
- Keep data extraction scripts modular and reusable

### Analysis Tools
- Python for statistical modeling (pandas, scikit-learn, statsmodels)
- JavaScript for interactive visualizations (Chart.js, D3.js)
- R for specialized statistical tests (if needed)

### Integration with fantasy-football-wrapped
- Clone their repo to separate directory
- Study their codebase (especially power rankings and expected wins)
- Extract reusable components into shared utilities
- Maintain our dashboard as separate UI
- Use their APIs/algorithms as backend services

## Success Metrics

### For the Analysis
1. Can we identify managers who are consistently above/below expected performance?
2. Can we quantify how much luck vs. skill contributed to each championship?
3. Can we predict season outcomes with >60% accuracy by Week 6?
4. Can we identify specific behaviors that correlate with success?

### For the Tool
1. Provides actionable insights ("You're too passive on waivers")
2. Entertaining and engaging for the league
3. Settles debates ("Who's the luckiest manager?")
4. Helps improve everyone's game

## Next Steps (Priority Order)

1. ✅ **Complete playoff tracking** - Add 3rd/4th/Sacko to current data
2. **Clone fantasy-football-wrapped** - Study their implementation
3. **Extract weekly data** - Get Sleeper weekly matchups for 2022-2025
4. **Build expected wins model** - First real "luck vs. skill" metric
5. **Create analysis notebook** - Jupyter notebook with initial findings

## Questions to Answer First

- [ ] Do we want to fork fantasy-football-wrapped or just learn from it?
- [ ] Should we focus on current season tools or historical analysis first?
- [ ] What's the most interesting question to answer first?
- [ ] Should we share findings with the league as we go, or wait for complete analysis?

---

*This is a living document - update as we make progress and learn more!*
