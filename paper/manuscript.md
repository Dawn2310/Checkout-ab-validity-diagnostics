%% Springer Nature LaTeX Template - Reviewer-2 Major Revision Version (13-page readable layout)
%% Compile with: pdflatex -> bibtex -> pdflatex -> pdflatex

\documentclass[pdflatex,sn-mathphys-num]{sn-jnl}

\usepackage{graphicx}
\usepackage{multirow}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{amsthm}
\usepackage{mathrsfs}
\usepackage[title]{appendix}
\usepackage{xcolor}
\usepackage{textcomp}
\usepackage{manyfoot}
\usepackage{booktabs}
\usepackage{siunitx}
\usepackage{array}
\usepackage{placeins}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}

% Readable layout tuning for the revised submission draft.
% Content is preserved; margins are no longer over-widened, and float spacing is
% kept moderate so tables and figures do not overlap while staying near discussion.
\geometry{left=34mm,right=34mm,top=26mm,bottom=26mm,bindingoffset=0mm}
\setlength{\textfloatsep}{12pt plus 3pt minus 2pt}
\setlength{\floatsep}{10pt plus 3pt minus 2pt}
\setlength{\intextsep}{10pt plus 3pt minus 2pt}
\setlength{\abovecaptionskip}{5pt}
\setlength{\belowcaptionskip}{3pt}
\linespread{1.07}
\renewcommand{\topfraction}{0.88}
\renewcommand{\bottomfraction}{0.72}
\renewcommand{\textfraction}{0.12}
\renewcommand{\floatpagefraction}{0.75}
\setcounter{topnumber}{2}
\setcounter{bottomnumber}{1}
\setcounter{totalnumber}{4}

\theoremstyle{thmstyleone}
\newtheorem{theorem}{Theorem}
\newtheorem{proposition}[theorem]{Proposition}
\theoremstyle{thmstyletwo}
\newtheorem{example}{Example}
\newtheorem{remark}{Remark}
\theoremstyle{thmstylethree}
\newtheorem{definition}{Definition}

\raggedbottom
\setlength{\emergencystretch}{2em}
\setlength{\bibsep}{1pt plus 0.3ex}

\begin{document}

\title[Aggregate Campaign Diagnostics]{What Can Be Learned from a Daily-Aggregate Marketing Campaign Dataset? Validity Diagnostics, Overdispersion, and Limits of Causal Interpretation}

\author*[1]{\fnm{Nguyen Luong Hai} \sur{Dang}}\email{nguyenluonghaidang2006pq@gmail.com}
\author[1]{\fnm{Duong Quoc} \sur{Huu}}
\author[1]{\fnm{Nguyen Thi Thanh} \sur{Tien}}

\affil*[1]{\orgdiv{Faculty of Artificial Intelligence},
\orgname{FPT University},
\orgaddress{\country{Vietnam}}}

\abstract{This study re-analyses a public daily-aggregate e-commerce dataset commonly framed as a checkout A/B test, but which structurally resembles a comparison of two aggregate marketing campaigns. The paper serves as a methodological caution rather than a direct product-deployment recommendation. The dataset contains large click counts but only paired daily aggregates and lacks documentation of the randomisation unit, intended allocation ratio, user identifiers, traffic-source composition, and session boundaries. These missing design details make a naive causal interpretation unsafe. We combine aggregate conversion-rate comparison with day-level robustness checks, sample-ratio-mismatch diagnostics, overdispersion modelling (quasi-binomial GLM), and funnel-stage decomposition. The click-pooled comparison suggests that the Test variant has lower overall conversion than Control, but this result is no longer statistically supported when calendar days are treated as the effective unit of variation and overdispersion is accounted for. Funnel decomposition reveals an acquisition--conversion contrast: the Test variant generates more clicks but has lower downstream progression. This pattern is more plausibly interpreted as compositional confounding (attracting a lower-intent audience via ads) than as direct evidence of mid-funnel checkout friction. Validity diagnostics further show that the daily variance is inflated by roughly 163$\times$ compared to a naive binomial assumption, driving an extreme false-positive rate in A/A simulations. The main contribution is therefore diagnostic: daily aggregate datasets can be useful for detecting fragility and compositional confounding, but they require robust overdispersion modelling and cannot by themselves support confident causal rollout decisions without unit-level tracking.}

\keywords{A/B testing, Conversion rate optimisation, Marketing campaigns,
Overdispersion, Funnel decomposition, Sample ratio mismatch,
Aggregate data, E-commerce}

\maketitle

%==============================================================
\section{Introduction}\label{sec:intro}
%==============================================================

