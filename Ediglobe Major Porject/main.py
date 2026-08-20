import csv
import json
import os
import webbrowser
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt

DATA_DIR = "data"
EXPENSE_FILE = os.path.join(DATA_DIR, "expenses.csv")
BUDGET_FILE = os.path.join(DATA_DIR, "budget.json")
REPORT_FILE = "expense_report.txt"
DASHBOARD_FILE = "expense_dashboard.html"

CATEGORIES = ["Food", "Transport", "Entertainment", "Shopping", "Bills", "Health", "Education", "Other"]

# Fixed category colors so the same category always renders in the same
# color across every chart (bar, pie, dashboard, etc.)
CATEGORY_COLORS = {
    "Food": "#E8B33D",
    "Transport": "#2FBF71",
    "Entertainment": "#5B8DEF",
    "Shopping": "#E4573D",
    "Bills": "#8A94A6",
    "Health": "#C36FE8",
    "Education": "#3DBFB8",
    "Other": "#B08968",
}


def ensure_storage():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(EXPENSE_FILE):
        with open(EXPENSE_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["id", "date", "category", "amount", "description"])
    if not os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE, "w", encoding="utf-8") as f:
            json.dump({"monthly_budget": 0}, f)


def load_expenses():
    ensure_storage()
    with open(EXPENSE_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_expenses(expenses):
    with open(EXPENSE_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "date", "category", "amount", "description"])
        writer.writeheader()
        writer.writerows(expenses)


def next_id(expenses):
    return max([int(e["id"]) for e in expenses] or [0]) + 1


def get_amount(prompt="Amount: "):
    while True:
        try:
            amount = float(input(prompt))
            if amount <= 0:
                raise ValueError
            return amount
        except ValueError:
            print("Enter a valid positive number.")


def get_date(prompt="Date (YYYY-MM-DD, blank=today): "):
    value = input(prompt).strip()
    if not value:
        return datetime.now().strftime("%Y-%m-%d")
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        print("Invalid date. Using today's date.")
        return datetime.now().strftime("%Y-%m-%d")


def choose_category():
    print("\nCategories:")
    for i, category in enumerate(CATEGORIES, 1):
        print(f"{i}. {category}")
    try:
        choice = int(input("Choose category: "))
        if 1 <= choice <= len(CATEGORIES):
            return CATEGORIES[choice - 1]
    except ValueError:
        pass
    print("Invalid category. Using Other.")
    return "Other"


def add_expense(expenses):
    expense = {
        "id": str(next_id(expenses)),
        "date": get_date(),
        "category": choose_category(),
        "amount": f"{get_amount():.2f}",
        "description": input("Description: ").strip() or "No description"
    }
    expenses.append(expense)
    save_expenses(expenses)
    print("Expense added successfully.")


def display(expenses):
    if not expenses:
        print("No expenses found.")
        return
    print("\nID   Date         Category          Amount      Description")
    print("-" * 70)
    for e in expenses:
        print(f'{e["id"]:<4} {e["date"]:<12} {e["category"]:<17} ₹{float(e["amount"]):<10.2f} {e["description"]}')


def delete_expense(expenses):
    display(expenses)
    target = input("Enter expense ID to delete: ").strip()
    updated = [e for e in expenses if e["id"] != target]
    if len(updated) == len(expenses):
        print("ID not found.")
    else:
        save_expenses(updated)
        expenses[:] = updated
        print("Expense deleted.")


