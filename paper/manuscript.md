What Can Be Learned from a Daily-Aggregate Checkout A/B
Test? Validity Diagnostics, Funnel Decomposition, and Limits of
Causal Interpretation
Nguyen Luong Hai Dang1*, Duong Quoc Huu1 and Nguyen Thi Thanh Tien1
1*Faculty of Artificial Intelligence, FPT University, Vietnam.
*Corresponding author(s). E-mail(s): nguyenluonghaidang2006pq@gmail.com;
Abstract
This study re-analyses a public daily-aggregate e-commerce A/B testing dataset for a checkout-page redesign.
The paper is framed as a methodological caution rather than as a direct product-deployment recommendation. The dataset contains large click counts but only paired daily aggregates and lacks documentation
of the randomisation unit, intended allocation ratio, user identifiers, traffic-source composition, and session
boundaries. These missing design details make a naive causal interpretation unsafe. We combine aggregate conversion-rate comparison with day-level robustness checks, sample-ratio-mismatch diagnostics, A/A
simulation, CUPED sensitivity analysis, funnel-stage decomposition, and exploratory weekday heterogeneity analysis. The click-pooled comparison suggests that the Test variant has lower overall conversion than
Control, but this result weakens when calendar days are treated as the effective unit of variation. Funnel
decomposition also reveals an acquisition–conversion contrast: the Test variant generates more clicks but
has lower downstream progression among clickers. This pattern cannot be interpreted as direct evidence of
checkout friction because conditioning on clicks and later funnel stages introduces post-treatment selection.
Validity diagnostics further show that the observed data structure is incompatible with a simple independenttrials analysis. The main contribution is therefore diagnostic: daily aggregate A/B datasets can be useful for
detecting fragility, compositional confounding, and analysis-unit ambiguity, but they cannot by themselves
support confident causal rollout decisions.
Keywords: A/B testing, Conversion rate optimisation, Checkout-page design, Sample ratio mismatch, Funnel
decomposition, Heterogeneous treatment effects, Aggregate data, E-commerce
1 Introduction
Checkout-page redesigns are often evaluated with online controlled experiments because small design changes can
affect whether a visitor reaches the cart, completes payment, or abandons the site. In a well-instrumented A/B
test, the analyst knows the exposure unit, the randomisation scheme, the allocation ratio, and the relationship
between users, sessions, clicks, and purchases. Under those conditions, a conversion-rate comparison can support
a relatively direct product decision [1, 2].
Public A/B testing datasets are rarely this complete. They often provide only aggregate counts by day
and variant. Such data can still be useful, but their evidential role changes. Instead of asking only whether
variant A or B wins, the more defensible question is what the aggregate data can and cannot support. A
large denominator may produce a very small p-value, but that denominator may not represent the number of
independent experimental units. A funnel table may show different rates at different stages, but conditional
rates after a treatment-affected click can reflect compositional selection rather than stage-specific design effects.
A subgroup analysis may show sign reversals, but a month of daily rows is too short to establish stable temporal
heterogeneity.
This paper re-analyses a public checkout-page A/B testing dataset from this more cautious perspective. The
dataset has one Control row and one Test row per day over a short calendar window. It reports impressions,
clicks, view-content events, add-to-cart events, purchases, and campaign spend. It does not report user identifiers,
the randomisation unit, the intended allocation ratio, or session-level covariates. These omissions are not minor
1
metadata issues. They determine whether clicks can be treated as independent trials, whether sample-ratio
mismatch is a randomisation failure or a treatment effect on click-through, and whether downstream funnel
rates can be given a causal interpretation.
We address three research questions:
RQ1 What does the aggregate conversion comparison show, and how does the conclusion change when the analysis
unit shifts from clicks to days?
RQ2 What do sample-ratio-mismatch diagnostics and A/A simulation reveal about the reliability of naive inference
on this aggregate dataset?
RQ3 What patterns appear in funnel-stage and weekday analyses, and which parts of those patterns are descriptive
rather than causal?
The contribution of the paper is not a claim that the redesigned checkout should be deployed or rejected.
Rather, the contribution is a structured diagnostic reading of a poorly documented aggregate experiment.
The analysis shows how an apparently decisive pooled conversion-rate result becomes fragile once the analyst
accounts for design ambiguity, time aggregation, post-treatment selection into clicks, and sparse subgroup
evidence. This reframing turns the dataset from a simple conversion-rate exercise into a case study on the limits
of causal interpretation in public A/B testing data.
2 Related Work
2.1 Online controlled experiments
Online controlled experiments are the standard empirical framework for evaluating digital product changes.
The core literature emphasises that credible experimentation requires more than a comparison of two observed
rates. Analysts must define the randomisation unit, track exposure consistently, pre-specify primary metrics,
handle ratio metrics appropriately, and diagnose validity problems such as sample ratio mismatch [1–4]. These
concerns are especially important when public datasets contain only aggregate summaries, because the analyst
cannot verify whether the available denominator is the same as the experimental unit.
2.2 Ratio metrics, variance reduction, and diagnostics
Conversion rate is a ratio metric. Its numerator and denominator may vary together over time, across campaigns,
or across traffic sources. For this reason, a test that treats every click as an independent Bernoulli trial can be
misleading when the data are temporally aggregated. Delta-method approaches for ratio metrics and variancereduction methods such as CUPED are designed to address some of these challenges when suitable pre-treatment
covariates are available [5, 6]. However, these methods cannot recover missing experimental-design information.
They can reduce variance or clarify uncertainty, but they cannot identify the randomisation unit after it has
been discarded from the data.
Sample ratio mismatch is another central diagnostic. In a clean randomised experiment, observed exposure
counts should be compatible with the intended allocation ratio. A mismatch may indicate allocation failure,
logging errors, bot filtering, or inconsistent inclusion rules [2, 4]. In the present dataset, the intended allocation
ratio is not known and the mismatch is measured on clicks, not on documented randomised users. The SRM
result must therefore be interpreted as an ambiguity diagnostic, not as automatic proof of broken randomisation.
2.3 Funnel analysis and post-treatment selection
Funnel analysis is useful because product interventions often affect different stages in different directions. A
checkout redesign may change attention, product inspection, cart formation, and purchase completion separately.
Prior studies on cart abandonment and checkout experience motivate this stage-wise perspective [7–10].
At the same time, funnel rates are not automatically causal stage effects. If treatment changes the probability
of clicking, then the set of users who click under Test may differ from the set who click under Control. Any later
rate conditioned on clickers is then affected by post-treatment selection. A lower add-to-cart rate among Test
clickers may reflect lower purchase intent among the additional clickers attracted by the design, not necessarily
a defect in the cart step itself. This is the key causal distinction that the present paper makes explicit.
2.4 Heterogeneous effects under sparse aggregate data
Heterogeneous treatment-effect analysis asks whether the average effect hides subgroup-level reversals. Prior
work discusses the value of subgroup analysis as well as the risk of false discoveries when many segment comparisons are explored [11, 12]. Uplift modelling extends this idea to individual-level targeting [13–15]. However,
uplift modelling requires real unit-level covariates and outcomes. Reconstructing pseudo-sessions from daily
2
rates cannot create genuine within-day individual heterogeneity. For that reason, this revised analysis does not
use pseudo-session uplift scores as evidence for deployment. It treats the weekday patterns only as exploratory
descriptive signals.
3 Data and Design Ambiguity
3.1 Observed data
The dataset contains 60 daily campaign records from 1–30 August 2019: one Control row and one Test row for
each day. The Control condition represents the existing checkout experience, and the Test condition represents
a redesigned checkout page. Each row includes aggregate counts for spend, impressions, reach, clicks, searches,
view-content events, add-to-cart events, and purchases. One Control row on 5 August 2019 has missing count
fields and is imputed by forward fill.
Revenue is not observed. Earlier versions of this manuscript used a constant assumed average order value to
compute revenue per session. That metric is removed from the main analysis because a constant average order
value merely rescales conversion rate and can misleadingly appear to add independent evidence. We therefore
analyse observed count and rate metrics only.
Table 1 Observed aggregate counts and derived
rates per variant. Spend is campaign spend, not
observed purchase revenue.
Quantity Control Test
Impressions 3 250 111 2 237 544
Clicks 157 368 180 970
View-content events 57 352 55 740
Add-to-cart events 38 883 26 446
Purchases 15 501 15 637
Spend (USD) 68 653 76 892
Click-through rate 4.84 % 8.09 %
View-content per click 36.44 % 30.80 %
Add-to-cart per view-content 67.80 % 47.45 %
Purchase per click 9.85 % 8.64 %
3.2 Design ambiguity as an analysis constraint
The dataset lacks the design metadata needed for a complete causal evaluation. Table 2 states how each missing
item limits the claims that can be made. This table is central to the revised manuscript because it prevents the
empirical sections from overstating what the public aggregate data can prove.
Table 2 Missing design metadata and the resulting claim boundary.
Missing information Why it matters Claim boundary used in this paper
Randomisation unit Determines whether clicks, sessions,
users, campaigns, or days are
independent experimental units.
Click-pooled tests are descriptive and
are not treated as definitive causal
inference.
Intended allocation ratio Required for a formal SRM pass/fail
interpretation.
SRM is interpreted as an ambiguity
warning, with sensitivity to plausible
reference splits.
User/session identifiers Needed to separate repeated behaviour
from independent observations.
No individual-level targeting or userlevel causal heterogeneity is claimed.
Traffic-source and device
mix
Needed to distinguish treatment effects
from compositional changes in the
audience.
Funnel and weekday patterns are
treated as hypotheses, not
deployment rules.
Pre-treatment covariates Needed for strong CUPED adjustment
and robust uplift modelling.
CUPED is a sensitivity check only;
pseudo-session uplift is not used as
main evidence.
3
4 Methodology
4.1 Metrics and denominators
The primary observed outcome is conversion rate among clickers:
CR = purchases
clicks . (1)
This denominator is analytically convenient but causally delicate because clicks can be affected by treatment.
Therefore, later funnel rates are interpreted as conditional descriptive rates, not as clean stage-specific treatment
effects.
Table 3 Funnel metric definitions. Explicit denominators are reported to avoid ambiguity in conditional-rate interpretation.
Metric Definition Interpretation caveat
Click-through rate Clicks / impressions Can be directly affected by the variant
and changes who enters later stages.
View-content per click View-content events / clicks Conditional on post-treatment clickers;
affected by clicker composition.
Add-to-cart per view-content Add-to-cart events /
view-content events
Conditional on users who already reached
a later stage.
Purchase given add-to-cart Purchases / add-to-cart events Conditional on cart formation; not
comparable to overall conversion.
Overall conversion rate Purchases / clicks Primary descriptive outcome among
clickers, but not necessarily a user-level
causal effect.
4.2 Aggregate and day-level inference
We report the click-pooled two-proportion Z-test because it is the standard first analysis for a binary conversion
outcome. However, we do not treat it as sufficient. We also report Welch’s t-test and Mann–Whitney tests on
daily conversion rates, and bootstrap intervals over daily resamples [16]. The purpose of presenting both views is
to expose the analysis-unit tension: clicks create a large denominator, whereas days represent the only replicated
units directly visible in the public data.
For ratio metrics, the relevant day-level uncertainty can be expressed through the delta method. If Nd
denotes purchases and Dd denotes clicks on day d, the rate is R = N/D. A first-order approximation is