Digital marketing campaigns and product changes are routinely evaluated using A/B testing. In a well-instrumented experiment, the analyst knows the exposure unit, the randomisation scheme, the allocation ratio, and the relationship between users, sessions, clicks, and purchases. Under those conditions, a conversion-rate comparison can support a relatively direct rollout decision \cite{kohavi2009controlled,kohavi2020trustworthy}.

However, public A/B testing datasets are rarely this complete. They often provide only aggregate counts by day and variant. Such data can still be useful, but their evidential role changes. Instead of asking only whether variant A or B wins, the more defensible question is what the aggregate data can and cannot support. A large denominator of clicks may produce a very small $p$-value, but treating clicks as independent trials ignores the substantial day-to-day overdispersion typical of marketing campaigns. A funnel table may show different rates at different stages, but conditional rates after a treatment-affected click can reflect compositional selection (i.e., acquiring a different mix of users) rather than stage-specific design effects.

This paper re-analyses a popular public A/B testing dataset from this cautious perspective. Although often presented as a ``checkout-page redesign,'' the dataset structurally resembles a comparison of two marketing campaigns. It provides one Control row and one Test row per day over a short calendar window, reporting ad-centric metrics such as impressions, reach, clicks, and campaign spend, alongside downstream web events. It does not report user identifiers, the randomisation unit, the intended allocation ratio, or session-level covariates. These omissions are not minor metadata issues. They determine whether clicks can be treated as independent trials, whether sample-ratio mismatch is a randomisation failure or a treatment effect on click-through, and whether downstream funnel rates can be given a causal interpretation.

We address three research questions:

\begin{enumerate}
\item[\textbf{RQ1}] What does the aggregate conversion comparison show, and how does the conclusion change when the analysis unit shifts from clicks to days?
\item[\textbf{RQ2}] What do overdispersion modelling, sample-ratio-mismatch diagnostics, and A/A simulation reveal about the reliability of naive inference on this aggregate dataset?
\item[\textbf{RQ3}] What descriptive funnel and temporal patterns appear, and why should they be treated as hypothesis-generating rather than causal?
\end{enumerate}

The contribution of the paper is not a claim that the Test campaign should be deployed or rejected. Rather, the contribution is a structured diagnostic reading of a poorly documented aggregate experiment. The analysis shows how an apparently decisive pooled conversion-rate result becomes fragile once the analyst accounts for design ambiguity, time aggregation, post-treatment selection into clicks, and sparse subgroup evidence. This reframing turns the dataset from a simple conversion-rate exercise into a case study on the limits of causal interpretation in public A/B testing data.

%==============================================================
\section{Related Work}\label{sec:related}
%==============================================================

\subsection{Online controlled experiments}\label{subsec:oce}

Online controlled experiments are the standard empirical framework for evaluating digital product changes. The core literature emphasises that credible experimentation requires more than a comparison of two observed rates. Analysts must define the randomisation unit, track exposure consistently, pre-specify primary metrics, handle ratio metrics appropriately, and diagnose validity problems such as sample ratio mismatch \cite{kohavi2009controlled,kohavi2013online,kohavi2020trustworthy,larsen2024statistical}. These concerns are especially important when public datasets contain only aggregate summaries, because the analyst cannot verify whether the available denominator is the same as the experimental unit.

\subsection{Ratio metrics, overdispersion, and diagnostics}\label{subsec:cuped}

Conversion rate is a ratio metric. Its numerator and denominator may vary together over time, across campaigns, or across traffic sources. For this reason, a test that treats every click as an independent Bernoulli trial can be misleading when the data are temporally aggregated. Delta-method approaches for ratio metrics and variance-reduction methods such as CUPED are designed to address some of these challenges when suitable pre-treatment covariates are available \cite{deng2013improving,deng2018applying}. Furthermore, when binary events are clustered within campaigns or days, the variance often far exceeds the binomial assumption. Quasi-binomial models directly estimate this overdispersion, scaling standard errors to match the observed cluster-level variation. However, these methods cannot recover missing experimental-design information. They can reduce variance or clarify uncertainty, but they cannot identify the randomisation unit after it has been discarded from the data.

Sample ratio mismatch is another central diagnostic. In a clean randomised experiment, observed exposure counts should be compatible with the intended allocation ratio. A mismatch may indicate allocation failure, logging errors, bot filtering, or inconsistent inclusion rules \cite{kohavi2020trustworthy,larsen2024statistical}. In the present dataset, the intended allocation ratio is not known and the mismatch is measured on clicks, not on documented randomised users. The SRM result must therefore be interpreted as an ambiguity diagnostic, not as automatic proof of broken randomisation.

\subsection{Funnel analysis and post-treatment selection}\label{subsec:funnel-selection}

