// Hierarchical variance-components model for fantasy football weekly scores,
// pooled across leagues.
//
//   y[n]                weekly score of one manager in one week
//   alpha[m]            manager m's persistent deviation from his league mean
//   tau[l], sigma[l]    league l's between-manager and within-manager SDs
//   rho[l]              the ICC for league l, a derived quantity
//
// Both tau and sigma are modelled on the log scale as functions of league
// covariates X (size, PPR, superflex), so the hypotheses about league design
// become coefficients rather than eyeballed subgroup medians. Because
//   rho = tau^2 / (tau^2 + sigma^2)
// is increasing in tau and decreasing in sigma, the effect of covariate k on the
// ICC is signed by d_rho[k] = b_tau[k] - b_sig[k]; that contrast is the test.
//
// A Student-t likelihood is used deliberately: weekly team scores are
// right-skewed sums of skewed player scores, and the normal-theory validation in
// the single-league analysis under-predicted the observed spread of season
// records, which is what fat tails would do. nu is estimated, so the data decide
// how far from normal they are.

data {
  int<lower=1> N;                              // manager-weeks
  int<lower=1> M;                              // manager-within-league units
  int<lower=1> L;                              // leagues
  int<lower=0> K;                              // league covariates
  vector[N] y;
  array[N] int<lower=1, upper=M> mgr;          // which manager each row belongs to
  array[M] int<lower=1, upper=L> mgr_league;   // which league each manager is in
  matrix[L, K] X;                              // standardised league covariates
}

parameters {
  vector[L] mu;                                // league mean weekly score
  vector[M] z_alpha;                           // non-centred manager effects

  real a_tau;   vector[K] b_tau;   real<lower=0> s_tau;   vector[L] z_tau;
  real a_sig;   vector[K] b_sig;   real<lower=0> s_sig;   vector[L] z_sig;

  real<lower=2> nu;
}

transformed parameters {
  vector<lower=0>[L] tau   = exp(a_tau + X * b_tau + s_tau * z_tau);
  vector<lower=0>[L] sigma = exp(a_sig + X * b_sig + s_sig * z_sig);
  vector[M] alpha;
  for (m in 1:M) alpha[m] = tau[mgr_league[m]] * z_alpha[m];
}

model {
  // non-centred hierarchical priors
  z_alpha ~ std_normal();
  z_tau   ~ std_normal();
  z_sig   ~ std_normal();

  // weakly informative, on the log-points scale:
  // exp(1.5) ~ 4.5 pts between managers, exp(3.1) ~ 22 pts within
  a_tau ~ normal(1.5, 1.0);
  a_sig ~ normal(3.1, 0.5);
  b_tau ~ normal(0, 0.5);
  b_sig ~ normal(0, 0.5);
  s_tau ~ normal(0, 0.5);
  s_sig ~ normal(0, 0.5);

  mu ~ normal(110, 30);
  nu ~ gamma(2, 0.1);

  {
    vector[N] m_hat;
    vector[N] s_hat;
    for (n in 1:N) {
      int l = mgr_league[mgr[n]];
      m_hat[n] = mu[l] + alpha[mgr[n]];
      s_hat[n] = sigma[l];
    }
    y ~ student_t(nu, m_hat, s_hat);
  }
}

generated quantities {
  vector[L] rho;                 // per-league ICC
  vector[L] kappa;               // skill-to-noise ratio, tau / (sigma * sqrt2)
  vector[L] p_win_1sd;           // P(a +1 SD manager wins a given week)
  vector[K] d_rho = b_tau - b_sig;   // >0 means this covariate raises the ICC
  real rho_median;

  for (l in 1:L) {
    rho[l]       = square(tau[l]) / (square(tau[l]) + square(sigma[l]));
    kappa[l]     = tau[l] / (sigma[l] * sqrt2());
    p_win_1sd[l] = Phi(kappa[l]);
  }
  {
    vector[L] s = sort_asc(rho);
    rho_median = s[(L + 1) %/% 2];
  }
}