def edit_expense(expenses):
    display(expenses)
    target = input("Enter expense ID to edit: ").strip()
    for e in expenses:
        if e["id"] == target:
            print("Press Enter to keep the current value.")
            date = input(f'Date [{e["date"]}]: ').strip()
            if date:
                try:
                    datetime.strptime(date, "%Y-%m-%d")
                    e["date"] = date
                except ValueError:
                    print("Invalid date; keeping old date.")
            category = input(f'Category [{e["category"]}]: ').strip()
            if category:
                matches = [c for c in CATEGORIES if c.lower() == category.lower()]
                if matches:
                    e["category"] = matches[0]
            amount = input(f'Amount [{e["amount"]}]: ').strip()
            if amount:
                try:
                    value = float(amount)
                    if value > 0:
                        e["amount"] = f"{value:.2f}"
                except ValueError:
                    print("Invalid amount; keeping old amount.")
            desc = input(f'Description [{e["description"]}]: ').strip()
            if desc:
                e["description"] = desc
            save_expenses(expenses)
            print("Expense updated.")
            return
    print("ID not found.")


def category_totals(expenses):
    totals = defaultdict(float)
    for e in expenses:
        totals[e["category"]] += float(e["amount"])
    return dict(totals)


def monthly_totals(expenses):
    totals = defaultdict(float)
    for e in expenses:
        month = e["date"][:7]
        totals[month] += float(e["amount"])
    return dict(sorted(totals.items()))


def get_budget():
    try:
        with open(BUDGET_FILE, encoding="utf-8") as f:
            return float(json.load(f).get("monthly_budget", 0))
    except (OSError, ValueError, json.JSONDecodeError):
        return 0.0