Funnel analysis is useful because product interventions often affect different stages in different directions. A checkout redesign may change attention, product inspection, cart formation, and purchase completion separately. Prior studies on cart abandonment and checkout experience motivate this stage-wise perspective \cite{kukar2010determinants,huang2018mobile,mcdowell2016retail,bleier2019creating}.

At the same time, funnel rates are not automatically causal stage effects. If treatment changes the probability of clicking, then the set of users who click under Test may differ from the set who click under Control. Any later rate conditioned on clickers is then affected by post-treatment selection. A lower add-to-cart rate among Test clickers may reflect lower purchase intent among the additional clickers attracted by the design, not necessarily a defect in the cart step itself. This is the key causal distinction that the present paper makes explicit.

\subsection{Heterogeneous effects under sparse aggregate data}\label{subsec:hte}

Heterogeneous treatment-effect analysis asks whether the average effect hides subgroup-level reversals. Prior work discusses the value of subgroup analysis as well as the risk of false discoveries when many segment comparisons are explored \cite{taddy2016nonparametric,yu2018false}. Uplift modelling extends this idea to individual-level targeting \cite{devriendt2018literature,gubela2020response,athey2019machine}. However, uplift modelling requires real unit-level covariates and outcomes. Reconstructing pseudo-sessions from daily rates cannot create genuine within-day individual heterogeneity. For that reason, this revised analysis does not use pseudo-session uplift scores as evidence for deployment. It treats the weekday patterns only as exploratory descriptive signals.

%==============================================================
\section{Data and Design Ambiguity}\label{sec:data}
%==============================================================

\subsection{Observed data}\label{subsec:dataset}

The dataset contains 60 daily campaign records from 1--30 August 2019: one Control row and one Test row for each day. The dataset labels the two arms as Control and Test. Although it is commonly framed as a checkout-page experiment, the available variables more directly describe aggregate marketing-campaign performance than a verified on-page randomised redesign. Each row includes aggregate counts for spend, impressions, reach, clicks, searches, view-content events, add-to-cart events, and purchases. One Control row on 5 August 2019 has missing count fields and is imputed by forward fill.

Revenue is not observed. Earlier versions of this manuscript used a constant assumed average order value to compute revenue per session. That metric is removed from the main analysis because a constant average order value merely rescales conversion rate and can misleadingly appear to add independent evidence. We therefore analyse observed count and rate metrics only.

\begin{table}[!htbp]
\caption{Observed aggregate counts and derived rates per variant. Spend is campaign spend, not observed purchase revenue.}\label{tab:dataset}
\begin{tabular}{@{}lcc@{}}
\toprule
Quantity & Control & Test\\
\midrule
Impressions & \num{3250111} & \num{2237544} \\
Clicks & \num{157368} & \num{180970} \\
View-content events & \num{57352} & \num{55740} \\
Add-to-cart events & \num{38883} & \num{26446} \\
Purchases & \num{15501} & \num{15637} \\
Spend (USD) & \num{68653} & \num{76892} \\
\midrule
Click-through rate & \SI{4.84}{\percent} & \SI{8.09}{\percent} \\
View-content per click & \SI{36.44}{\percent} & \SI{30.80}{\percent} \\
Add-to-cart per view-content & \SI{67.80}{\percent} & \SI{47.45}{\percent} \\
Purchase per click & \SI{9.85}{\percent} & \SI{8.64}{\percent} \\
\botrule
\end{tabular}
\end{table}

\subsection{Design ambiguity as an analysis constraint}\label{subsec:design}

The dataset lacks the design metadata needed for a complete causal evaluation. Table~\ref{tab:claim-boundary} states how each missing item limits the claims that can be made. This table is central to the revised manuscript because it prevents the empirical sections from overstating what the public aggregate data can prove.

\begin{table}[!htbp]
\caption{Missing design metadata and the resulting claim boundary.}\label{tab:claim-boundary}
\small
\begin{tabular}{@{}L{0.24\textwidth}L{0.34\textwidth}L{0.32\textwidth}@{}}
\toprule
Missing information & Why it matters & Claim boundary used in this paper\\
\midrule
Randomisation unit & Determines whether clicks, sessions, users, campaigns, or days are independent experimental units. & Click-pooled tests are descriptive and are not treated as definitive causal inference.\\
Intended allocation ratio & Required for a formal SRM pass/fail interpretation. & SRM is interpreted as an ambiguity warning, with sensitivity to plausible reference splits.\\
User/session identifiers & Needed to separate repeated behaviour from independent observations. & No individual-level targeting or user-level causal heterogeneity is claimed.\\
Traffic-source and device mix & Needed to distinguish treatment effects from compositional changes in the audience. & Funnel and weekday patterns are treated as hypotheses, not deployment rules.\\
Pre-treatment covariates & Needed for strong CUPED adjustment and robust uplift modelling. & CUPED is a sensitivity check only; pseudo-session uplift is not used as main evidence.\\
\botrule
\end{tabular}
\end{table}

