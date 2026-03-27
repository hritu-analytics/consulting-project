-- ============================================================================
-- MERIDIAN & PARTNERS: ENGAGEMENT PROFITABILITY & UTILISATION ANALYSIS
-- SQL Analysis Layer | Hrituparna Das
-- ============================================================================
-- Tools: PostgreSQL-style syntax
-- Key techniques: CTEs, Window Functions, Profitability Waterfall, Scenario Analysis
-- ============================================================================


-- ============================================================================
-- QUERY 1: PROFITABILITY WATERFALL — CONTRACTED vs ACTUAL BY PRACTICE AREA
-- Business Question: Where is margin leaking between contract and delivery?
-- ============================================================================

WITH practice_financials AS (
    SELECT
        practice_area,
        COUNT(*) AS engagements,
        ROUND(SUM(contracted_revenue_gbp), 0) AS total_revenue,
        ROUND(SUM(direct_cost_gbp), 0) AS total_direct_cost,
        ROUND(SUM(overhead_cost_gbp), 0) AS total_overhead,
        ROUND(SUM(contracted_margin_gbp), 0) AS contracted_margin,
        ROUND(SUM(actual_margin_gbp), 0) AS actual_margin,
        ROUND(AVG(contracted_margin_pct), 1) AS avg_contracted_margin_pct,
        ROUND(AVG(actual_margin_pct), 1) AS avg_actual_margin_pct,
        ROUND(AVG(scope_overrun_pct), 1) AS avg_scope_overrun
    FROM engagements
    GROUP BY practice_area
),

margin_erosion AS (
    SELECT
        *,
        contracted_margin - actual_margin AS margin_leaked_gbp,
        ROUND(
            (contracted_margin - actual_margin) * 100.0 /
            NULLIF(contracted_margin, 0), 1
        ) AS margin_erosion_pct,
        -- Rank practices by margin leakage
        RANK() OVER (ORDER BY (contracted_margin - actual_margin) DESC) AS leakage_rank
    FROM practice_financials
)

SELECT
    practice_area,
    engagements,
    total_revenue,
    total_direct_cost,
    total_overhead,
    contracted_margin,
    actual_margin,
    margin_leaked_gbp,
    avg_contracted_margin_pct,
    avg_actual_margin_pct,
    margin_erosion_pct,
    avg_scope_overrun,
    leakage_rank,
    -- Cumulative margin leakage across practices
    SUM(margin_leaked_gbp) OVER (
        ORDER BY (contracted_margin - actual_margin) DESC
        ROWS UNBOUNDED PRECEDING
    ) AS cumulative_leakage
FROM margin_erosion
ORDER BY margin_leaked_gbp DESC;


-- ============================================================================
-- QUERY 2: UTILISATION GAP ANALYSIS — REVENUE OPPORTUNITY BY LEVEL & PRACTICE
-- Business Question: What's the revenue impact of closing the utilisation gap?
-- ============================================================================

WITH monthly_util AS (
    SELECT
        u.practice_area,
        u.level,
        u.month,
        COUNT(DISTINCT u.consultant_id) AS headcount,
        ROUND(AVG(u.utilisation_pct), 1) AS avg_util,
        ROUND(AVG(u.utilisation_target_pct), 1) AS target_util,
        SUM(u.billable_hours) AS total_billable,
        SUM(u.bench_hours) AS total_bench,
        SUM(u.available_hours) AS total_available
    FROM utilisation u
    GROUP BY u.practice_area, u.level, u.month
),

util_gap AS (
    SELECT
        practice_area,
        level,
        COUNT(DISTINCT month) AS months_observed,
        ROUND(AVG(avg_util), 1) AS actual_util,
        ROUND(AVG(target_util), 1) AS target_util,
        ROUND(AVG(target_util) - AVG(avg_util), 1) AS util_gap_ppts,
        ROUND(AVG(headcount), 0) AS avg_headcount,
        ROUND(SUM(total_bench), 0) AS total_bench_hours
    FROM monthly_util
    GROUP BY practice_area, level
),

revenue_opportunity AS (
    SELECT
        g.*,
        c.avg_billing_rate,
        -- Revenue opportunity = gap hours × billing rate
        ROUND(
            g.total_bench_hours *
            (g.util_gap_ppts / NULLIF(100 - g.actual_util, 0)) *
            c.avg_billing_rate, 0
        ) AS revenue_opportunity_gbp,
        -- Rank by opportunity size
        ROW_NUMBER() OVER (
            ORDER BY g.total_bench_hours *
            (g.util_gap_ppts / NULLIF(100 - g.actual_util, 0)) *
            c.avg_billing_rate DESC
        ) AS opportunity_rank
    FROM util_gap g
    JOIN (
        SELECT practice_area, level,
               ROUND(AVG(billing_rate_gbp), 0) AS avg_billing_rate
        FROM consultants
        GROUP BY practice_area, level
    ) c ON g.practice_area = c.practice_area AND g.level = c.level
    WHERE g.util_gap_ppts > 0
)

