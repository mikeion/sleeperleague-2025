// ========================================
// FANTASY LEAGUE WRAPPED - UI & Animations
// ========================================

// Global state
let wrappedData = null;
let selectedManager = null;
let slides = [];
let currentSlide = 0;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Register GSAP plugins
    gsap.registerPlugin(ScrollTrigger);

    // Get slides
    slides = document.querySelectorAll('.wrapped-slide');

    // Set up event listeners
    setupEventListeners();

    // Initialize data loading
    initWrapped();
});

// Event Listeners
function setupEventListeners() {
    // Manager dropdown change
    const dropdown = document.getElementById('manager-dropdown');
    const startBtn = document.getElementById('start-wrapped-btn');

    if (dropdown) {
        dropdown.addEventListener('change', (e) => {
            startBtn.disabled = !e.target.value;
        });
    }

    if (startBtn) {
        startBtn.addEventListener('click', () => {
            const manager = dropdown.value;
            if (manager) {
                selectManager(manager);
            }
        });
    }

    // Copy link button
    const copyBtn = document.getElementById('copy-link-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', copyShareLink);
    }

    // Listen for data ready event
    window.addEventListener('wrappedDataReady', (e) => {
        wrappedData = e.detail;
        populateManagerDropdown();
        hideLoading();
    });

    // Listen for manager selection from URL
    window.addEventListener('managerSelected', (e) => {
        selectManager(e.detail);
    });

    // Listen for show manager selector
    window.addEventListener('showManagerSelector', () => {
        hideLoading();
        showManagerSelector();
    });
}

// Hide loading screen
function hideLoading() {
    const loading = document.getElementById('loading-screen');
    if (loading) {
        loading.classList.add('hidden');
    }
}

// Show/hide manager selector
function showManagerSelector() {
    const selector = document.getElementById('manager-selector');
    if (selector) {
        selector.classList.remove('hidden');
    }
}

function hideManagerSelector() {
    const selector = document.getElementById('manager-selector');
    if (selector) {
        selector.classList.add('hidden');
    }
}

// Populate manager dropdown
function populateManagerDropdown() {
    const dropdown = document.getElementById('manager-dropdown');
    if (!dropdown || !wrappedData) return;

    const managers = Object.values(wrappedData.managers)
        .sort((a, b) => a.displayName.localeCompare(b.displayName));

    dropdown.innerHTML = '<option value="">Choose a manager...</option>';
    managers.forEach(manager => {
        const option = document.createElement('option');
        option.value = manager.username;
        option.textContent = manager.displayName;
        dropdown.appendChild(option);
    });
}

// Select a manager and start the experience
function selectManager(username) {
    selectedManager = username;
    const manager = wrappedData.managers[username];

    if (!manager) {
        console.error('Manager not found:', username);
        return;
    }

    // Update URL
    const url = new URL(window.location);
    url.searchParams.set('manager', username);
    window.history.replaceState({}, '', url);

    // Hide selector, populate data, start animations
    hideManagerSelector();
    populateSlides(manager);
    setupScrollAnimations();
    setupNavDots();
}