def generate_report(expenses):
    if not expenses:
        print("No expenses to report.")
        return
    total = sum(float(e["amount"]) for e in expenses)
    average = total / len(expenses)
    highest = max(expenses, key=lambda e: float(e["amount"]))
    totals = category_totals(expenses)

    print("\n===== EXPENSE REPORT =====")
    print(f"Total spent      : ₹{total:.2f}")
    print(f"Average expense  : ₹{average:.2f}")
    print(f"Highest expense  : ₹{float(highest['amount']):.2f} ({highest['category']})")
    print("\nCategory-wise spending:")
    for category, amount in sorted(totals.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category:<15} ₹{amount:.2f}")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("PERSONAL EXPENSE TRACKER REPORT\n")
        f.write("=" * 35 + "\n")
        f.write(f"Total spent: ₹{total:.2f}\n")
        f.write(f"Average expense: ₹{average:.2f}\n")
        f.write(f"Highest expense: ₹{float(highest['amount']):.2f} ({highest['category']})\n\n")
        for category, amount in sorted(totals.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{category}: ₹{amount:.2f}\n")
    print(f"Report exported to {REPORT_FILE}.")


def monthly_summary(expenses):
    month = input("Month (YYYY-MM, blank=current): ").strip() or datetime.now().strftime("%Y-%m")
    selected = [e for e in expenses if e["date"].startswith(month)]
    if not selected:
        print("No expenses for that month.")
        return
    total = sum(float(e["amount"]) for e in selected)
    print(f"\nSpending for {month}: ₹{total:.2f}")
    for category, amount in sorted(category_totals(selected).items(), key=lambda x: x[1], reverse=True):
        print(f"  {category:<15} ₹{amount:.2f}")


def search_filter(expenses):
    category = input("Category filter (blank=all): ").strip().lower()
    month = input("Month filter YYYY-MM (blank=all): ").strip()
    results = [
        e for e in expenses
        if (not category or e["category"].lower() == category)
        and (not month or e["date"].startswith(month))
    ]
    display(results)


def set_budget():
    try:
        value = float(input("Monthly budget (₹): "))
        if value < 0:
            raise ValueError
        with open(BUDGET_FILE, "w", encoding="utf-8") as f:
            json.dump({"monthly_budget": value}, f)
        print("Budget saved.")
    except ValueError:
        print("Enter a valid non-negative number.")


def budget_status(expenses):
    budget = get_budget()
    month = datetime.now().strftime("%Y-%m")
    spent = sum(float(e["amount"]) for e in expenses if e["date"].startswith(month))
    if budget <= 0:
        print("No monthly budget set.")
        return
    remaining = budget - spent
    print(f"Budget: ₹{budget:.2f} | Spent: ₹{spent:.2f} | Remaining: ₹{remaining:.2f}")
    if spent > budget:
        print("ALERT: Monthly budget exceeded!")
    elif spent >= budget * 0.8:
        print("WARNING: You have used 80% or more of your budget.")


def smart_insights(expenses):
    if not expenses:
        print("No data for insights.")
        return
    totals = category_totals(expenses)
    top_category, top_amount = max(totals.items(), key=lambda x: x[1])
    total = sum(totals.values())
    share = (top_amount / total) * 100 if total else 0
    print("\n===== SMART INSIGHTS =====")
    print(f"Top spending category: {top_category} (₹{top_amount:.2f})")
    print(f"It represents {share:.1f}% of all recorded spending.")
    if share >= 50:
        print("Suggestion: Review this category and look for possible savings.")
    else:
        print("Your spending is relatively distributed across categories.")


def visualize(expenses):
    """One tidy multi-panel matplotlib dashboard instead of separate pop-ups:
    category bar, category pie, monthly trend line, and cumulative spend area."""
    if not expenses:
        print("No data to visualize.")
        return

    totals = category_totals(expenses)
    labels = list(totals.keys())
    values = list(totals.values())
    colors = [CATEGORY_COLORS.get(c, "#8A94A6") for c in labels]

    m_totals = monthly_totals(expenses)
    months = list(m_totals.keys())
    m_values = list(m_totals.values())
    cumulative = []
    running = 0
    for v in m_values:
        running += v
        cumulative.append(running)

    plt.style.use("seaborn-v0_8-whitegrid") if "seaborn-v0_8-whitegrid" in plt.style.available else None
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle("Personal Expense Dashboard", fontsize=18, fontweight="bold")

    ax = axes[0][0]
    bars = ax.bar(labels, values, color=colors)
    ax.set_title("Spending by Category")
    ax.set_ylabel("Amount (₹)")
    ax.tick_params(axis="x", rotation=30)
    for b in bars:
        ax.annotate(f"₹{b.get_height():,.0f}", (b.get_x() + b.get_width() / 2, b.get_height()),
                    ha="center", va="bottom", fontsize=8)

    ax = axes[0][1]
    ax.pie(values, labels=labels, colors=colors, autopct="%1.1f%%",
           wedgeprops={"linewidth": 1, "edgecolor": "white"})
    ax.set_title("Expense Distribution")

    ax = axes[1][0]
    if months:
        ax.plot(months, m_values, marker="o", color="#2FBF71", linewidth=2)
        ax.fill_between(months, m_values, alpha=0.15, color="#2FBF71")
    ax.set_title("Monthly Spending Trend")
    ax.set_ylabel("Amount (₹)")
    ax.tick_params(axis="x", rotation=30)

    ax = axes[1][1]
    if months:
        ax.plot(months, cumulative, marker="o", color="#E8B33D", linewidth=2)
        ax.fill_between(months, cumulative, alpha=0.15, color="#E8B33D")
    ax.set_title("Cumulative Spending Over Time")
    ax.set_ylabel("Amount (₹)")
    ax.tick_params(axis="x", rotation=30)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


def export_html_dashboard(expenses):
    """Builds a polished, standalone HTML dashboard (charts + stat cards +
    a budget gauge) that opens straight in the browser and can be shared
    or embedded in a project write-up."""
    if not expenses:
        print("No data to build a dashboard from. Add some expenses first.")
        return

    total = sum(float(e["amount"]) for e in expenses)
    average = total / len(expenses)
    highest = max(expenses, key=lambda e: float(e["amount"]))
    totals = category_totals(expenses)
    m_totals = monthly_totals(expenses)
    budget = get_budget()
    current_month = datetime.now().strftime("%Y-%m")
    spent_this_month = sum(float(e["amount"]) for e in expenses if e["date"].startswith(current_month))
    budget_pct = min((spent_this_month / budget) * 100, 100) if budget > 0 else 0

    sorted_categories = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    top5 = sorted(expenses, key=lambda e: float(e["amount"]), reverse=True)[:5]

    cat_labels = [c for c, _ in sorted_categories]
    cat_values = [round(v, 2) for _, v in sorted_categories]
    cat_colors = [CATEGORY_COLORS.get(c, "#8A94A6") for c in cat_labels]
    month_labels = list(m_totals.keys())
    month_values = [round(v, 2) for v in m_totals.values()]

    data = {
        "catLabels": cat_labels,
        "catValues": cat_values,
        "catColors": cat_colors,
        "monthLabels": month_labels,
        "monthValues": month_values,
        "budget": round(budget, 2),
        "spentThisMonth": round(spent_this_month, 2),
        "budgetPct": round(budget_pct, 1),
        "top5": [
            {"desc": e["description"], "cat": e["category"], "amount": float(e["amount"]), "date": e["date"]}
            for e in top5
        ],
    }

    html = HTML_TEMPLATE.replace("__DATA__", json.dumps(data)) \
        .replace("__TOTAL__", f"{total:,.2f}") \
        .replace("__AVERAGE__", f"{average:,.2f}") \
        .replace("__HIGHEST__", f"{float(highest['amount']):,.2f}") \
        .replace("__HIGHEST_CAT__", highest["category"]) \
        .replace("__COUNT__", str(len(expenses))) \
        .replace("__BUDGET__", f"{budget:,.2f}" if budget > 0 else "Not set") \
        .replace("__REMAINING__", f"{(budget - spent_this_month):,.2f}" if budget > 0 else "—") \
        .replace("__GENERATED__", datetime.now().strftime("%d %b %Y, %I:%M %p"))

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard exported to {os.path.abspath(DASHBOARD_FILE)}")
    try:
        webbrowser.open("file://" + os.path.abspath(DASHBOARD_FILE))
    except Exception:
        pass


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Personal Expense Ledger — Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.4/chart.umd.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --ink: #14171C;
    --panel: #1C212B;
    --panel-2: #232A36;
    --line: #313A48;
    --paper: #EDEDE3;
    --muted: #8A94A6;
    --green: #2FBF71;
    --gold: #E8B33D;
    --red: #E4573D;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--ink);
    color: var(--paper);
    font-family: 'IBM Plex Sans', sans-serif;
    padding: 40px 6vw 80px;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 1px solid var(--line);
    padding-bottom: 22px;
    margin-bottom: 30px;
    flex-wrap: wrap;
    gap: 16px;
  }
  .eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-size: 11px;
    color: var(--green);
    font-weight: 600;
    margin: 0 0 6px;
  }
  h1 {
    font-family: 'Fraunces', serif;
    font-weight: 700;
    font-size: 34px;
    margin: 0;
    letter-spacing: -0.01em;
  }
  .meta { color: var(--muted); font-size: 13px; text-align: right; }
  .meta span { display: block; }

  .stat-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 16px;
    margin-bottom: 28px;
  }
  .stat {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 18px 20px;
    position: relative;
  }
  .stat::before {
    content: "";
    position: absolute;
    left: 0; top: 14px; bottom: 14px;
    width: 3px;
    background: var(--green);
    border-radius: 0 3px 3px 0;
  }
  .stat.gold::before { background: var(--gold); }
  .stat.red::before { background: var(--red); }
  .stat-label {
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-size: 10.5px;
    color: var(--muted);
    margin: 0 0 8px;
  }
  .stat-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 24px;
    font-weight: 600;
  }
  .stat-sub { font-size: 12px; color: var(--muted); margin-top: 4px; }

  .grid {
    display: grid;
    grid-template-columns: 1.2fr 1fr;
    gap: 18px;
    margin-bottom: 18px;
  }
  .grid.thirds { grid-template-columns: 1fr 1fr 1fr; }
  .card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 20px;
  }
  .card h2 {
    font-family: 'Fraunces', serif;
    font-size: 16px;
    font-weight: 600;
    margin: 0 0 14px;
    color: var(--paper);
  }
  .card h2 small {
    display: block;
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 400;
    font-size: 11px;
    color: var(--muted);
    margin-top: 3px;
    letter-spacing: 0.02em;
  }
  canvas { max-height: 300px; }

  .gauge-wrap { position: relative; text-align: center; }
  .gauge-readout {
    position: absolute;
    left: 50%; top: 62%;
    transform: translate(-50%, -50%);
  }
  .gauge-readout .pct {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 30px;
    font-weight: 600;
  }
  .gauge-readout .label {
    font-size: 11px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th {
    text-align: left;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 10.5px;
    color: var(--muted);
    font-weight: 500;
    border-bottom: 1px solid var(--line);
    padding: 0 0 8px;
  }
  td {
    padding: 9px 0;
    border-bottom: 1px dashed var(--line);
  }
  td.amount {
    font-family: 'IBM Plex Mono', monospace;
    text-align: right;
    font-weight: 600;
  }
  .tag {
    display: inline-block;
    font-size: 10.5px;
    padding: 2px 8px;
    border-radius: 20px;
    background: var(--panel-2);
    color: var(--muted);
  }

  footer {
    text-align: center;
    color: var(--muted);
    font-size: 11.5px;
    margin-top: 40px;
    letter-spacing: 0.04em;
  }

  @media (max-width: 900px) {
    .grid, .grid.thirds { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<header>
  <div>
    <p class="eyebrow">Personal Finance · Ledger No. 001</p>
    <h1>Expense Dashboard</h1>
  </div>
  <div class="meta">
    <span>__COUNT__ entries recorded</span>
    <span>Generated __GENERATED__</span>
  </div>
</header>

<div class="stat-row">
  <div class="stat">
    <p class="stat-label">Total Spent</p>
    <div class="stat-value">₹__TOTAL__</div>
  </div>
  <div class="stat gold">
    <p class="stat-label">Average / Entry</p>
    <div class="stat-value">₹__AVERAGE__</div>
  </div>
  <div class="stat red">
    <p class="stat-label">Highest Expense</p>
    <div class="stat-value">₹__HIGHEST__</div>
    <p class="stat-sub">__HIGHEST_CAT__</p>
  </div>
  <div class="stat">
    <p class="stat-label">Monthly Budget</p>
    <div class="stat-value">₹__BUDGET__</div>
    <p class="stat-sub">Remaining: ₹__REMAINING__</p>
  </div>
</div>

<div class="grid">
  <div class="card">
    <h2>Spending by Category <small>Total ₹ per category, high to low</small></h2>
    <canvas id="catBar"></canvas>
  </div>
  <div class="card">
    <h2>Expense Distribution <small>Share of total spend</small></h2>
    <canvas id="catDoughnut"></canvas>
  </div>
</div>

<div class="grid">
  <div class="card">
    <h2>Monthly Trend <small>Spending by calendar month</small></h2>
    <canvas id="monthLine"></canvas>
  </div>
  <div class="card">
    <h2>Budget Dial <small>Used this month vs. monthly budget</small></h2>
    <div class="gauge-wrap">
      <canvas id="gauge"></canvas>
      <div class="gauge-readout">
        <div class="pct" id="gaugePct">0%</div>
        <div class="label">of budget used</div>
      </div>
    </div>
  </div>
</div>

<div class="card">
  <h2>Top 5 Expenses <small>Largest single entries recorded</small></h2>
  <table>
    <thead><tr><th>Date</th><th>Description</th><th>Category</th><th style="text-align:right">Amount</th></tr></thead>
    <tbody id="top5Body"></tbody>
  </table>
</div>

<footer>PERSONAL EXPENSE TRACKER — auto-generated dashboard, no data leaves this file</footer>

<script>
const DATA = __DATA__;
Chart.defaults.color = "#8A94A6";
Chart.defaults.font.family = "'IBM Plex Sans', sans-serif";
Chart.defaults.borderColor = "#313A48";

new Chart(document.getElementById('catBar'), {
  type: 'bar',
  data: {
    labels: DATA.catLabels,
    datasets: [{ data: DATA.catValues, backgroundColor: DATA.catColors, borderRadius: 4, maxBarThickness: 42 }]
  },
  options: {
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true, grid: { color: '#313A48' } }, x: { grid: { display: false } } }
  }
});

new Chart(document.getElementById('catDoughnut'), {
  type: 'doughnut',
  data: {
    labels: DATA.catLabels,
    datasets: [{ data: DATA.catValues, backgroundColor: DATA.catColors, borderColor: '#1C212B', borderWidth: 2 }]
  },
  options: {
    cutout: '62%',
    plugins: { legend: { position: 'right', labels: { boxWidth: 12, padding: 14, font: { size: 11 } } } }
  }
});

new Chart(document.getElementById('monthLine'), {
  type: 'line',
  data: {
    labels: DATA.monthLabels,
    datasets: [{
      data: DATA.monthValues,
      borderColor: '#2FBF71',
      backgroundColor: 'rgba(47,191,113,0.12)',
      fill: true,
      tension: 0.35,
      pointBackgroundColor: '#2FBF71',
      pointRadius: 4
    }]
  },
  options: {
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true, grid: { color: '#313A48' } }, x: { grid: { display: false } } }
  }
});