\widehat{\operatorname{Var}}(\hat{R}) \approx \frac{1}{\overline{D}^{2}} \widehat{\operatorname{Var}}(N_{d} - \hat{R}D_{d}), (2)

which highlights that variation in the numerator and denominator should be considered jointly [6]. With only
daily aggregates, this approximation is informative but still cannot replace the missing randomisation unit.
4.3 Validity diagnostics
We examine sample ratio mismatch under several reference allocations rather than only a 50/50 split:
χ
2
SRM =
X
a∈{C,T}
(na − npa)
2
npa
. (3)
Here, na is the observed click count in arm a, and pa is a reference allocation share. Because the true allocation
is unavailable, the result is not a definitive randomisation-failure test. It is a sensitivity analysis showing which
allocation assumptions would make the observed click split surprising.
We also run an A/A simulation by repeatedly splitting Control days into pseudo-arms and applying the
same testing logic. This is not interpreted as proof that a specific Z-test is universally miscalibrated. Instead,
it diagnoses whether the daily aggregate structure behaves like exchangeable experimental replicates. A highly
non-uniform A/A p-value distribution indicates that daily rows are not a reliable basis for replicated causal
inference.
4
4.4 Funnel and heterogeneity analysis
Funnel-stage comparisons are computed with two-proportion tests and Holm correction. The tests are reported
because they reveal where observed rates differ, but the interpretation is deliberately cautious. Since clickers
and later-stage users are post-treatment subsets, a stage difference can reflect a change in user composition
rather than a direct effect of the redesigned checkout component.
Weekday heterogeneity is analysed descriptively by pooling clicks within weekday labels and comparing
Control and Test conversion rates. The dataset covers only one month, so each weekday has only four or five
paired daily observations. For this reason, weekday results are used to motivate follow-up hypotheses rather
than specific day-of-week deployment recommendations.
CUPED is included only as a sensitivity check. The available pre-period information is weak and aggregate,
so a small variance reduction is interpreted as a limitation of the dataset rather than as evidence against the
method [5].
5 Results
5.1 Aggregate conversion suggests a Test loss, but only under a click-level view
At the click-pooled level, the Test variant has a lower purchase-per-click rate than the Control variant: 8.64 %
compared with 9.85 %. The absolute difference is about −1.21 percentage points. If each click is treated as an
independent Bernoulli trial, the result is highly statistically significant. That conclusion is technically correct
under the click-level model, but the model is not guaranteed by the dataset.
Table 4 Click-pooled conversion comparison for overall
purchases per click.
Quantity Result
CR Control 9.8502 % (Wilson 95% CI: 9.70–9.99%)
CR Test 8.6407 % (Wilson 95% CI: 8.51–8.77%)
Absolute CR difference −1.21 percentage points
Relative CR difference −12.28 %
Two-proportion Z −12.139; p < 10−30
χ
2 on 2 × 2 table 147.21; df = 1; p < 10−30
The key analytical point is that the table does not settle the product question. The visible independent
records in the public dataset are days, not individual randomised users. Once the analysis moves from pooled
clicks to daily variation, the apparent certainty falls sharply.
Table 5 Day-level robustness and sensitivity checks. These results describe uncertainty when days, rather than clicks, are
treated as the visible repeated units.
Check Result Interpretation
Daily Welch t-test t = −1.518; p = 0.135 The daily-rate difference is not
significant at the 5% level.
Mann–Whitney U U = 375; p = 0.271 Daily rank evidence is weak.
Cohen’s d on daily CR −0.392 The daily effect is small to moderate.
Bootstrap CI for relative uplift [−32.19%, +12.71%] The daily-resampled interval crosses
zero.
CUPED variance reduction 1.04 % Available aggregate covariates provide
little variance reduction.
This contrast is the first main finding. The dataset supports a descriptive statement that the Test arm has
lower pooled conversion among clickers. It does not support a high-confidence causal claim that the redesign
would lower user-level purchase probability under clean randomisation.
5.2 Funnel decomposition reveals a compositional puzzle, not a direct mechanism
The funnel analysis reveals why the aggregate result is difficult to interpret. The Test variant has a much higher
click-through rate, but lower view-content and add-to-cart progression among the users who enter the funnel.
Among users who reach the cart, the Test arm has a higher purchase-given-cart rate. A superficial reading
would say that the redesign improves attraction and late purchase completion but damages the middle of the
funnel. The more rigorous reading is weaker and more useful: the redesign changes the composition of the users
observed at each conditional stage.
5
Fig. 1 Overall conversion rate per variant with Wilson 95% confidence intervals.
Table 6 Funnel-stage differences with explicit interpretation limits. Tests use two-proportion comparisons with
Holm correction.
Funnel step Control Test Relative diff. pHolm Interpretation limit
CTR 4.84% 8.09% +67.0% < 10−30 Pre-click comparison over
impressions.
View-content per click 36.44% 30.80% −15.5% < 10−30 Conditional on clickers.
Add-to-cart per
view-content
67.80% 47.45% −30.0% < 10−30 Conditional on viewers.
Purchase given add-to-cart 39.87% 59.13% +48.3% < 10−30 Conditional on cart users.
Overall purchase per click 9.85% 8.64% −12.3% < 10−30 Clicker-level descriptive
outcome.
The observed pattern is consistent with at least two different stories. One story is a design-mechanism story:
the Test page attracts attention but introduces friction before cart formation. Another story is a selection story:
the Test page attracts additional lower-intent clickers, so the conditional mid-funnel rates decline even if the
checkout mechanics are not worse. The aggregate dataset cannot distinguish these stories. This is why the paper
treats funnel decomposition as diagnostic exploration rather than causal mechanism identification.
Fig. 2 Relative differences by funnel step, Test versus Control.
6
5.3 Validity diagnostics show that the experiment cannot be read as a clean
independent-trials test
The observed click split is 46.51% Control and 53.49% Test. Under a strict 50/50 click-level reference, this is
an extreme sample ratio mismatch. But because the true allocation ratio and assignment unit are unknown,
the result has two possible meanings. If assignment occurred before impressions, the imbalance may partly
reflect the Test variant’s higher click-through rate. If assignment occurred at the click or session level, the same
imbalance would be stronger evidence of allocation or logging failure.
Table 7 Validity diagnostics for the aggregate dataset. SRM is reported under a baseline assumption of equal 50/50 allocation.
Diagnostic Result Interpretation
Observed click split 46.51% / 53.49% Test has more observed clicks.
SRM under 50/50 reference χ
2 = 1646.44; p < 10−30 Extreme mismatch if 50/50 click
allocation was intended.
A/A false-positive rate 87.8% at nominal 5% Control days do not behave like
exchangeable experimental
replicates.
KS test of A/A p-values p < 10−15 A/A p-values are far from uniform.
The A/A result should not be interpreted as evidence that one particular implementation of a conversionrate test is universally invalid. It is more specific: when the available units are daily aggregates, random splits of
days do not behave like repeated draws from the same experimental process. Day-of-week structure, campaign
scheduling, spend variation, and unobserved traffic composition can all break exchangeability. The consequence
is severe: the public data are useful for detecting that naive inference is fragile, but not for producing a final
rollout verdict.
Fig. 3 A/A simulation using random splits of Control days.
5.4 Weekday patterns are hypothesis-generating only
The weekday analysis shows sign reversals: the Test arm is lower on some weekdays and higher on others.
This is an important exploratory signal because it suggests that the aggregate average may be mixing different
traffic regimes. However, the evidence is sparse. In this 30-day window, each weekday has only four or five
paired observations. Therefore, the table should be read as a map of possible heterogeneity, not as a reliable
calendar-based deployment rule.
The weekday table is useful because it tells the analyst where to look next. It does not justify a recommendation such as deploying the Test variant on Sunday or disabling it on Saturday. A valid temporal-deployment
7
Table 8 Exploratory weekday heterogeneity. Counts of matched days are shown to make the small effective
sample size explicit.
Weekday Matched days CR Control CR Test Relative diff. Interpretation
Monday 4 12.68% 8.89% −29.9% Negative signal; sparse
evidence.
Tuesday 4 13.45% 10.17% −24.4% Negative signal; sparse
evidence.
Wednesday 4 14.26% 10.06% −29.5% Negative signal; sparse
evidence.
Thursday 5 6.35% 7.46% +17.6% Positive signal; needs
replication.
Friday 5 10.09% 10.46% +3.7% Weak positive signal.
Saturday 4 9.81% 4.38% −55.4% Large negative signal;
unstable with four days.
Sunday 4 6.36% 10.37% +63.0% Large positive signal;
unstable with four days.
claim would require a new experiment that pre-registers weekday as a moderator, runs for a longer period,
preserves the randomisation unit, and records traffic-source and device covariates.
Fig. 4 Weekday-level conversion-rate differences, Test minus Control.
6 Discussion
6.1 The strongest result is diagnostic, not causal
The revised interpretation is deliberately narrower than a conventional A/B testing report. The data do show
that the Test variant has lower pooled purchase-per-click than Control. However, the same data also show that
this conclusion depends strongly on treating clicks as independent trials. Since the dataset does not document
whether clicks are the randomisation unit, the result is better understood as a diagnostic finding: under one
common analysis model, the Test arm loses, but the public data do not contain enough design information to
transform that descriptive loss into a confident causal rollout decision.
This distinction makes the paper more useful for methodology. A weak public dataset can still teach analysts
what to check before making a product decision: exposure logging, allocation ratios, denominator definitions,
temporal clustering, and post-treatment conditioning. The paper’s value is therefore not in declaring a winner
but in showing how quickly a winner-loser conclusion becomes unstable when those checks are made explicit.
6.2 Why conditioning on clicks changes the meaning of funnel results
The most important interpretive change concerns the funnel. It is tempting to say that the Test variant “creates
mid-funnel friction” because add-to-cart progression is lower. The revised manuscript avoids that claim. If the
Test variant increases click-through rate, it may bring in a different mix of users. Some of these additional
8
clickers may be curious, low-intent, or campaign-driven visitors. Lower downstream rates among that expanded
clicker set would then be a compositional consequence of top-of-funnel expansion, not necessarily a defect in
the checkout design.
This does not make funnel analysis useless. It makes it a source of hypotheses rather than proof of mechanism.
A follow-up study should either randomise at the relevant funnel entry point, retain user/session identifiers,
or use a compositional framework that explicitly accounts for selection into post-treatment stages. Without
that, stage-level differences should be described as observed conditional differences rather than causal effects of
specific page components.
6.3 SRM and A/A simulation as warnings about the data structure
The SRM result is severe under a 50/50 click reference, but it is not self-interpreting. If the original allocation
was 50/50 at the user level before impressions, then a click imbalance can arise because the Test variant produces
more clicks. If allocation was intended at the click or session level, the same imbalance becomes evidence of a
serious design or logging problem. Since the dataset does not tell us which scenario is true, the paper treats
SRM as a warning about analysis-unit uncertainty rather than as a single definitive diagnosis.
The A/A simulation reaches a similar conclusion from a different angle. Splitting Control days produces
far too many small p-values, but the cause is not simply a flawed formula. It is the non-exchangeability of
daily aggregates. Days in an e-commerce campaign can differ by weekday, spend, traffic source, promotion, and
external demand. Therefore, a day-level pseudo-experiment is not equivalent to repeated randomisation. This
is precisely why public daily aggregates should be used cautiously for causal inference.
6.4 Why pseudo-session uplift modelling is removed from the main evidence
Earlier versions of this manuscript trained uplift meta-learners after expanding daily aggregates into pseudosession observations. That section is removed from the main empirical argument. The reason is methodological:
drawing Bernoulli outcomes from each day’s observed conversion rate cannot create real individual-level heterogeneity. Any apparent uplift ranking would mostly rediscover the day-level and weekday-level patterns already
encoded in the reconstruction process.
This change strengthens the paper. Instead of using a sophisticated model on unsuitable data, the revised
analysis states what the data can support. Real uplift modelling would require actual user-level or session-level
covariates, stable treatment assignment, pre-treatment features, and validation on a later experiment. Without
those ingredients, pseudo-session uplift is best left as an appendix simulation or omitted entirely.
6.5 Practical implications for analysts
For practitioners, the lesson is not that aggregate dashboards are useless. The lesson is that aggregate dashboards
should trigger questions before they trigger deployment. A responsible checkout A/B test report should identify
the randomisation unit, define every denominator, report SRM on the correct exposure unit, separate pretreatment from post-treatment segments, account for temporal clustering, and avoid presenting exploratory
subgroup patterns as action rules.
In this dataset, the safest product recommendation is therefore conservative. The Test variant should not be
rolled out on the basis of the observed aggregate table. Nor should it be rejected as wholly uninformative. The
observed patterns suggest a better follow-up experiment: preserve the randomisation unit, collect real sessionlevel covariates, pre-specify the funnel metrics, run long enough to estimate weekday effects, and test whether
the acquisition gain persists without a downstream compositional penalty.
7 Limitations
This study has four main limitations. First, the dataset lacks the randomisation unit, intended allocation
ratio, user identifiers, session boundaries, and traffic-source covariates. This prevents strong causal product
conclusions. Second, the time window is short, so weekday patterns are unstable and may reflect ordinary
campaign variation rather than treatment heterogeneity. Third, revenue is unavailable; any constant-averageorder-value calculation would only rescale conversion rate and is therefore omitted from the main analysis.
Fourth, because the data are aggregated by day and variant, individual-level uplift modelling is not appropriate
as main evidence.
These limitations are not treated as afterthoughts. They are the reason for the paper’s revised framing. The
manuscript uses the dataset to demonstrate how to diagnose fragility in aggregate A/B testing data, not to
claim a deployable checkout optimisation rule. To definitively resolve these structural ambiguities, future studies must collaborate with platform providers to obtain raw, session-level event logs rather than daily aggregates. Having access to unique session identifiers and explicit exposure timestamps would solve the unit-of-analysis paradox, allow for accurate clustered standard errors, and cleanly distinguish between true randomisation failures (SRM) and post-treatment click-through inflation.
9
8 Conclusion
This paper re-analysed a public checkout-page A/B testing dataset as a case study in validity diagnostics and
cautious interpretation. The pooled click-level comparison suggests that the Test variant has lower purchaseper-click than Control. Yet this conclusion weakens when daily variation, sample-ratio ambiguity, A/A nonexchangeability, and post-treatment funnel conditioning are taken seriously.
The central conclusion is methodological. Daily aggregate A/B datasets can reveal warning signs and generate
hypotheses, but they cannot replace a properly logged experiment. The most defensible next step is not an
immediate rollout decision. It is a cleaner follow-up experiment with documented randomisation, user/session
identifiers, pre-specified funnel metrics, and enough duration to evaluate temporal heterogeneity.
Code and data availability. All code and data references should be provided in the final submission repository. The current manuscript uses a public aggregate dataset and should include the exact dataset URL before
submission.
Acknowledgements. The authors thank colleagues and reviewers for helpful feedback.
Declarations
• Funding: not applicable.
• Conflict of interest: the authors declare no competing interests.
• Data availability: the dataset is publicly available; the exact URL should be inserted before submission.
• Code availability: the repository URL should be inserted before submission.
• Author contributions: Nguyen Luong Hai Dang: conceptualisation, methodology, analysis, writing - original
draft. Duong Quoc Huu: review and editing. Nguyen Thi Thanh Tien: review and editing. These roles should
be confirmed before submission.
Appendix A Supplementary diagnostics
The figures below are retained as supplementary diagnostics. They are not used to make additional causal claims.
Fig. A1 Supplementary bootstrap distribution of relative conversion-rate uplift over daily resamples.
References
[1] Kohavi, R., Longbotham, R., Sommerfield, D., Henne, R.M.: Controlled experiments on the web: survey
and practical guide. Data Mining and Knowledge Discovery 18(1), 140–181 (2009).
[2] Kohavi, R., Tang, D., Xu, Y.: Trustworthy Online Controlled Experiments: A Practical Guide to A/B
Testing. Cambridge University Press, Cambridge, United Kingdom (2020)
[3] Kohavi, R., Deng, A., Frasca, B., Walker, T., Xu, Y., Pohlmann, N.: Online controlled experiments at large
scale. In: Proceedings of the 19th ACM SIGKDD, pp. 1168–1176 (2013)
10
Fig. A2 Supplementary CUPED adjustment plot.
[4] Larsen, N., Stallrich, J., Sengupta, S., Deng, A., Kohavi, R., Stevens, N.T.: Statistical challenges in online
controlled experiments: A review of a/b testing methodology. The American Statistician (2024).
[5] Deng, A., Xu, Y., Kohavi, R., Walker, T.: Improving the sensitivity of online controlled experiments by
utilizing pre-experiment data. In: Proceedings of the Sixth ACM International Conference on Web Search
and Data Mining, pp. 123–132 (2013)
[6] Deng, A., Knoblich, U., Lu, J.: Applying the delta method in metric analytics. In: KDD (2018)
[7] Kukar-Kinney, M., Close, A.G.: The determinants of consumers’ online shopping cart abandonment. Journal
of the Academy of Marketing Science 38(2), 240–250 (2010).
[8] Huang, G.H., Korfiatis, N., Chang, C.T.: Mobile shopping cart-checkout abandonment: A configurational
perspective. Journal of Retailing and Consumer Services (2018).
[9] McDowell, W.C., Wilson, R.C., Kile, C.O.: An examination of retail website design and conversion rate.
Journal of Business Research (2016).
[10] Bleier, A., Harmeling, C.M., Palmatier, R.W.: Creating effective online customer experiences. Journal of
Marketing (2019).
[11] Taddy, M., Gardner, M., Chen, L., Draper, D.: A nonparametric bayesian analysis of heterogeneous
treatment effects in digital experimentation. Journal of Business & Economic Statistics (2016).
[12] Yu, M., Sun, W., Kreager, D.: False discovery rate controlled heterogeneous treatment effect detection for
online controlled experiments. In: KDD (2018)
[13] Devriendt, F., Moldovan, D., Verbeke, W.: A literature survey and experimental evaluation of the stateof-the-art in uplift modeling. Big Data (2018).
[14] Gubela, R.M., Lessmann, S., Jaroszewicz, S.: Response transformation and profit decomposition for revenue
uplift modeling. European Journal of Operational Research (2020).
[15] Athey, S., Imbens, G.W.: Machine learning methods that economists should know about. Annual Review
of Economics (2019).
[16] Davison, A.C., Hinkley, D.V.: Bootstrap Methods and Their Application. Cambridge University Press,
Cambridge, United Kingdom (1997)
11