%==============================================================
\section{Methodology}\label{sec:method}
%==============================================================

\subsection{Metrics and denominators}\label{subsec:metrics}

The primary observed outcome is conversion rate among clickers:
\begin{equation}
\mathrm{CR}=\frac{\mathrm{purchases}}{\mathrm{clicks}}.
\end{equation}
This denominator is analytically convenient but causally delicate because clicks can be affected by treatment. Therefore, later funnel rates are interpreted as conditional descriptive rates, not as clean stage-specific treatment effects.

\begin{table}[!htbp]
\caption{Funnel metric definitions. Explicit denominators are reported to avoid ambiguity in conditional-rate interpretation.}\label{tab:metric-defs}
\small
\begin{tabular}{@{}L{0.27\textwidth}L{0.28\textwidth}L{0.35\textwidth}@{}}
\toprule
Metric & Definition & Interpretation caveat\\
\midrule
Click-through rate & Clicks / impressions & Can be directly affected by the variant and changes who enters later stages.\\
View-content per click & View-content events / clicks & Conditional on post-treatment clickers; affected by clicker composition.\\
Add-to-cart per view-content & Add-to-cart events / view-content events & Conditional on users who already reached a later stage.\\
Purchase given add-to-cart & Purchases / add-to-cart events & Conditional on cart formation; not comparable to overall conversion.\\
Overall conversion rate & Purchases / clicks & Primary descriptive outcome among clickers, but not necessarily a user-level causal effect.\\
\botrule
\end{tabular}
\end{table}

\subsection{Aggregate and day-level inference}\label{subsec:methods-classical}

We report the click-pooled two-proportion $Z$-test because it is the standard first analysis for a binary conversion outcome. However, we do not treat it as sufficient. We also report Welch's $t$-test and Mann--Whitney tests on daily conversion rates, and bootstrap intervals over daily resamples \cite{davison1997bootstrap}. The purpose of presenting both views is to expose the analysis-unit tension: clicks create a large denominator, whereas days represent the only replicated units directly visible in the public data.

For ratio metrics, the relevant day-level uncertainty can be expressed through the delta method. If $N_d$ denotes purchases and $D_d$ denotes clicks on day $d$, the rate is $R=N/D$. A first-order approximation is
\begin{equation}
\widehat{\operatorname{Var}}(\hat R) \approx \frac{1}{\bar D^2}\widehat{\operatorname{Var}}(N_d-\hat R D_d),
\end{equation}
which highlights that variation in the numerator and denominator should be considered jointly \cite{deng2018applying}. With only daily aggregates, this approximation is informative but still cannot replace the missing randomisation unit.

To formalise the day-to-day variance, we fit a quasi-binomial Generalized Linear Model (GLM). The outcome is the number of purchases over the number of clicks, modelled by the variant indicator. Unlike a naive binomial model, the quasi-binomial approach estimates a dispersion scale parameter from the Pearson chi-square statistic divided by the residual degrees of freedom. This scales the standard errors to account for the unobserved daily shocks common in aggregate campaign data, making it far more appropriate than assuming independent Bernoulli trials.

\subsection{Validity diagnostics}\label{subsec:methods-validity}

We examine sample ratio mismatch under several reference allocations rather than only a 50/50 split:
\begin{equation}
\chi^{2}_{\mathrm{SRM}} = \sum_{a\in\{C,T\}} \frac{(n_{a} - n p_{a})^{2}}{n p_{a}}.
\end{equation}
Here, $n_a$ is the observed click count in arm $a$, and $p_a$ is a reference allocation share. Because the true allocation is unavailable, the result is not a definitive randomisation-failure test. It is a sensitivity analysis showing which allocation assumptions would make the observed click split surprising.

We also run an A/A simulation. In each simulation, Control days were randomly split into two pseudo-arms, their clicks and purchases were pooled within each pseudo-arm, and a two-proportion $Z$-test was applied. This simulation does not imply that all pooled tests are flawed; rather, it demonstrates that naive pooled inference on daily aggregate data is severely biased due to day-level clustering and non-exchangeability. A highly non-uniform A/A $p$-value distribution indicates that daily rows are not a reliable basis for replicated causal inference.

\subsection{Funnel and heterogeneity analysis}\label{subsec:methods-funnel-hte}

