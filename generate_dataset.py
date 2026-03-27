"""
MERIDIAN & PARTNERS — Consulting Engagement Dataset Generator
==============================================================
Generates a realistic dataset simulating a mid-size management consulting firm
with ~320 consultants across 5 practice areas, 480 engagements over 2 years.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

np.random.seed(2024)
random.seed(2024)

# ── FIRM STRUCTURE ────────────────────────────────────────────────────────────

practice_areas = {
    "Strategy & Growth": {"headcount": 52, "avg_bill_rate": 285, "margin_target": 0.42},
    "Technology & Digital": {"headcount": 78, "avg_bill_rate": 260, "margin_target": 0.38},
    "Operations & Supply Chain": {"headcount": 65, "avg_bill_rate": 240, "margin_target": 0.35},
    "Financial Advisory": {"headcount": 58, "avg_bill_rate": 275, "margin_target": 0.40},
    "People & Organisation": {"headcount": 68, "avg_bill_rate": 230, "margin_target": 0.33},
}

levels = {
    "Partner": {"pct": 0.08, "bill_mult": 1.80, "cost_mult": 1.60, "util_target": 0.45},
    "Director": {"pct": 0.12, "bill_mult": 1.45, "cost_mult": 1.30, "util_target": 0.55},
    "Senior Manager": {"pct": 0.15, "bill_mult": 1.20, "cost_mult": 1.10, "util_target": 0.65},
    "Manager": {"pct": 0.20, "bill_mult": 1.00, "cost_mult": 0.85, "util_target": 0.75},
    "Senior Consultant": {"pct": 0.22, "bill_mult": 0.80, "cost_mult": 0.65, "util_target": 0.80},
    "Consultant": {"pct": 0.23, "bill_mult": 0.60, "cost_mult": 0.48, "util_target": 0.85},
}

regions = ["London", "Manchester", "Edinburgh", "Birmingham", "Bristol"]
client_industries = [
    "Financial Services", "Technology", "Healthcare & Pharma",
    "Energy & Utilities", "Retail & Consumer", "Public Sector",
    "Manufacturing", "Telecommunications"
]

engagement_types = [
    "Strategic Review", "Digital Transformation", "Cost Reduction",
    "M&A Due Diligence", "Operating Model Design", "Market Entry",
    "Workforce Transformation", "Process Optimisation", "Data Strategy",
    "Regulatory Compliance", "Customer Experience", "Supply Chain Redesign"
]

# ── GENERATE CONSULTANTS ──────────────────────────────────────────────────────

consultants = []
cid = 1
for practice, config in practice_areas.items():
    for level, lconfig in levels.items():
        n = max(1, int(config["headcount"] * lconfig["pct"]))
        for _ in range(n):
            base_rate = config["avg_bill_rate"] * lconfig["bill_mult"]
            cost_rate = config["avg_bill_rate"] * lconfig["cost_mult"] * 0.55
            consultants.append({
                "consultant_id": f"MP-{str(cid).zfill(4)}",
                "practice_area": practice,
                "level": level,
                "region": np.random.choice(regions, p=[0.35, 0.22, 0.15, 0.15, 0.13]),
                "billing_rate_gbp": round(base_rate + np.random.normal(0, 15), 0),
                "cost_rate_gbp": round(cost_rate + np.random.normal(0, 10), 0),
                "utilisation_target": lconfig["util_target"],
                "years_at_firm": max(1, int(np.random.exponential(4) + (6 - list(levels.keys()).index(level)))),
            })
            cid += 1

consultants_df = pd.DataFrame(consultants)
print(f"Consultants generated: {len(consultants_df)}")
print(f"By practice:\n{consultants_df['practice_area'].value_counts()}")

# ── GENERATE ENGAGEMENTS ──────────────────────────────────────────────────────

n_engagements = 480
start_window = datetime(2023, 1, 1)
end_window = datetime(2024, 12, 31)

# Client name generator
prefixes = ["Apex", "Vertex", "Horizon", "Sterling", "Nexus", "Atlas", "Crest",
            "Pinnacle", "Falcon", "Ironbridge", "Cascade", "Zenith", "Monarch",
            "Sentinel", "Vanguard", "Ember", "Helix", "Cobalt", "Astra", "Meridian"]
suffixes = ["Group", "Holdings", "Capital", "Partners", "International", "Corp",
            "Industries", "Systems", "Solutions", "Enterprises", "Ltd", "PLC"]

engagements = []
for i in range(1, n_engagements + 1):
    practice = np.random.choice(list(practice_areas.keys()),
                                 p=[0.22, 0.26, 0.18, 0.17, 0.17])
    config = practice_areas[practice]

    # Engagement size and duration
    eng_type = np.random.choice(engagement_types)
    duration_weeks = np.random.choice(
        [4, 6, 8, 10, 12, 16, 20, 24, 32],
        p=[0.08, 0.12, 0.18, 0.15, 0.18, 0.12, 0.08, 0.05, 0.04]
    )
    team_size = np.random.choice([2, 3, 4, 5, 6, 8, 10],
                                  p=[0.10, 0.20, 0.25, 0.20, 0.12, 0.08, 0.05])

    start_date = start_window + timedelta(days=np.random.randint(0, 650))
    end_date = start_date + timedelta(weeks=int(duration_weeks))

    # Revenue calculation
    avg_rate = config["avg_bill_rate"] * (1 + np.random.normal(0, 0.08))
    billable_hours = team_size * duration_weeks * 5 * np.random.uniform(0.55, 0.90)
    contracted_revenue = avg_rate * billable_hours

    # Cost calculation (consultant cost + overheads)
    avg_cost = avg_rate * 0.52 * (1 + np.random.normal(0, 0.05))
    direct_cost = avg_cost * billable_hours
    overhead_pct = np.random.uniform(0.08, 0.15)
    total_cost = direct_cost * (1 + overhead_pct)

    # Margin
    gross_margin = contracted_revenue - total_cost
    margin_pct = gross_margin / contracted_revenue if contracted_revenue > 0 else 0

    # Scope creep / overrun
    scope_overrun_pct = max(0, np.random.normal(0.08, 0.12))
    actual_hours = billable_hours * (1 + scope_overrun_pct)
    actual_cost = total_cost * (1 + scope_overrun_pct * 0.7)
    actual_margin = contracted_revenue - actual_cost
    actual_margin_pct = actual_margin / contracted_revenue if contracted_revenue > 0 else 0

    # Client satisfaction (1-10)
    base_sat = 7.2
    sat_adjust = -scope_overrun_pct * 8 + margin_pct * 3 + np.random.normal(0, 0.8)
    satisfaction = np.clip(base_sat + sat_adjust, 3, 10)

    # Repeat client probability
    is_repeat = np.random.binomial(1, 0.35)

    client_name = f"{random.choice(prefixes)} {random.choice(suffixes)}"

    engagements.append({
        "engagement_id": f"ENG-{str(i).zfill(4)}",
        "client_name": client_name,
        "client_industry": np.random.choice(client_industries),
        "engagement_type": eng_type,
        "practice_area": practice,
        "region": np.random.choice(regions, p=[0.38, 0.20, 0.15, 0.14, 0.13]),
        "start_date": start_date,
        "end_date": end_date,
        "duration_weeks": int(duration_weeks),
        "team_size": team_size,
        "contracted_hours": round(billable_hours, 0),
        "actual_hours": round(actual_hours, 0),
        "scope_overrun_pct": round(scope_overrun_pct * 100, 1),
        "avg_billing_rate_gbp": round(avg_rate, 0),
        "contracted_revenue_gbp": round(contracted_revenue, 0),
        "direct_cost_gbp": round(direct_cost, 0),
        "overhead_cost_gbp": round(total_cost - direct_cost, 0),
        "total_cost_gbp": round(total_cost, 0),
        "actual_cost_gbp": round(actual_cost, 0),
        "contracted_margin_gbp": round(gross_margin, 0),
        "contracted_margin_pct": round(margin_pct * 100, 1),
        "actual_margin_gbp": round(actual_margin, 0),
        "actual_margin_pct": round(actual_margin_pct * 100, 1),
        "client_satisfaction_score": round(satisfaction, 1),
        "is_repeat_client": is_repeat,
    })

engagements_df = pd.DataFrame(engagements)

# ── GENERATE MONTHLY UTILISATION DATA ─────────────────────────────────────────

months = pd.date_range("2023-01-01", "2024-12-01", freq="MS")
util_records = []

for _, consultant in consultants_df.iterrows():
    base_util = consultant["utilisation_target"]
    for month in months:
        # Seasonal pattern (lower in Dec, Aug)
        month_num = month.month
        seasonal = -0.08 if month_num in [8, 12] else (0.03 if month_num in [1, 9, 10] else 0)

        # Practice variation
        practice_var = np.random.normal(0, 0.06)

        # Tenure effect (new hires ramp up)
        tenure_effect = -0.10 if consultant["years_at_firm"] <= 1 else 0

        actual_util = np.clip(
            base_util + seasonal + practice_var + tenure_effect + np.random.normal(0, 0.05),
            0.15, 1.0
        )

        available_hours = 168  # ~21 working days × 8 hours
        billable = round(available_hours * actual_util, 0)
        non_billable = round(available_hours * np.random.uniform(0.10, 0.25), 0)
        bench = round(available_hours - billable - non_billable, 0)

        util_records.append({
            "consultant_id": consultant["consultant_id"],
            "practice_area": consultant["practice_area"],
            "level": consultant["level"],
            "month": month,
            "available_hours": available_hours,
            "billable_hours": billable,
            "non_billable_hours": non_billable,
            "bench_hours": max(0, bench),
            "utilisation_pct": round(actual_util * 100, 1),
            "utilisation_target_pct": round(consultant["utilisation_target"] * 100, 1),
        })

utilisation_df = pd.DataFrame(util_records)

# ── SAVE ──────────────────────────────────────────────────────────────────────

consultants_df.to_csv("/home/claude/consulting-project/data/meridian_consultants.csv", index=False)
engagements_df.to_csv("/home/claude/consulting-project/data/meridian_engagements.csv", index=False)
utilisation_df.to_csv("/home/claude/consulting-project/data/meridian_utilisation.csv", index=False)

print(f"\n{'='*60}")
print(f"DATASET SUMMARY")
print(f"{'='*60}")
print(f"Consultants: {len(consultants_df)}")
print(f"Engagements: {len(engagements_df)}")
print(f"Utilisation records: {len(utilisation_df)}")
print(f"\nFirm-wide avg utilisation: {utilisation_df['utilisation_pct'].mean():.1f}%")
print(f"Utilisation target (weighted): 75%")
print(f"\nTotal contracted revenue: £{engagements_df['contracted_revenue_gbp'].sum():,.0f}")
print(f"Total actual margin: £{engagements_df['actual_margin_gbp'].sum():,.0f}")
print(f"Avg contracted margin: {engagements_df['contracted_margin_pct'].mean():.1f}%")
print(f"Avg actual margin: {engagements_df['actual_margin_pct'].mean():.1f}%")
print(f"Avg scope overrun: {engagements_df['scope_overrun_pct'].mean():.1f}%")
print(f"Avg client satisfaction: {engagements_df['client_satisfaction_score'].mean():.1f}/10")
print(f"\nMargin by practice:")
print(engagements_df.groupby('practice_area')['actual_margin_pct'].mean().round(1))
print(f"\nUtilisation by level:")
print(utilisation_df.groupby('level')['utilisation_pct'].mean().round(1))
