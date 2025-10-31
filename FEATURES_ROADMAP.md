# Fantasy League Dashboard - Features Roadmap

## Completed Features ✅

### Phase 1: Data Integration (Completed)
- [x] MFL data extraction (2016-2019)
- [x] Yahoo data extraction (2020-2021)
- [x] Sleeper API integration (2022-2025)
- [x] Owner mapping across platforms
- [x] Dynasty Rankings page with complete history
- [x] Champions timeline (2016-2025)
- [x] First name display mapping

### Phase 2: Dashboard Polish (Completed)
- [x] Remove "Interesting Stats & Records" section
- [x] Work in progress disclaimer
- [x] Proper name formatting (Ryan instead of Thorp, Chris instead of Chris Attias, Mike instead of Mike Ion)
- [x] Runner-up display for Yahoo seasons

## In Progress 🚧

### Phase 3: User Profile Pages
**Goal:** Individual manager pages with detailed career statistics

#### User Page (`/user.html`)
**URL Structure:** `/user.html?username=mikeion`

**Sections to Build:**

1. **Profile Header**
   - [ ] Display user's first name prominently
   - [ ] Career overview stats card
     - [ ] Total games played
     - [ ] Overall record (W-L-T)
     - [ ] Career win percentage
     - [ ] Total championships
     - [ ] Total runner-up finishes
     - [ ] Years in league
   - [ ] Profile badge/icon (could use first letter or custom icon)

2. **Year-by-Year Performance Table**
   - [ ] Sortable table with columns:
     - Year
     - Platform (MFL/Yahoo/Sleeper badge)
     - Record (W-L-T)
     - Win %
     - Points For
     - Points Against
     - Point Differential
     - Final Rank
     - Playoff Result (Champion 🏆, Runner-up 🥈, Made Playoffs, Missed)
   - [ ] Color coding for championship/playoff years
   - [ ] Expandable rows for more detail?

3. **Career Performance Charts**
   - [ ] **Points Per Season Line Chart**
     - X-axis: Years (2016-2025)
     - Y-axis: Total points
     - Line showing trend over time
     - Highlight championship years with marker
   - [ ] **Win Percentage by Season**
     - Bar or line chart
     - Show league average as reference line
   - [ ] **Season Rank History**
     - Line chart showing final rank each year
     - Lower is better visualization
   - [ ] **Points For vs Points Against**
     - Dual-line chart comparing offensive vs defensive performance

4. **Head-to-Head Records**
   - [ ] Table showing record against each opponent
     - Opponent name
     - Games played
     - W-L-T record
     - Win percentage
     - Total points scored against them
   - [ ] Sort by: Most played, Best record, Worst record
   - [ ] **Highlight stats:**
     - 🏆 Best matchup (highest win %)
     - 😱 Nemesis (lowest win %)
     - 🤝 Most played opponent
     - 💥 Highest scoring game against
     - 😭 Worst loss to

5. **Career Milestones & Records**
   - [ ] Best single season (points)
   - [ ] Worst single season (points)
   - [ ] Best record in a season
   - [ ] Worst record in a season
   - [ ] Longest winning streak
   - [ ] Longest losing streak
   - [ ] Most points in a single game
   - [ ] Fewest points in a single game
   - [ ] Biggest blowout win (margin)
   - [ ] Worst blowout loss (margin)
   - [ ] Average points per season
   - [ ] Average finish position
   - [ ] Playoff appearance rate

6. **Season Highlights Timeline**
   - [ ] Chronological list of notable achievements:
     - Championship wins with scores
     - Runner-up finishes
     - Playoff appearances
     - High-scoring seasons
     - Career milestones (100th win, etc.)
   - [ ] Each item expandable for more details

7. **Comparison Tools**
   - [ ] "Compare with another manager" dropdown
   - [ ] Side-by-side stats comparison
   - [ ] Head-to-head record highlighted

#### Technical Implementation
- [ ] Create `user.html` page
- [ ] Add JavaScript function to parse username from URL params
- [ ] Create `renderUserProfile(username)` function in `league-data.js`
- [ ] Add Chart.js integration for line charts
- [ ] Style cards and sections consistently with existing design
- [ ] Make manager names in Dynasty Rankings clickable links to user pages
- [ ] Add "Back to Dynasty Rankings" navigation

#### Data Requirements
- [ ] Aggregate user stats across all platforms (MFL, Yahoo, Sleeper)
- [ ] Calculate head-to-head records (may need weekly matchup data)
- [ ] Calculate streaks and milestones
- [ ] Generate chart data in proper format for Chart.js

## Future Features 💡

### Phase 4: League Insights
- [ ] League-wide statistics page
  - [ ] Most competitive season (closest records)
  - [ ] Highest scoring season
  - [ ] Parity metrics
  - [ ] Home vs Away records (if applicable)
- [ ] Power rankings calculator
- [ ] Playoff odds calculator (for current season)

### Phase 5: Interactive Features
- [ ] Trade analyzer/history
- [ ] Draft history and analysis
- [ ] Waiver wire activity
- [ ] Weekly recap narratives
- [ ] Rivalry tracker

### Phase 6: Social Features
- [ ] Manager notes/trash talk section
- [ ] Season predictions
- [ ] Awards voting (Most Improved, etc.)
- [ ] League constitution/rules page

### Phase 7: Mobile Optimization
- [ ] Responsive design improvements
- [ ] Mobile-friendly charts
- [ ] Touch-optimized navigation
- [ ] PWA support for offline access

### Phase 8: Advanced Analytics
- [ ] "Luck" metrics (points against variance)
- [ ] Strength of schedule
- [ ] Consistency scores
- [ ] Clutch performance metrics
- [ ] Weekly performance variance

## Technical Debt & Improvements
- [ ] Add loading states for all data fetches
- [ ] Error handling for missing data
- [ ] Cache optimization
- [ ] Add unit tests for data transformation
- [ ] Document API endpoints and data formats
- [ ] Add data validation
- [ ] Optimize for large datasets (10+ years)
- [ ] Remove "Unknown" and "buddygalletti" display issues in Yahoo data

## Data Gaps to Fill
- [ ] Weekly matchup results for head-to-head records
- [ ] Draft data (if available from platforms)
- [ ] Waiver/trade data
- [ ] Keeper/dynasty player data
- [ ] Weekly high scores

## Design System
- [ ] Create consistent color palette for charts
- [ ] Championship gold (#FFD700)
- [ ] Runner-up silver (#C0C0C0)
- [ ] Playoff green (#4CAF50)
- [ ] Regular season blue (#2196F3)
- [ ] Standard card/section styling
- [ ] Loading skeletons
- [ ] Error state designs
- [ ] Empty state designs

## Notes
- Chart.js is already included via CDN
- HTML5 UP Landed template provides base styling
- Data is loaded from JSON files (MFL, Yahoo) and Sleeper API
- All usernames normalized to lowercase for consistency
- Display names mapped via USERNAME_TO_NAME constant