Funnel-stage comparisons are computed with two-proportion tests and Holm correction. The tests are reported because they reveal where observed rates differ, but the interpretation is deliberately cautious. Since clickers and later-stage users are post-treatment subsets, a stage difference can reflect a change in user composition rather than a direct effect of the redesigned checkout component.

Weekday heterogeneity is analysed descriptively by pooling clicks within weekday labels and comparing Control and Test conversion rates. The dataset covers only one month, so each weekday has only four or five paired daily observations. For this reason, weekday results are used to motivate follow-up hypotheses rather than specific day-of-week deployment recommendations.

CUPED is included only as a supplementary sensitivity check and is relegated to the appendix. The available pre-period information is weak and aggregate, so CUPED produced negligible variance reduction and did not change the substantive conclusion \cite{deng2013improving}.

%==============================================================
\section{Results}\label{sec:results}
%==============================================================

\subsection{Aggregate conversion suggests a Test loss, but only under a click-level view}\label{subsec:results-aggregate}

At the click-pooled level, the Test variant has a lower purchase-per-click rate than the Control variant: \SI{8.64}{\percent} compared with \SI{9.85}{\percent}. The absolute difference is about $-1.21$ percentage points. If each click is treated as an independent Bernoulli trial, the result is highly statistically significant. That conclusion is technically correct under the click-level model, but the model is not guaranteed by the dataset.

\begin{table}[!htbp]
\caption{Click-pooled conversion comparison for overall purchases per click.}\label{tab:aggregate}
\begin{tabular}{@{}lc@{}}
\toprule
Quantity & Result\\
\midrule
CR Control & \SI{9.8502}{\percent} (Wilson 95\% CI: 9.70--9.99\%) \\
CR Test & \SI{8.6407}{\percent} (Wilson 95\% CI: 8.51--8.77\%) \\
Absolute CR difference & $-1.21$ percentage points \\
Relative CR difference & $-\SI{12.28}{\percent}$ \\
Two-proportion $Z$ & $-12.139$; $p<10^{-30}$ \\
$\chi^{2}$ on $2\times2$ table & $147.21$; df = 1; $p<10^{-30}$ \\
\botrule
\end{tabular}
\end{table}

The key analytical point is that the table does not settle the causal question. The visible independent records in the public dataset are days, not individual randomised users. In aggregate marketing campaigns, daily unobserved shocks (e.g., ad delivery algorithms, competitor actions, or weekday seasonality) cause conversion rates to fluctuate much more than a binomial distribution would predict. We model this by fitting a quasi-binomial Generalized Linear Model (GLM) where standard errors are scaled by the Pearson chi-square dispersion statistic.

\begin{table}[!htbp]
\caption{Day-level overdispersion and robustness checks. These results describe uncertainty when days, rather than clicks, are treated as the visible repeated units.}\label{tab:sensitivity}
\small
\begin{tabular}{@{}L{0.32\textwidth}L{0.24\textwidth}L{0.34\textwidth}@{}}
\toprule
Check & Result & Interpretation\\
\midrule
Estimated dispersion scale & $162.95$ & Variance is inflated roughly 163$\times$ compared to a naive binomial model.\\
Quasi-Binomial GLM $p$-value & $p=0.342$ & The conversion difference is entirely non-significant after correcting for overdispersion.\\
Daily Welch $t$-test & $t=-1.518$; $p=0.135$ & The daily-rate difference is not significant at the 5\% level.\\
Bootstrap CI for relative uplift & $[-32.19\%, +12.71\%]$ & The daily-resampled interval crosses zero.\\
\botrule
\end{tabular}
\end{table}

This contrast is the first main finding. The dataset supports a descriptive statement that the Test campaign had lower pooled conversion among its clickers. However, it does not support a high-confidence causal claim that the Test campaign's underlying true conversion rate was worse, because the observed difference is well within the bounds of daily overdispersed noise.

\begin{figure}[!htbp]
\centering
\includegraphics[width=0.68\textwidth]{figures/cr_bar_with_ci.png}
\caption{Overall conversion rate per variant with Wilson 95\% confidence intervals.}\label{fig:cr_bar}
\end{figure}

\subsection{Funnel decomposition reveals a compositional puzzle, not a direct mechanism}\label{subsec:results-funnel}

The funnel analysis reveals why the aggregate result is difficult to interpret. The Test variant has a much higher click-through rate, but lower view-content and add-to-cart progression among the users who enter the funnel. Among users who reach the cart, the Test arm has a higher purchase-given-cart rate. A superficial reading would say that the redesign improves attraction and late purchase completion but damages the middle of the funnel. The more rigorous reading is weaker and more useful: the redesign changes the composition of the users observed at each conditional stage.