const pct = DATA.budgetPct;
const gaugeColor = pct >= 100 ? '#E4573D' : (pct >= 80 ? '#E8B33D' : '#2FBF71');
new Chart(document.getElementById('gauge'), {
  type: 'doughnut',
  data: {
    datasets: [{
      data: [pct, 100 - pct],
      backgroundColor: [gaugeColor, '#2A3140'],
      borderWidth: 0,
      circumference: 180,
      rotation: 270,
      cutout: '75%'
    }]
  },
  options: { plugins: { legend: { display: false }, tooltip: { enabled: false } } }
});
document.getElementById('gaugePct').textContent = (DATA.budget > 0 ? pct.toFixed(1) + '%' : '—');
document.getElementById('gaugePct').style.color = gaugeColor;

const tbody = document.getElementById('top5Body');
DATA.top5.forEach(row => {
  const tr = document.createElement('tr');
  tr.innerHTML = `<td>${row.date}</td><td>${row.desc}</td><td><span class="tag">${row.cat}</span></td><td class="amount">₹${row.amount.toLocaleString('en-IN', {minimumFractionDigits:2})}</td>`;
  tbody.appendChild(tr);
});
</script>
</body>
</html>
"""


def main():
    ensure_storage()
    expenses = load_expenses()

    while True:
        print("""
========== PERSONAL EXPENSE TRACKER ==========
1. Add Expense
2. View All Expenses
3. Edit Expense
4. Delete Expense
5. Generate Report
6. Monthly Summary
7. Search / Filter
8. Set Monthly Budget
9. Budget Status
10. Smart Spending Insights
11. Visualize Expenses (matplotlib dashboard)
12. Export Visual Dashboard (HTML, all charts)
13. Save and Exit
===============================================
""")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            add_expense(expenses)
        elif choice == "2":
            display(expenses)
        elif choice == "3":
            edit_expense(expenses)
        elif choice == "4":
            delete_expense(expenses)
        elif choice == "5":
            generate_report(expenses)
        elif choice == "6":
            monthly_summary(expenses)
        elif choice == "7":
            search_filter(expenses)
        elif choice == "8":
            set_budget()
        elif choice == "9":
            budget_status(expenses)
        elif choice == "10":
            smart_insights(expenses)
        elif choice == "11":
            visualize(expenses)
        elif choice == "12":
            export_html_dashboard(expenses)
        elif choice == "13":
            save_expenses(expenses)
            print("Saved. Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1-13.")


if __name__ == "__main__":
    main()