// Populate all slides with data
function populateSlides(manager) {
    // Slide 2: Season Overview
    animateCounter('stat-weeks', wrappedData.weeksCompleted);
    animateCounter('stat-games', wrappedData.league.totalGames);
    animateCounter('stat-points', Math.round(wrappedData.league.totalPoints), true);

    // Slide 3: Your Season
    document.getElementById('manager-name').textContent = manager.displayName;
    document.getElementById('your-record').textContent =
        `${manager.record.wins}-${manager.record.losses}${manager.record.ties > 0 ? `-${manager.record.ties}` : ''}`;

    // Show both regular season rank and playoff finish
    const rankBadge = document.querySelector('#your-rank');
    const rankNumber = rankBadge.querySelector('.rank-number');
    const rankLabel = rankBadge.querySelector('.rank-label');

    if (manager.playoffFinish) {
        // Show playoff result prominently
        rankNumber.textContent = manager.playoffFinish.emoji || `#${manager.playoffFinish.place}`;
        rankLabel.innerHTML = `${manager.playoffFinish.label}<br><span style="font-size: 0.7em; opacity: 0.8;">(#${manager.regularSeasonRank} regular season)</span>`;
    } else {
        // No playoff data - just show regular season
        rankNumber.textContent = `#${manager.regularSeasonRank}`;
        rankLabel.textContent = 'Regular Season';
    }

    document.getElementById('your-pf').textContent = manager.pointsFor.toFixed(1);
    document.getElementById('your-pa').textContent = manager.pointsAgainst.toFixed(1);

    // Slide 4: Peak Week
    document.getElementById('peak-score').textContent = manager.peakWeek.score.toFixed(1);
    document.getElementById('peak-week').textContent = manager.peakWeek.week;

    // Calculate rank among all weeks
    const allScores = wrappedData.league.top5Scores;
    const peakRank = allScores.findIndex(s =>
        s.manager === manager.displayName && s.week === manager.peakWeek.week
    );
    const rankContext = document.getElementById('peak-rank-context');
    if (peakRank >= 0 && peakRank < 5) {
        rankContext.innerHTML = `<strong>#${peakRank + 1}</strong> highest score of the season!`;
    } else {
        rankContext.innerHTML = `That was a great week!`;
    }

    // Slide 5: Valley Week
    document.getElementById('valley-score').textContent = manager.valleyWeek.score.toFixed(1);
    document.getElementById('valley-week').textContent = manager.valleyWeek.week;

    // Slide 6: Consistency (now uses chart - label set based on stdDev)
    const maxStdDev = Math.max(...Object.values(wrappedData.managers).map(m => m.consistencyScore));
    const consistencyPct = Math.max(0, 100 - (manager.consistencyScore / maxStdDev) * 100);

    const consistencyLabel = document.getElementById('consistency-label');
    if (consistencyPct > 80) {
        consistencyLabel.textContent = 'Rock solid - steady every week';
    } else if (consistencyPct > 60) {
        consistencyLabel.textContent = 'Pretty reliable';
    } else if (consistencyPct > 40) {
        consistencyLabel.textContent = 'Some ups and downs';
    } else {
        consistencyLabel.textContent = 'Boom or bust - wild swings';
    }

    // Slide 7: Luck Index
    const luckValue = document.getElementById('luck-value');
    const luckSign = manager.luckIndex >= 0 ? '+' : '';
    luckValue.textContent = `${luckSign}${manager.luckIndex.toFixed(1)}`;
    luckValue.className = `luck-number ${manager.luckIndex >= 0 ? 'positive' : 'negative'}`;

    document.getElementById('luck-label').textContent =
        manager.luckIndex >= 0 ? 'wins above expected' : 'wins below expected';

    document.getElementById('luck-context').textContent =
        `You won ${manager.record.wins} games but "deserved" ${manager.expectedWins.toFixed(1)} based on your scoring`;

    // Slide 8: Nemesis
    if (manager.nemesis) {
        document.getElementById('nemesis-name').textContent = manager.nemesis.name;
        document.getElementById('nemesis-record').textContent = manager.nemesis.record + ' against them';
    } else {
        document.getElementById('nemesis-name').textContent = 'Nobody!';
        document.getElementById('nemesis-record').textContent = 'You dominated everyone';
        document.querySelector('#slide-nemesis .rivalry-text').textContent = 'No one had your number this season';
    }

    // Slide 9: Victim
    if (manager.victim) {
        document.getElementById('victim-name').textContent = manager.victim.name;
        document.getElementById('victim-record').textContent = manager.victim.record + ' against them';
    } else {
        document.getElementById('victim-name').textContent = 'Nobody!';
        document.getElementById('victim-record').textContent = 'Tough matchups all around';
        document.querySelector('#slide-victim .rivalry-text').textContent = 'Every win was hard-fought';
    }

    // Slide 10: Closest Game
    if (manager.closestGame) {
        const game = manager.closestGame;
        const myScore = game.score.toFixed(1);
        const theirScore = game.opponentScore.toFixed(1);
        document.getElementById('closest-score').textContent =
            game.won ? `${myScore} - ${theirScore}` : `${theirScore} - ${myScore}`;
        document.getElementById('closest-opponent').textContent = game.opponentName;
        document.getElementById('closest-week').textContent = game.week;
        document.getElementById('closest-margin').textContent = Math.abs(game.margin).toFixed(1);

        const resultEl = document.getElementById('closest-result');
        resultEl.textContent = game.won ? 'W' : 'L';
        resultEl.className = `matchup-result ${game.won ? 'win' : 'loss'}`;
    }

    // Slide 11: Champion
    if (wrappedData.league.champion) {
        document.getElementById('champion-name').textContent = wrappedData.league.champion;
    } else {
        document.getElementById('champion-name').textContent = 'TBD';
        document.querySelector('#slide-champion .slide-label').textContent = 'STILL IN PROGRESS';
    }

    // Slide 12: Top 5 Scores
    const top5List = document.getElementById('top5-list');
    top5List.innerHTML = wrappedData.league.top5Scores.map((score, i) => `
        <div class="leaderboard-item">
            <span class="leaderboard-rank">${i + 1}</span>
            <div class="leaderboard-info">
                <div class="leaderboard-name">${score.manager}</div>
                <div class="leaderboard-week">Week ${score.week}</div>
            </div>
            <span class="leaderboard-score">${score.score.toFixed(1)}</span>
        </div>
    `).join('');

    // Slide 13: Biggest Blowout
    if (wrappedData.league.biggestBlowout) {
        const blowout = wrappedData.league.biggestBlowout;
        document.getElementById('blowout-winner').textContent = blowout.winner;
        document.getElementById('blowout-score').textContent =
            `${blowout.winnerScore.toFixed(1)} - ${blowout.loserScore.toFixed(1)}`;
        document.getElementById('blowout-loser').textContent = blowout.loser;
        document.getElementById('blowout-margin').textContent = blowout.margin.toFixed(1);
        document.getElementById('blowout-week').textContent = blowout.week;
    }

    // Slide 14: Heartbreaker
    if (wrappedData.league.heartbreaker) {
        const hb = wrappedData.league.heartbreaker;
        document.getElementById('heartbreak-loser').textContent = hb.loser;
        document.getElementById('heartbreak-margin').textContent = hb.margin.toFixed(2);
        document.getElementById('heartbreak-winner').textContent = hb.winner;
        document.getElementById('heartbreak-week').textContent = hb.week;
    }

    // Slide 15: Share Card
    document.getElementById('share-name').textContent = manager.displayName;
    document.getElementById('share-record').textContent =
        `${manager.record.wins}-${manager.record.losses}`;

    // Show playoff finish if available, otherwise regular season rank
    if (manager.playoffFinish) {
        document.getElementById('share-rank').textContent = manager.playoffFinish.emoji || `#${manager.playoffFinish.place}`;
    } else {
        document.getElementById('share-rank').textContent = `#${manager.regularSeasonRank}`;
    }
    document.getElementById('share-points').textContent = manager.pointsFor.toFixed(0);

    const shareLink = `${window.location.origin}/wrapped.html?manager=${manager.username}`;
    document.getElementById('share-link').textContent = shareLink;

    // Initialize all charts
    initializeCharts(manager);
}