\begin{table}[!htbp]
\caption{Funnel-stage differences with explicit interpretation limits. Tests use two-proportion comparisons with Holm correction.}\label{tab:funnel}
\small
\begin{tabular}{@{}L{0.24\textwidth}ccccL{0.22\textwidth}@{}}
\toprule
Funnel step & Control & Test & Relative diff. & $p_{\mathrm{Holm}}$ & Interpretation limit\\
\midrule
CTR & 4.84\% & 8.09\% & $+67.0\%$ & $<10^{-30}$ & Pre-click comparison over impressions.\\
View-content per click & 36.44\% & 30.80\% & $-15.5\%$ & $<10^{-30}$ & Conditional on clickers.\\
Add-to-cart per view-content & 67.80\% & 47.45\% & $-30.0\%$ & $<10^{-30}$ & Conditional on viewers.\\
Purchase given add-to-cart & 39.87\% & 59.13\% & $+48.3\%$ & $<10^{-30}$ & Conditional on cart users.\\
Overall purchase per click & 9.85\% & 8.64\% & $-12.3\%$ & $<10^{-30}$ & Clicker-level descriptive outcome.\\
\botrule
\end{tabular}
\end{table}

The observed pattern is consistent with at least two different stories. One story is a design-mechanism story: the Test campaign's landing page attracts attention but introduces friction before cart formation. Another story is a selection story: the Test campaign attracts additional lower-intent clickers (perhaps via broader ad targeting), so the conditional mid-funnel rates decline even if the checkout mechanics themselves are identical. Given that the observed variables resemble campaign-level aggregates rather than a verified controlled on-page split test, the selection story should be treated as the more cautious interpretation. The aggregate dataset cannot fully disentangle these without user-level tracking. This is why the paper treats funnel decomposition as diagnostic exploration rather than causal mechanism identification.

\begin{figure}[!htbp]
\centering
\includegraphics[width=0.78\textwidth]{figures/uplift_waterfall.png}
\caption{Relative differences by funnel step, Test versus Control.}\label{fig:waterfall}
\end{figure}

\subsection{Validity diagnostics show that the experiment cannot be read as a clean independent-trials test}\label{subsec:results-validity}

The observed click split is 46.51\% Control and 53.49\% Test. Under a strict 50/50 click-level reference, this is an extreme sample ratio mismatch. But because the true allocation ratio and assignment unit are unknown, the result has two possible meanings. If assignment occurred before impressions, the imbalance may partly reflect the Test variant's higher click-through rate. If assignment occurred at the click or session level, the same imbalance would be stronger evidence of allocation or logging failure.

\begin{table}[!htbp]
\caption{Validity diagnostics for the aggregate dataset. SRM is reported under a baseline assumption of equal 50/50 allocation.}\label{tab:srm}
\small
\begin{tabular}{@{}L{0.34\textwidth}L{0.26\textwidth}L{0.30\textwidth}@{}}
\toprule
Diagnostic & Result & Interpretation\\
\midrule
Observed click split & 46.51\% / 53.49\% & Test has more observed clicks.\\
SRM under 50/50 reference & $\chi^2=1646.44$; \mbox{$p<10^{-30}$} & Extreme mismatch if 50/50 click allocation was intended.\\
A/A false-positive rate & 87.8\% at nominal 5\% & Control days do not behave like exchangeable experimental replicates.\\
KS test of A/A $p$-values & \mbox{$p<10^{-15}$} & A/A $p$-values are far from uniform.\\
\botrule
\end{tabular}
\end{table}

The A/A result should not be interpreted as evidence that one particular implementation of a conversion-rate test is universally invalid. It is more specific: when the available units are daily aggregates, random splits of days do not behave like repeated draws from the same experimental process. Day-of-week structure, campaign scheduling, spend variation, and unobserved traffic composition can all break exchangeability. The consequence is severe: the public data are useful for detecting that naive inference is fragile, but not for producing a final rollout verdict.

\begin{figure}[!htbp]
\centering
\includegraphics[width=0.72\textwidth]{figures/aa_simulation_pvalues.png}
\caption{A/A simulation using random splits of Control days.}\label{fig:aa}
\end{figure}

\subsection{Weekday patterns are hypothesis-generating only}\label{subsec:results-hte}

The weekday analysis shows sign reversals: the Test campaign's conversion rate is lower on some weekdays and higher on others. This is an important exploratory signal because it suggests that the aggregate average may be mixing different traffic regimes over time. However, the evidence is highly sparse. In this 30-day window, each weekday has only four or five paired observations, leading to extremely wide variance. 