SELECT
    practice_area,
    level,
    avg_headcount,
    actual_util,
    target_util,
    util_gap_ppts,
    total_bench_hours,
    avg_billing_rate,
    revenue_opportunity_gbp,
    opportunity_rank,
    -- Percentage of total firm opportunity
    ROUND(
        revenue_opportunity_gbp * 100.0 /
        SUM(revenue_opportunity_gbp) OVER (), 1
    ) AS pct_of_total_opportunity
FROM revenue_opportunity
WHERE revenue_opportunity_gbp > 0
ORDER BY revenue_opportunity_gbp DESC
LIMIT 20;


-- ============================================================================
-- QUERY 3: ENGAGEMENT PERFORMANCE SCORING — PARTNER DECISION MATRIX
-- Business Question: Which engagements should we expand, reprice, or exit?
-- ============================================================================

WITH engagement_scores AS (
    SELECT
        engagement_id,
        client_name,
        client_industry,
        engagement_type,
        practice_area,
        contracted_revenue_gbp,
        actual_margin_pct,
        scope_overrun_pct,
        client_satisfaction_score,
        is_repeat_client,
        duration_weeks,
        team_size,
        -- Normalised scores (0-100)
        NTILE(100) OVER (ORDER BY actual_margin_pct) AS margin_percentile,
        NTILE(100) OVER (ORDER BY client_satisfaction_score) AS satisfaction_percentile,
        NTILE(100) OVER (ORDER BY scope_overrun_pct DESC) AS efficiency_percentile,
        NTILE(100) OVER (ORDER BY contracted_revenue_gbp) AS revenue_percentile
    FROM engagements
),

scored AS (
    SELECT
        *,
        -- Composite score (weighted)
        ROUND(
            margin_percentile * 0.35 +
            satisfaction_percentile * 0.25 +
            efficiency_percentile * 0.25 +
            revenue_percentile * 0.15, 1
        ) AS composite_score
    FROM engagement_scores
),

actioned AS (
    SELECT
        *,
        CASE
            WHEN composite_score >= 75 AND is_repeat_client = 1 THEN 'EXPAND — Upsell & Extend'
            WHEN composite_score >= 75 THEN 'GROW — Convert to Retainer'
            WHEN composite_score >= 50 AND actual_margin_pct < 30 THEN 'REPRICE — Renegotiate Terms'
            WHEN composite_score >= 50 THEN 'MAINTAIN — Steady State'
            WHEN composite_score >= 25 AND scope_overrun_pct > 15 THEN 'FIX — Scope Management'
            WHEN composite_score < 25 THEN 'EXIT — Discontinue or Refer'
            ELSE 'REVIEW — Needs Assessment'
        END AS partner_action,
        -- Rank within practice for prioritisation
        ROW_NUMBER() OVER (
            PARTITION BY practice_area
            ORDER BY composite_score DESC
        ) AS practice_rank
    FROM scored
)

SELECT
    partner_action,
    COUNT(*) AS engagement_count,
    ROUND(SUM(contracted_revenue_gbp), 0) AS total_revenue,
    ROUND(AVG(actual_margin_pct), 1) AS avg_margin,
    ROUND(AVG(client_satisfaction_score), 1) AS avg_satisfaction,
    ROUND(AVG(scope_overrun_pct), 1) AS avg_overrun,
    ROUND(AVG(composite_score), 1) AS avg_composite_score,
    SUM(is_repeat_client) AS repeat_clients
FROM actioned
GROUP BY partner_action
ORDER BY
    CASE partner_action
        WHEN 'EXPAND — Upsell & Extend' THEN 1
        WHEN 'GROW — Convert to Retainer' THEN 2
        WHEN 'REPRICE — Renegotiate Terms' THEN 3
        WHEN 'MAINTAIN — Steady State' THEN 4
        WHEN 'FIX — Scope Management' THEN 5
        WHEN 'REVIEW — Needs Assessment' THEN 6
        WHEN 'EXIT — Discontinue or Refer' THEN 7
    END;


-- ============================================================================
-- QUERY 4: SCOPE CREEP FINANCIAL IMPACT — BY ENGAGEMENT TYPE & PRACTICE
-- Business Question: Where is scope creep costing us the most?
-- ============================================================================