// Animate number counter
function animateCounter(elementId, targetValue, useCommas = false) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const duration = 2;
    const obj = { value: 0 };

    gsap.to(obj, {
        value: targetValue,
        duration: duration,
        ease: 'power2.out',
        onUpdate: () => {
            const val = Math.round(obj.value);
            element.textContent = useCommas ? val.toLocaleString() : val;
        }
    });
}

// Setup scroll-triggered animations
function setupScrollAnimations() {
    // Intro slide animations
    gsap.to('.slide-intro .reveal-text', {
        opacity: 1,
        y: 0,
        duration: 1,
        stagger: 0.3,
        ease: 'power3.out',
        delay: 0.5
    });

    // Each slide gets scroll-triggered animations
    slides.forEach((slide, index) => {
        if (index === 0) return; // Skip intro, already animated

        const content = slide.querySelector('.slide-content');

        gsap.fromTo(content,
            { opacity: 0, y: 50 },
            {
                opacity: 1,
                y: 0,
                duration: 0.8,
                ease: 'power3.out',
                scrollTrigger: {
                    trigger: slide,
                    start: 'top 80%',
                    toggleActions: 'play none none reverse'
                }
            }
        );

        // Special animations for specific slides
        if (slide.id === 'slide-overview') {
            ScrollTrigger.create({
                trigger: slide,
                start: 'top center',
                onEnter: () => {
                    animateCounter('stat-weeks', wrappedData.weeksCompleted);
                    animateCounter('stat-games', wrappedData.league.totalGames);
                    animateCounter('stat-points', Math.round(wrappedData.league.totalPoints), true);
                }
            });
        }

        // Charts handle their own animations now
    });

    // Update nav dots on scroll
    slides.forEach((slide, index) => {
        ScrollTrigger.create({
            trigger: slide,
            start: 'top center',
            end: 'bottom center',
            onEnter: () => updateNavDot(index),
            onEnterBack: () => updateNavDot(index)
        });
    });
}