Because of this sparsity, the weekday analysis is presented visually in Figure~\ref{fig:hte_wd} to highlight the uncertainty, rather than as a definitive calendar-based deployment rule. It does not justify a recommendation such as deploying the Test variant on Sunday or disabling it on Saturday. A valid temporal-deployment claim would require a new experiment that pre-registers weekday as a moderator, runs for a longer period, preserves the randomisation unit, and records traffic-source covariates.

\begin{figure}[!htbp]
\centering
\includegraphics[width=0.78\textwidth]{figures/hte_forest_weekday.png}
\caption{Weekday-level conversion-rate differences, Test minus Control.}\label{fig:hte_wd}
\end{figure}

\FloatBarrier
%==============================================================
\section{Discussion}\label{sec:discussion}
%==============================================================

\subsection{The strongest result is diagnostic, not causal}\label{subsec:disc-aggregate}

The revised interpretation is deliberately narrower than a conventional A/B testing report. The data do show that the Test variant has lower pooled purchase-per-click than Control. However, the same data also show that this conclusion depends strongly on treating clicks as independent trials. Since the dataset does not document whether clicks are the randomisation unit, the result is better understood as a diagnostic finding: under one common analysis model, the Test arm loses, but the public data do not contain enough design information to transform that descriptive loss into a confident causal rollout decision.

This distinction makes the paper more useful for methodology. A weak public dataset can still teach analysts what to check before making a product decision: exposure logging, allocation ratios, denominator definitions, temporal clustering, and post-treatment conditioning. The paper's value is therefore not in declaring a winner but in showing how quickly a winner-loser conclusion becomes unstable when those checks are made explicit.

\subsection{Why conditioning on clicks changes the meaning of funnel results}\label{subsec:disc-selection}

The most important interpretive change concerns the funnel. It is tempting to say that the Test variant ``creates mid-funnel friction'' because add-to-cart progression is lower. The revised manuscript avoids that claim. If the Test variant increases click-through rate, it may bring in a different mix of users. Some of these additional clickers may be curious, low-intent, or campaign-driven visitors. Lower downstream rates among that expanded clicker set would then be a compositional consequence of top-of-funnel expansion, not necessarily a defect in the checkout design.

This does not make funnel analysis useless. It makes it a source of hypotheses rather than proof of mechanism. A follow-up study should either randomise at the relevant funnel entry point, retain user/session identifiers, or use a compositional framework that explicitly accounts for selection into post-treatment stages. Without that, stage-level differences should be described as observed conditional differences rather than causal effects of specific page components.

\subsection{SRM and A/A simulation as warnings about the data structure}\label{subsec:disc-srm}

The SRM result is severe under a 50/50 click reference, but it is not self-interpreting. If the original allocation was 50/50 at the user level before impressions, then a click imbalance can arise because the Test variant produces more clicks. If allocation was intended at the click or session level, the same imbalance becomes evidence of a serious design or logging problem. Since the dataset does not tell us which scenario is true, the paper treats SRM as a warning about analysis-unit uncertainty rather than as a single definitive diagnosis.

The A/A simulation reaches a similar conclusion from a different angle. Splitting Control days produces far too many small $p$-values, but the cause is not simply a flawed formula. It is the non-exchangeability of daily aggregates. Days in an e-commerce campaign can differ by weekday, spend, traffic source, promotion, and external demand. Therefore, a day-level pseudo-experiment is not equivalent to repeated randomisation. This is precisely why public daily aggregates should be used cautiously for causal inference.

\subsection{Why pseudo-session uplift modelling is removed from the main evidence}\label{subsec:disc-uplift}

Earlier versions of this manuscript trained uplift meta-learners after expanding daily aggregates into pseudo-session observations. That section is removed from the main empirical argument. The reason is methodological: drawing Bernoulli outcomes from each day's observed conversion rate cannot create real individual-level heterogeneity. Any apparent uplift ranking would mostly rediscover the day-level and weekday-level patterns already encoded in the reconstruction process.

This change strengthens the paper. Instead of using a sophisticated model on unsuitable data, the revised analysis states what the data can support. Real uplift modelling would require actual user-level or session-level covariates, stable treatment assignment, pre-treatment features, and validation on a later experiment. Without those ingredients, pseudo-session uplift is best left as an appendix simulation or omitted entirely.

\subsection{Practical implications for analysts}\label{subsec:disc-practical}

For practitioners, the lesson is not that aggregate dashboards are useless. The lesson is that aggregate dashboards should trigger questions before they trigger deployment. A responsible checkout A/B test report should identify the randomisation unit, define every denominator, report SRM on the correct exposure unit, separate pre-treatment from post-treatment segments, account for temporal clustering, and avoid presenting exploratory subgroup patterns as action rules.