WITH scope_analysis AS (
    SELECT
        engagement_type,
        practice_area,
        COUNT(*) AS engagements,
        ROUND(AVG(scope_overrun_pct), 1) AS avg_overrun_pct,
        ROUND(AVG(contracted_margin_pct), 1) AS avg_contracted_margin,
        ROUND(AVG(actual_margin_pct), 1) AS avg_actual_margin,
        ROUND(SUM(contracted_margin_gbp - actual_margin_gbp), 0) AS total_margin_eroded,
        ROUND(AVG(client_satisfaction_score), 1) AS avg_satisfaction
    FROM engagements
    GROUP BY engagement_type, practice_area
    HAVING COUNT(*) >= 3
),

ranked AS (
    SELECT
        *,
        avg_contracted_margin - avg_actual_margin AS margin_drop_ppts,
        -- Window: rank engagement types by total erosion within practice
        RANK() OVER (
            PARTITION BY practice_area
            ORDER BY total_margin_eroded DESC
        ) AS erosion_rank_in_practice,
        -- Window: running total of margin erosion across all types
        SUM(total_margin_eroded) OVER (
            ORDER BY total_margin_eroded DESC
            ROWS UNBOUNDED PRECEDING
        ) AS cumulative_erosion,
        -- Window: what % of practice's total erosion
        ROUND(
            total_margin_eroded * 100.0 /
            NULLIF(SUM(total_margin_eroded) OVER (PARTITION BY practice_area), 0), 1
        ) AS pct_of_practice_erosion
    FROM scope_analysis
)

SELECT *
FROM ranked
WHERE total_margin_eroded > 0
ORDER BY total_margin_eroded DESC
LIMIT 20;


-- ============================================================================
-- QUERY 5: SCENARIO ANALYSIS — UTILISATION IMPROVEMENT REVENUE IMPACT
-- Business Question: What if we close the utilisation gap to 75% firm-wide?
-- ============================================================================

WITH current_state AS (
    SELECT
        u.practice_area,
        u.level,
        COUNT(DISTINCT u.consultant_id) AS headcount,
        ROUND(AVG(u.utilisation_pct), 1) AS current_util,
        ROUND(AVG(u.utilisation_target_pct), 1) AS target_util,
        ROUND(AVG(c.billing_rate_gbp), 0) AS avg_bill_rate,
        ROUND(AVG(c.cost_rate_gbp), 0) AS avg_cost_rate,
        SUM(u.available_hours) AS total_available_hours,
        SUM(u.billable_hours) AS current_billable_hours
    FROM utilisation u
    JOIN consultants c ON u.consultant_id = c.consultant_id
    GROUP BY u.practice_area, u.level
),

scenarios AS (
    SELECT
        practice_area,
        level,
        headcount,
        current_util,
        target_util,
        avg_bill_rate,
        avg_cost_rate,
        total_available_hours,
        current_billable_hours,
        -- Scenario 1: Close to 73% (conservative)
        ROUND(total_available_hours * 0.73 - current_billable_hours, 0) AS s1_additional_hours,
        ROUND((total_available_hours * 0.73 - current_billable_hours) * avg_bill_rate, 0) AS s1_additional_revenue,
        ROUND((total_available_hours * 0.73 - current_billable_hours) * (avg_bill_rate - avg_cost_rate), 0) AS s1_additional_margin,
        -- Scenario 2: Close to 75% (target)
        ROUND(total_available_hours * 0.75 - current_billable_hours, 0) AS s2_additional_hours,
        ROUND((total_available_hours * 0.75 - current_billable_hours) * avg_bill_rate, 0) AS s2_additional_revenue,
        ROUND((total_available_hours * 0.75 - current_billable_hours) * (avg_bill_rate - avg_cost_rate), 0) AS s2_additional_margin,
        -- Scenario 3: Stretch to 78% (aggressive)
        ROUND(total_available_hours * 0.78 - current_billable_hours, 0) AS s3_additional_hours,
        ROUND((total_available_hours * 0.78 - current_billable_hours) * avg_bill_rate, 0) AS s3_additional_revenue,
        ROUND((total_available_hours * 0.78 - current_billable_hours) * (avg_bill_rate - avg_cost_rate), 0) AS s3_additional_margin
    FROM current_state
    WHERE current_util < 75
)

SELECT
    practice_area,
    SUM(headcount) AS underutilised_headcount,
    ROUND(AVG(current_util), 1) AS avg_current_util,
    -- Scenario summaries
    SUM(s1_additional_revenue) AS conservative_revenue_uplift,
    SUM(s1_additional_margin) AS conservative_margin_uplift,
    SUM(s2_additional_revenue) AS target_revenue_uplift,
    SUM(s2_additional_margin) AS target_margin_uplift,
    SUM(s3_additional_revenue) AS stretch_revenue_uplift,
    SUM(s3_additional_margin) AS stretch_margin_uplift
FROM scenarios
WHERE s2_additional_hours > 0
GROUP BY practice_area
ORDER BY SUM(s2_additional_revenue) DESC;