// Setup navigation dots
function setupNavDots() {
    const nav = document.getElementById('wrapped-nav');
    if (!nav) return;

    nav.innerHTML = slides.length > 0
        ? Array.from(slides).map((_, i) =>
            `<span class="nav-dot ${i === 0 ? 'active' : ''}" data-slide="${i}"></span>`
        ).join('')
        : '';

    // Click to scroll to slide
    nav.querySelectorAll('.nav-dot').forEach(dot => {
        dot.addEventListener('click', () => {
            const slideIndex = parseInt(dot.dataset.slide);
            slides[slideIndex].scrollIntoView({ behavior: 'smooth' });
        });
    });
}

// Update active nav dot
function updateNavDot(index) {
    currentSlide = index;
    document.querySelectorAll('.nav-dot').forEach((dot, i) => {
        dot.classList.toggle('active', i === index);
    });
}

// Copy share link to clipboard
function copyShareLink() {
    const manager = wrappedData.managers[selectedManager];
    const link = `${window.location.origin}/wrapped.html?manager=${manager.username}`;

    navigator.clipboard.writeText(link).then(() => {
        const btn = document.getElementById('copy-link-btn');
        const originalText = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Could not copy link:', err);
    });
}

// ========================================
// CHART CREATION FUNCTIONS
// ========================================

// Register Chart.js components (required for v4+)
if (typeof Chart !== 'undefined') {
    Chart.register(
        Chart.LineController,
        Chart.BarController,
        Chart.LineElement,
        Chart.BarElement,
        Chart.PointElement,
        Chart.LinearScale,
        Chart.CategoryScale,
        Chart.Legend,
        Chart.Tooltip,
        Chart.Filler
    );
}

// Store chart instances for cleanup
let chartInstances = {};

// Destroy existing chart if it exists
function destroyChart(chartId) {
    if (chartInstances[chartId]) {
        chartInstances[chartId].destroy();
        delete chartInstances[chartId];
    }
}

// Common chart options
const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: {
                color: 'rgba(255, 255, 255, 0.8)',
                font: { family: '-apple-system, BlinkMacSystemFont, sans-serif' }
            }
        }
    },
    scales: {
        x: {
            ticks: { color: 'rgba(255, 255, 255, 0.7)' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
        },
        y: {
            ticks: { color: 'rgba(255, 255, 255, 0.7)' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
        }
    }
};

// Create Season Journey Chart (line graph of weekly scores)
function createJourneyChart(manager) {
    const ctx = document.getElementById('journey-chart');
    if (!ctx) return;

    destroyChart('journey');

    const weeks = manager.weeklyScores.map((_, i) => `Wk ${i + 1}`);
    const scores = manager.weeklyScores;

    // Calculate league average per week
    const allManagers = Object.values(wrappedData.managers);
    const leagueAvgByWeek = weeks.map((_, i) => {
        const weekScores = allManagers.map(m => m.weeklyScores[i] || 0).filter(s => s > 0);
        return weekScores.reduce((a, b) => a + b, 0) / weekScores.length;
    });

    chartInstances['journey'] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: weeks,
            datasets: [
                {
                    label: 'Your Score',
                    data: scores,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: scores.map((s, i) => {
                        // Color points based on win/loss if we have that data
                        return s > leagueAvgByWeek[i] ? '#6bcf6b' : '#ff6b6b';
                    }),
                    pointRadius: 6,
                    pointHoverRadius: 8
                },
                {
                    label: 'League Average',
                    data: leagueAvgByWeek,
                    borderColor: 'rgba(255, 255, 255, 0.5)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0
                }
            ]
        },
        options: {
            ...chartDefaults,
            plugins: {
                ...chartDefaults.plugins,
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.dataset.label}: ${context.raw.toFixed(1)} pts`
                    }
                }
            }
        }
    });
}

// Create Consistency Chart (box plot style showing score distribution)
function createConsistencyChart(manager) {
    const ctx = document.getElementById('consistency-chart');
    if (!ctx) return;

    destroyChart('consistency');

    const scores = [...manager.weeklyScores].sort((a, b) => a - b);
    const min = scores[0];
    const max = scores[scores.length - 1];
    const avg = scores.reduce((a, b) => a + b, 0) / scores.length;

    // Create a histogram of scores
    const bucketSize = 10;
    const minBucket = Math.floor(min / bucketSize) * bucketSize;
    const maxBucket = Math.ceil(max / bucketSize) * bucketSize;
    const buckets = [];
    const bucketLabels = [];

    for (let b = minBucket; b < maxBucket; b += bucketSize) {
        bucketLabels.push(`${b}-${b + bucketSize}`);
        const count = scores.filter(s => s >= b && s < b + bucketSize).length;
        buckets.push(count);
    }

    chartInstances['consistency'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: bucketLabels,
            datasets: [{
                label: 'Games',
                data: buckets,
                backgroundColor: bucketLabels.map((_, i) => {
                    const bucketMid = minBucket + (i * bucketSize) + bucketSize / 2;
                    if (bucketMid >= avg) return 'rgba(107, 207, 107, 0.7)';
                    return 'rgba(255, 107, 107, 0.7)';
                }),
                borderColor: 'rgba(255, 255, 255, 0.3)',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            ...chartDefaults,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.raw} game${context.raw !== 1 ? 's' : ''}`
                    }
                }
            },
            scales: {
                ...chartDefaults.scales,
                y: {
                    ...chartDefaults.scales.y,
                    beginAtZero: true,
                    ticks: {
                        ...chartDefaults.scales.y.ticks,
                        stepSize: 1
                    }
                }
            }
        }
    });

    // Update range text
    const rangeEl = document.getElementById('consistency-range');
    if (rangeEl) {
        rangeEl.textContent = `${min.toFixed(1)} - ${max.toFixed(1)} pts`;
    }
}