In this dataset, the safest product recommendation is therefore conservative. The Test variant should not be rolled out on the basis of the observed aggregate table. Nor should it be rejected as wholly uninformative. The observed patterns suggest a better follow-up experiment: preserve the randomisation unit, collect real session-level covariates, pre-specify the funnel metrics, run long enough to estimate weekday effects, and test whether the acquisition gain persists without a downstream compositional penalty.

\FloatBarrier
%==============================================================
\section{Limitations}\label{sec:limitations}
%==============================================================

This study has four main limitations. First, the dataset lacks the randomisation unit, intended allocation ratio, user identifiers, session boundaries, and traffic-source covariates. This prevents strong causal product conclusions. Second, the time window is short, so weekday patterns are unstable and may reflect ordinary campaign variation rather than treatment heterogeneity. Third, revenue is unavailable; any constant-average-order-value calculation would only rescale conversion rate and is therefore omitted from the main analysis. Fourth, because the data are aggregated by day and variant, individual-level uplift modelling is not appropriate as main evidence.

These limitations are not treated as afterthoughts. They are the reason for the paper's revised framing. The manuscript uses the dataset to demonstrate how to diagnose fragility in aggregate A/B testing data, not to claim a deployable campaign or checkout optimisation rule. To definitively resolve these structural ambiguities, future studies must collaborate with platform providers to obtain raw, session-level event logs rather than daily aggregates. Having access to unique session identifiers and explicit exposure timestamps would solve the unit-of-analysis paradox, allow for accurate clustered standard errors, and cleanly distinguish between true randomisation failures (SRM) and post-treatment click-through inflation.

\FloatBarrier
%==============================================================
\section{Conclusion}\label{sec:conclusion}
%==============================================================

This paper re-analysed a public dataset commonly presented as a checkout A/B test, but which fundamentally reflects a comparison of two aggregate marketing campaigns. The pooled click-level comparison suggests that the Test campaign yields lower conversion among clickers than Control. Yet this conclusion is no longer supported when the substantial daily overdispersion inherent to marketing campaigns, sample-ratio ambiguity, A/A non-exchangeability, and post-treatment funnel conditioning are taken into account.

The central conclusion is methodological. Daily aggregate datasets can reveal compositional confounding and generate hypotheses, but they cannot replace a properly logged, unit-level experiment. The observed overdispersion makes standard independent-trials inference inappropriate for causal interpretation. The most defensible next step is not an immediate rollout decision, but rather a cleaner follow-up experiment with documented randomisation, user/session identifiers, pre-specified funnel metrics, and robust statistical models that account for cluster-level noise.

\FloatBarrier
%==============================================================
\backmatter

\bmhead{Code and data availability}

All replication code for this re-analysis, along with the data processing pipelines and validity diagnostics, are available at \url{https://github.com/Dawn2310/Checkout-ab-validity-diagnostics}.

\bmhead{Acknowledgements}

The authors thank colleagues and reviewers for helpful feedback.

\section*{Declarations}
\begin{itemize}
\item \textbf{Funding}: not applicable.
\item \textbf{Conflict of interest}: the authors declare no competing interests.
\item \textbf{Data availability}: the dataset is publicly available on Kaggle (\url{https://www.kaggle.com/datasets/faviovaz/marketing-ab-testing}).
\item \textbf{Code availability}: replication code is available at \url{https://github.com/Dawn2310/Checkout-ab-validity-diagnostics}.
\item \textbf{Author contributions}: Nguyen Luong Hai Dang: conceptualisation, methodology, analysis, writing - original draft. Duong Quoc Huu: review and editing. Nguyen Thi Thanh Tien: review and editing.
\end{itemize}

\FloatBarrier
\begin{appendices}
\setcounter{figure}{0}
\renewcommand{\thefigure}{A\arabic{figure}}
\renewcommand{\theHfigure}{A\arabic{figure}}

\section{Supplementary diagnostics}\label{app:suppfigs}

The figures below are retained as supplementary diagnostics. They are not used to make additional causal claims.

\begin{figure}[!htbp]
\centering
\includegraphics[width=0.70\textwidth]{figures/bootstrap_uplift.png}
\caption{Supplementary bootstrap distribution of relative conversion-rate uplift over daily resamples.}\label{fig:bootstrap_app}
\end{figure}

\begin{figure}[!htbp]
\centering
\includegraphics[width=0.70\textwidth]{figures/cuped_adjustment.png}
\caption{Supplementary CUPED adjustment plot.}\label{fig:cuped_app}
\end{figure}

\end{appendices}

\bibliography{references}

\end{document}
