"""
MERIDIAN & PARTNERS — Engagement Profitability & Utilisation Analysis
=====================================================================
Full analytical pipeline: profitability waterfall, utilisation gap analysis,
partner decision matrix, scope creep impact, and scenario modelling.

Author: Hrituparna Das
Tools: Python (pandas, matplotlib, seaborn), SQL, Power BI
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ── STYLE CONFIG ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor': '#0D1117',
    'axes.facecolor': '#0D1117',
    'text.color': '#C9D1D9',
    'axes.labelcolor': '#C9D1D9',
    'xtick.color': '#8B949E',
    'ytick.color': '#8B949E',
    'axes.edgecolor': '#21262D',
    'grid.color': '#21262D',
    'grid.alpha': 0.5,
    'font.family': 'sans-serif',
    'font.size': 11,
})

ACCENT = '#58A6FF'
RED = '#F85149'
GREEN = '#3FB950'
ORANGE = '#D29922'
PURPLE = '#BC8CFF'
TEAL = '#39D2C0'
GOLD = '#E3B341'

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
eng = pd.read_csv('/home/claude/consulting-project/data/meridian_engagements.csv',
                   parse_dates=['start_date', 'end_date'])
con = pd.read_csv('/home/claude/consulting-project/data/meridian_consultants.csv')
util = pd.read_csv('/home/claude/consulting-project/data/meridian_utilisation.csv',
                    parse_dates=['month'])

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 1: EXECUTIVE KPI DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

fig = plt.figure(figsize=(20, 5.5))
gs = GridSpec(1, 5, figure=fig, wspace=0.35)

firm_util = util['utilisation_pct'].mean()
util_gap = 75 - firm_util
total_rev = eng['contracted_revenue_gbp'].sum()
total_margin_leaked = (eng['contracted_margin_gbp'] - eng['actual_margin_gbp']).sum()
avg_actual_margin = eng['actual_margin_pct'].mean()
avg_satisfaction = eng['client_satisfaction_score'].mean()

metrics = [
    (f"£{total_rev/1e6:.1f}M", "Total Contracted\nRevenue (2Y)", ACCENT),
    (f"{firm_util:.1f}%", "Firm-Wide\nUtilisation", ORANGE),
    (f"£{total_margin_leaked/1e6:.2f}M", "Margin Leaked\n(Scope Creep)", RED),
    (f"{avg_actual_margin:.1f}%", "Avg Actual\nEngagement Margin", GREEN),
    (f"{avg_satisfaction:.1f}/10", "Avg Client\nSatisfaction", TEAL),
]

for i, (value, label, color) in enumerate(metrics):
    ax = fig.add_subplot(gs[0, i])
    ax.text(0.5, 0.62, value, fontsize=28, fontweight='bold', color=color,
            ha='center', va='center', transform=ax.transAxes)
    ax.text(0.5, 0.22, label, fontsize=11, color='#8B949E',
            ha='center', va='center', transform=ax.transAxes, linespacing=1.4)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    rect = FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle="round,pad=0.02",
                           facecolor='#161B22', edgecolor='#30363D', linewidth=1.5,
                           transform=ax.transAxes)
    ax.add_patch(rect)

fig.suptitle('MERIDIAN & PARTNERS — Engagement Profitability: Executive Dashboard',
             fontsize=15, fontweight='bold', color='#F0F6FC', y=1.05)
plt.savefig('/home/claude/consulting-project/visuals/01_executive_dashboard.png',
            dpi=200, bbox_inches='tight', facecolor='#0D1117')
plt.close()
print("✓ Figure 1: Executive Dashboard")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 2: PROFITABILITY WATERFALL — CONTRACTED vs ACTUAL MARGIN
# ══════════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(14, 7))

practice_fin = eng.groupby('practice_area').agg(
    contracted=('contracted_margin_gbp', 'sum'),
    actual=('actual_margin_gbp', 'sum'),
    revenue=('contracted_revenue_gbp', 'sum'),
    overrun=('scope_overrun_pct', 'mean')
).reset_index()
practice_fin['leaked'] = practice_fin['contracted'] - practice_fin['actual']
practice_fin = practice_fin.sort_values('leaked', ascending=False)

x = np.arange(len(practice_fin))
w = 0.32

bars1 = ax.bar(x - w/2, practice_fin['contracted']/1000, w,
               label='Contracted Margin', color=GREEN, edgecolor='none', zorder=3)
bars2 = ax.bar(x + w/2, practice_fin['actual']/1000, w,
               label='Actual Margin', color=ACCENT, edgecolor='none', zorder=3)

# Leakage arrows
for i, (_, row) in enumerate(practice_fin.iterrows()):
    leaked = row['leaked'] / 1000
    ax.annotate(
        f'−£{leaked:.0f}K\n({row["overrun"]:.0f}% overrun)',
        xy=(i + w/2, row['actual']/1000),
        xytext=(i + 0.55, row['actual']/1000 + 80),
        fontsize=9, color=RED, fontweight='bold',
        arrowprops=dict(arrowstyle='->', color=RED, lw=1.5),
        ha='left'
    )

short_names = [p.split(' & ')[0].split(' ')[0] for p in practice_fin['practice_area']]
ax.set_xticks(x)
ax.set_xticklabels(practice_fin['practice_area'], fontsize=10, rotation=12, ha='right')
ax.set_ylabel('Margin (£K)', fontsize=12, fontweight='bold')
ax.set_title('Profitability Waterfall — Contracted vs Actual Margin by Practice Area',
             fontsize=14, fontweight='bold', color='#F0F6FC', pad=15)
ax.legend(fontsize=11, framealpha=0.3, loc='upper right')
ax.grid(axis='y', alpha=0.2)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'£{x:,.0f}K'))

plt.savefig('/home/claude/consulting-project/visuals/02_profitability_waterfall.png',
            dpi=200, bbox_inches='tight', facecolor='#0D1117')
plt.close()
print("✓ Figure 2: Profitability Waterfall")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 3: UTILISATION GAP — BY LEVEL (THE MONEY CHART)
# ══════════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(13, 7))

level_order = ['Partner', 'Director', 'Senior Manager', 'Manager', 'Senior Consultant', 'Consultant']
level_util = util.groupby('level').agg(
    actual=('utilisation_pct', 'mean'),
    target=('utilisation_target_pct', 'mean'),
    headcount=('consultant_id', 'nunique')
).reindex(level_order)

y = np.arange(len(level_util))
height = 0.35

bars_actual = ax.barh(y + height/2, level_util['actual'], height,
                       label='Actual Utilisation', color=ACCENT, edgecolor='none', zorder=3)
bars_target = ax.barh(y - height/2, level_util['target'], height,
                       label='Target Utilisation', color='#30363D', edgecolor='#8B949E',
                       linewidth=1, zorder=2)

for i, (level, row) in enumerate(level_util.iterrows()):
    gap = row['target'] - row['actual']
    color = RED if gap > 3 else ORANGE if gap > 0 else GREEN
    symbol = '▼' if gap > 0 else '▲'
    ax.text(max(row['actual'], row['target']) + 1.5, i,
            f'{symbol} {abs(gap):.1f}pp gap  (n={int(row["headcount"])})',
            va='center', fontsize=10, fontweight='bold', color=color)

ax.axvline(75, color=GOLD, linestyle='--', linewidth=2, alpha=0.6, zorder=1)
ax.text(75.5, -0.7, '75% Firm Target', fontsize=9, color=GOLD, fontweight='bold')

ax.set_yticks(y)
ax.set_yticklabels(level_order, fontsize=12)
ax.set_xlabel('Utilisation (%)', fontsize=12, fontweight='bold')
ax.set_title('Utilisation Gap by Consultant Level — Mid-Levels Drive the Biggest Opportunity',
             fontsize=14, fontweight='bold', color='#F0F6FC', pad=15)
ax.legend(fontsize=10, framealpha=0.3, loc='lower right')
ax.set_xlim(0, 100)
ax.grid(axis='x', alpha=0.2)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.savefig('/home/claude/consulting-project/visuals/03_utilisation_gap.png',
            dpi=200, bbox_inches='tight', facecolor='#0D1117')
plt.close()
print("✓ Figure 3: Utilisation Gap")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 4: UTILISATION TREND — MONTHLY WITH SEASONAL PATTERN
# ══════════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(14, 6))

monthly_trend = util.groupby('month')['utilisation_pct'].mean().reset_index()
monthly_trend['month_label'] = monthly_trend['month'].dt.strftime('%b %Y')

ax.plot(monthly_trend['month'], monthly_trend['utilisation_pct'],
        color=ACCENT, linewidth=2.5, zorder=3, marker='o', markersize=5)
ax.fill_between(monthly_trend['month'], monthly_trend['utilisation_pct'],
                alpha=0.15, color=ACCENT)

ax.axhline(75, color=GOLD, linestyle='--', linewidth=2, alpha=0.7, label='75% Target')

# Highlight seasonal dips
for _, row in monthly_trend.iterrows():
    if row['utilisation_pct'] < 68:
        ax.annotate(f'{row["utilisation_pct"]:.1f}%',
                    (row['month'], row['utilisation_pct']),
                    textcoords="offset points", xytext=(0, -20),
                    fontsize=9, color=RED, fontweight='bold',
                    ha='center',
                    arrowprops=dict(arrowstyle='->', color=RED, lw=1.2))

ax.set_xlabel('Month', fontsize=12, fontweight='bold')
ax.set_ylabel('Avg Utilisation (%)', fontsize=12, fontweight='bold')
ax.set_title('Monthly Utilisation Trend — August & December Consistently Below Target',
             fontsize=14, fontweight='bold', color='#F0F6FC', pad=15)
ax.legend(fontsize=10, framealpha=0.3)
ax.grid(alpha=0.2)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_ylim(60, 80)
plt.xticks(rotation=45, ha='right')

plt.savefig('/home/claude/consulting-project/visuals/04_utilisation_trend.png',
            dpi=200, bbox_inches='tight', facecolor='#0D1117')
plt.close()
print("✓ Figure 4: Utilisation Trend")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 5: SCOPE CREEP IMPACT — ENGAGEMENT TYPE BREAKDOWN
# ══════════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(14, 7))

scope = eng.groupby('engagement_type').agg(
    avg_overrun=('scope_overrun_pct', 'mean'),
    margin_eroded=('contracted_margin_gbp', 'sum'),
    actual_margin=('actual_margin_gbp', 'sum'),
    count=('engagement_id', 'count')
).reset_index()
scope['total_eroded'] = scope['margin_eroded'] - scope['actual_margin']
scope = scope.sort_values('avg_overrun', ascending=True)

colors = [RED if o > 12 else ORANGE if o > 8 else GREEN for o in scope['avg_overrun']]
bars = ax.barh(scope['engagement_type'], scope['avg_overrun'],
               color=colors, edgecolor='none', height=0.6, zorder=3)

for bar, (_, row) in zip(bars, scope.iterrows()):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f'{row["avg_overrun"]:.1f}%  (£{row["total_eroded"]/1000:.0f}K eroded, n={int(row["count"])})',
            va='center', fontsize=9, fontweight='bold',
            color=RED if row['avg_overrun'] > 12 else '#C9D1D9')

ax.set_xlabel('Average Scope Overrun (%)', fontsize=12, fontweight='bold')
ax.set_title('Scope Creep by Engagement Type — Digital Transformation & M&A Are the Worst Offenders',
             fontsize=13, fontweight='bold', color='#F0F6FC', pad=15)
ax.grid(axis='x', alpha=0.2)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.savefig('/home/claude/consulting-project/visuals/05_scope_creep.png',
            dpi=200, bbox_inches='tight', facecolor='#0D1117')
plt.close()
print("✓ Figure 5: Scope Creep Impact")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 6: PARTNER DECISION MATRIX — MARGIN vs SATISFACTION
# ══════════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(13, 8))

practice_colors = {
    "Strategy & Growth": ACCENT,
    "Technology & Digital": PURPLE,
    "Operations & Supply Chain": GREEN,
    "Financial Advisory": GOLD,
    "People & Organisation": TEAL,
}

for practice, color in practice_colors.items():
    mask = eng['practice_area'] == practice
    ax.scatter(
        eng.loc[mask, 'actual_margin_pct'],
        eng.loc[mask, 'client_satisfaction_score'],
        s=eng.loc[mask, 'contracted_revenue_gbp'] / 800,
        c=color, alpha=0.6, edgecolors='#F0F6FC', linewidth=0.5,
        label=practice, zorder=3
    )

# Quadrant lines
ax.axvline(eng['actual_margin_pct'].median(), color='#30363D', linestyle='--', alpha=0.7)
ax.axhline(eng['client_satisfaction_score'].median(), color='#30363D', linestyle='--', alpha=0.7)

ax.text(0.02, 0.98, 'HIGH SATISFACTION\nLOW MARGIN\n→ Reprice', transform=ax.transAxes,
        fontsize=9, color=ORANGE, alpha=0.8, va='top', fontweight='bold')
ax.text(0.98, 0.98, 'STARS\nHigh Margin + Happy Client\n→ Expand', transform=ax.transAxes,
        fontsize=9, color=GREEN, alpha=0.8, va='top', ha='right', fontweight='bold')
ax.text(0.02, 0.02, 'PROBLEM\nLow Margin + Unhappy\n→ Exit / Fix', transform=ax.transAxes,
        fontsize=9, color=RED, alpha=0.8, fontweight='bold')
ax.text(0.98, 0.02, 'CASH COWS\nHigh Margin, Lower Satisfaction\n→ Invest in Delivery', transform=ax.transAxes,
        fontsize=9, color=ACCENT, alpha=0.8, ha='right', fontweight='bold')

ax.set_xlabel('Actual Margin (%)', fontsize=12, fontweight='bold')
ax.set_ylabel('Client Satisfaction (1-10)', fontsize=12, fontweight='bold')
ax.set_title('Partner Decision Matrix — Engagement Performance by Practice Area',
             fontsize=14, fontweight='bold', color='#F0F6FC', pad=15)
ax.legend(fontsize=9, framealpha=0.3, loc='center left', bbox_to_anchor=(1, 0.5),
          title='Practice Area', title_fontsize=10)
ax.grid(alpha=0.2)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.savefig('/home/claude/consulting-project/visuals/06_partner_decision_matrix.png',
            dpi=200, bbox_inches='tight', facecolor='#0D1117')
plt.close()
print("✓ Figure 6: Partner Decision Matrix")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 7: UTILISATION SCENARIO ANALYSIS — REVENUE UPLIFT
# ══════════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(13, 7))

# Calculate revenue opportunity by practice
practice_util = util.merge(con[['consultant_id', 'billing_rate_gbp']], on='consultant_id')

underutil = practice_util[practice_util['utilisation_pct'] < 75].copy()
practice_opp = underutil.groupby('practice_area').apply(
    lambda g: pd.Series({
        'headcount': g['consultant_id'].nunique(),
        'current_util': g['utilisation_pct'].mean(),
        'gap_hours': ((75 - g['utilisation_pct']) / 100 * g['available_hours']).sum(),
        's1_revenue': ((73 - g['utilisation_pct']).clip(lower=0) / 100 * g['available_hours'] * g['billing_rate_gbp']).sum(),
        's2_revenue': ((75 - g['utilisation_pct']).clip(lower=0) / 100 * g['available_hours'] * g['billing_rate_gbp']).sum(),
        's3_revenue': ((78 - g['utilisation_pct']).clip(lower=0) / 100 * g['available_hours'] * g['billing_rate_gbp']).sum(),
    })
).reset_index()

practice_opp = practice_opp.sort_values('s2_revenue', ascending=True)

y = np.arange(len(practice_opp))
h = 0.22

ax.barh(y - h, practice_opp['s1_revenue']/1e6, h, label='Conservative (→73%)',
        color=ACCENT, edgecolor='none', zorder=3)
ax.barh(y, practice_opp['s2_revenue']/1e6, h, label='Target (→75%)',
        color=GREEN, edgecolor='none', zorder=3)
ax.barh(y + h, practice_opp['s3_revenue']/1e6, h, label='Stretch (→78%)',
        color=GOLD, edgecolor='none', zorder=3)

for i, (_, row) in enumerate(practice_opp.iterrows()):
    ax.text(row['s3_revenue']/1e6 + 0.03, i + h,
            f'£{row["s2_revenue"]/1e6:.2f}M @ target',
            va='center', fontsize=9, fontweight='bold', color=GREEN)

ax.set_yticks(y)
ax.set_yticklabels(practice_opp['practice_area'], fontsize=11)
ax.set_xlabel('Additional Revenue (£M)', fontsize=12, fontweight='bold')
ax.set_title(f'Revenue Uplift Scenarios — Closing the Utilisation Gap (£{practice_opp["s2_revenue"].sum()/1e6:.1f}M at Target)',
             fontsize=13, fontweight='bold', color='#F0F6FC', pad=15)
ax.legend(fontsize=10, framealpha=0.3, loc='lower right')
ax.grid(axis='x', alpha=0.2)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'£{x:.1f}M'))

plt.savefig('/home/claude/consulting-project/visuals/07_scenario_analysis.png',
            dpi=200, bbox_inches='tight', facecolor='#0D1117')
plt.close()
print("✓ Figure 7: Scenario Analysis")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 8: PRACTICE AREA HEATMAP — UTILISATION × LEVEL
# ══════════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(13, 7))

pivot = util.pivot_table(values='utilisation_pct', index='level', columns='practice_area',
                          aggfunc='mean')
pivot = pivot.reindex(level_order)

sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn', linewidths=2,
            linecolor='#0D1117', cbar_kws={'label': 'Utilisation %', 'shrink': 0.8},
            ax=ax, annot_kws={'fontsize': 11, 'fontweight': 'bold'},
            vmin=40, vmax=90, center=70)

ax.set_title('Utilisation Heatmap — Practice Area × Consultant Level',
             fontsize=14, fontweight='bold', color='#F0F6FC', pad=15)
ax.set_ylabel('')
ax.tick_params(axis='y', rotation=0)
ax.tick_params(axis='x', rotation=15)

plt.savefig('/home/claude/consulting-project/visuals/08_utilisation_heatmap.png',
            dpi=200, bbox_inches='tight', facecolor='#0D1117')
plt.close()
print("✓ Figure 8: Utilisation Heatmap")


# ══════════════════════════════════════════════════════════════════════════════
# CONSOLE OUTPUT: KEY FINDINGS
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("KEY FINDINGS — MERIDIAN & PARTNERS PROFITABILITY ANALYSIS")
print("="*70)

total_leaked = (eng['contracted_margin_gbp'] - eng['actual_margin_gbp']).sum()

print(f"\n📊 FIRM FINANCIAL OVERVIEW (2023–2024)")
print(f"   Total contracted revenue: £{eng['contracted_revenue_gbp'].sum():,.0f}")
print(f"   Total actual margin: £{eng['actual_margin_gbp'].sum():,.0f}")
print(f"   Margin leaked to scope creep: £{total_leaked:,.0f}")
print(f"   Avg contracted margin: {eng['contracted_margin_pct'].mean():.1f}%")
print(f"   Avg actual margin: {eng['actual_margin_pct'].mean():.1f}%")
print(f"   Margin erosion: {(eng['contracted_margin_pct'].mean() - eng['actual_margin_pct'].mean()):.1f} percentage points")

print(f"\n🔥 UTILISATION GAP")
print(f"   Firm-wide utilisation: {firm_util:.1f}% vs 75% target")
print(f"   Gap: {75 - firm_util:.1f} percentage points")
print(f"   Revenue opportunity at target: £{practice_opp['s2_revenue'].sum():,.0f}")

print(f"\n📉 SCOPE CREEP WORST OFFENDERS")
worst = eng.groupby('engagement_type')['scope_overrun_pct'].mean().sort_values(ascending=False).head(3)
for etype, overrun in worst.items():
    print(f"   {etype}: {overrun:.1f}% avg overrun")

print(f"\n💰 PARTNER ACTIONS")
high_margin_happy = eng[(eng['actual_margin_pct'] > eng['actual_margin_pct'].median()) &
                         (eng['client_satisfaction_score'] > eng['client_satisfaction_score'].median())]
print(f"   EXPAND (high margin + satisfied): {len(high_margin_happy)} engagements")
print(f"   Revenue in EXPAND quadrant: £{high_margin_happy['contracted_revenue_gbp'].sum():,.0f}")

print("\n" + "="*70)
print("All visualizations saved to /visuals/")
print("="*70)