// Create Head-to-Head Chart
function createH2HChart(manager) {
    const ctx = document.getElementById('h2h-chart');
    if (!ctx) return;

    destroyChart('h2h');

    // Use actual H2H record from data
    const h2hRecord = manager.h2hRecord || [];

    if (h2hRecord.length === 0) {
        console.log('No H2H record data available');
        return;
    }

    // Sort by most games played together
    const sortedH2H = [...h2hRecord].sort((a, b) =>
        (b.wins + b.losses) - (a.wins + a.losses)
    );

    const opponents = sortedH2H.map(r => r.opponent);
    const wins = sortedH2H.map(r => r.wins);
    const losses = sortedH2H.map(r => r.losses);

    chartInstances['h2h'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: opponents,
            datasets: [
                {
                    label: 'Wins',
                    data: wins,
                    backgroundColor: 'rgba(107, 207, 107, 0.8)',
                    borderRadius: 5
                },
                {
                    label: 'Losses',
                    data: losses,
                    backgroundColor: 'rgba(255, 107, 107, 0.8)',
                    borderRadius: 5
                }
            ]
        },
        options: {
            ...chartDefaults,
            indexAxis: 'y',
            plugins: {
                ...chartDefaults.plugins,
                legend: {
                    ...chartDefaults.plugins.legend,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    ...chartDefaults.scales.x,
                    stacked: false,
                    beginAtZero: true,
                    ticks: {
                        ...chartDefaults.scales.x.ticks,
                        stepSize: 1
                    }
                },
                y: {
                    ...chartDefaults.scales.y,
                    stacked: false
                }
            }
        }
    });
}

// Create Top 5 Scores Chart
function createTop5Chart() {
    const ctx = document.getElementById('top5-chart');
    if (!ctx) return;

    destroyChart('top5');

    const top5 = wrappedData.league.top5Scores;
    const labels = top5.map(s => `${s.manager} (Wk ${s.week})`);
    const scores = top5.map(s => s.score);

    // Gradient colors for podium effect
    const colors = [
        'rgba(255, 215, 0, 0.9)',   // Gold
        'rgba(192, 192, 192, 0.9)', // Silver
        'rgba(205, 127, 50, 0.9)',  // Bronze
        'rgba(102, 126, 234, 0.8)', // Purple
        'rgba(102, 126, 234, 0.6)'  // Light purple
    ];

    chartInstances['top5'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Points',
                data: scores,
                backgroundColor: colors,
                borderColor: 'rgba(255, 255, 255, 0.3)',
                borderWidth: 1,
                borderRadius: 8
            }]
        },
        options: {
            ...chartDefaults,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.raw.toFixed(1)} points`
                    }
                }
            },
            scales: {
                x: {
                    ...chartDefaults.scales.x,
                    beginAtZero: false,
                    min: Math.min(...scores) - 20
                },
                y: {
                    ...chartDefaults.scales.y
                }
            }
        }
    });
}

// Initialize all charts for a manager
function initializeCharts(manager) {
    // Small delay to ensure canvas elements are ready
    setTimeout(() => {
        createJourneyChart(manager);
        createConsistencyChart(manager);
        createH2HChart(manager);
        createTop5Chart();
    }, 100);
}
