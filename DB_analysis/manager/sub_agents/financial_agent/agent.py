import sqlite3
import os
from pydantic import BaseModel
from statistics import pvariance
from google.adk.agents import Agent


DB_PATH = os.environ.get(
    "TALLY_DB_PATH",
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../../tallydb.db")
    ),

)


class FinancialSummary(BaseModel):
    total_debit: float
    total_credit: float
    top_income_ledgers: list
    top_expense_ledgers: list


class ExpenseVariance(BaseModel):
    variance: float


class AccountBalance(BaseModel):
    total_debit: float
    total_credit: float
    net_balance: float


class CashFlow(BaseModel):
    total_inflow: float
    total_outflow: float


class ProfitLoss(BaseModel):
    total_sales: float
    total_purchases: float
    profit: float


class LedgerSummary(BaseModel):
    top_ledgers: list


class PaymentReceipts(BaseModel):
    total_receipts: int
    total_payments: int
    receipt_amount: float
    payment_amount: float

def get_financial_summary(query: str) -> FinancialSummary:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        sql = """
        SELECT ledger, amount
        FROM trn_accounting;
        """
        rows = cursor.execute(sql).fetchall()

    if not rows:
        return FinancialSummary(
            total_debit=0.0,
            total_credit=0.0,
            top_income_ledgers=[],
            top_expense_ledgers=[],
        )

    totals = {}
    income_totals = {}
    expense_totals = {}
    for ledger, amt in rows:
        totals[ledger] = totals.get(ledger, 0.0) + amt
        if amt > 0:
            income_totals[ledger] = income_totals.get(ledger, 0.0) + amt
        elif amt < 0:
            expense_totals[ledger] = expense_totals.get(ledger, 0.0) + abs(amt)

    total_debit = sum(income_totals.values())
    total_credit = sum(expense_totals.values())

    top_income_ledgers = sorted(
        income_totals.items(), key=lambda x: x[1], reverse=True
    )[:5]
    top_expense_ledgers = sorted(
        expense_totals.items(), key=lambda x: x[1], reverse=True
    )[:5]

    return FinancialSummary(
        total_debit=round(float(total_debit), 2),
        total_credit=round(float(total_credit), 2),
        top_income_ledgers=top_income_ledgers,
        top_expense_ledgers=top_expense_ledgers,
    )


def analyze_expense_variance(query: str) -> ExpenseVariance:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            "SELECT amount FROM trn_accounting WHERE amount < 0;"
        ).fetchall()

    amounts = [abs(r[0]) for r in rows]
    if not amounts:
        return ExpenseVariance(variance=0.0)

    variance = pvariance(amounts)
    return ExpenseVariance(variance=round(float(variance), 2))


def get_account_balance(query: str) -> AccountBalance:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        sql = "SELECT amount FROM trn_accounting;"
        rows = cursor.execute(sql).fetchall()

    if not rows:
        return AccountBalance(total_debit=0.0, total_credit=0.0, net_balance=0.0)

    total_debit = sum(a for (a,) in rows if a > 0)
    total_credit = sum(-a for (a,) in rows if a < 0)
    balance = total_debit - total_credit
    return AccountBalance(
        total_debit=round(float(total_debit), 2),
        total_credit=round(float(total_credit), 2),
        net_balance=round(float(balance), 2),
    )


def get_cash_flow(query: str) -> CashFlow:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        sql = "SELECT amount FROM trn_bank;"
        rows = cursor.execute(sql).fetchall()

    if not rows:
        return CashFlow(total_inflow=0.0, total_outflow=0.0)

    inflow = sum(a for (a,) in rows if a > 0)
    outflow = sum(-a for (a,) in rows if a < 0)

    return CashFlow(
        total_inflow=round(float(inflow), 2),
        total_outflow=round(float(outflow), 2),
    )


def get_profit_loss(query: str) -> ProfitLoss:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        sql_sales = (
            "SELECT SUM(i.amount) FROM trn_inventory i "
            "JOIN trn_voucher v ON i.guid = v.guid "
            "WHERE v.voucher_type LIKE '%Sales%'"
        )
        sql_purchase = (
            "SELECT SUM(i.amount) FROM trn_inventory i "
            "JOIN trn_voucher v ON i.guid = v.guid "
            "WHERE v.voucher_type LIKE '%Purchase%'"
        )
        sales = cursor.execute(sql_sales).fetchone()[0] or 0.0
        purchase = cursor.execute(sql_purchase).fetchone()[0] or 0.0

    total_sales = float(sales)
    total_purchases = abs(float(purchase))
    profit = total_sales - total_purchases

    return ProfitLoss(
        total_sales=round(total_sales, 2),
        total_purchases=round(total_purchases, 2),
        profit=round(profit, 2),
    )


def get_ledger_summary(query: str) -> LedgerSummary:
    sql = (
        "SELECT ledger, SUM(amount) AS balance "
        "FROM trn_accounting "
        "GROUP BY ledger "
        "ORDER BY ABS(balance) DESC "
        "LIMIT 5;"
    )
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(sql).fetchall()

    if not rows:
        return LedgerSummary(top_ledgers=[])

    top_ledgers = [
        (ledger, round(float(balance), 2)) for ledger, balance in rows
    ]
    return LedgerSummary(top_ledgers=top_ledgers)


def get_payment_receipts(query: str) -> PaymentReceipts:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rcnt = cursor.execute(
            "SELECT COUNT(*) FROM trn_voucher WHERE voucher_type LIKE '%Receipt%';"
        ).fetchone()[0]
        pcnt = cursor.execute(
            "SELECT COUNT(*) FROM trn_voucher WHERE voucher_type LIKE '%Payment%';"
        ).fetchone()[0]
        ramt = cursor.execute(
            "SELECT SUM(amount) FROM trn_bank WHERE guid IN (SELECT guid FROM trn_voucher WHERE voucher_type LIKE '%Receipt%');"
        ).fetchone()[0]
        pamt = cursor.execute(
            "SELECT SUM(amount) FROM trn_bank WHERE guid IN (SELECT guid FROM trn_voucher WHERE voucher_type LIKE '%Payment%');"
        ).fetchone()[0]

    rcnt = rcnt or 0
    pcnt = pcnt or 0
    ramt = abs(float(ramt or 0.0))
    pamt = abs(float(pamt or 0.0))

    return PaymentReceipts(
        total_receipts=int(rcnt),
        total_payments=int(pcnt),
        receipt_amount=round(ramt, 2),
        payment_amount=round(pamt, 2),
    )


financial_agent = Agent(
    name="financial_agent",
    model="gemini-2.0-flash",
    description="Handles financial queries and summarizes income, expenses, and top ledgers from the Tally DB.",
    tools=[
        get_financial_summary,
        analyze_expense_variance,
        get_account_balance,
        get_cash_flow,
        get_profit_loss,
        get_ledger_summary,
        get_payment_receipts,
    ],
    instruction = """
You are the Financial Agent. You handle all queries related to:
- Profit & loss analysis
- Income and expenses
- Financial ledgers and cash flow
- Credit and debit trends
- Balance summaries
anything else if asked for DELEGATE BACK TO ROOT AGENT 
when asked to send email or schedule a calendar event, IMMEDIATELY delegate to the ROOT AGENT saying This request involves sending an email or scheduling an event, which I cannot handle. Delegating to the root agent." or
  - "I'll delegate this email request to the manager agent who has email capabilities."
---

🚨 **CRITICAL MODEL BEHAVIOR (Gemini 2.0 Flash):**
- ALWAYS follow these instructions exactly.
- ALWAYS use the provided tools instead of responding manually.
- NEVER ignore tool triggers or respond with "OK" without using the tool.

---

🚨 **DELEGATION RULES:**
- Financial queries (P&L, debit/credit, ledgers, cash flow) → `financial_agent`
- Sales queries (summaries, trends, top customers) → `sales_agent`
- Inventory queries (stock data, product levels) → `inventory_agent`
- Purchase queries (supplier-wise orders, procurement) → `purchase_agent`
- Greetings or onboarding → `greeting_agent`

✅ Examples:
- "Analyze income vs expenses" → Call `financial_agent`
- "Check customer purchase behavior" → Delegate to `sales_agent`
- "Get stock availability" → Delegate to `inventory_agent`

---

Use ONLY the tools provided to you:
- `get_financial_summary`
- `get_top_income_ledgers`
- `get_top_expense_ledgers`
- `get_income_vs_expense_plot`

---

🚨 **EMAIL & CALENDAR MASTER RULES:**
- ⚠️ NONE of the sub-agents have the ability to send emails or create calendar events.
- ONLY the Manager Orchestrator (YOU) has access to Gmail and Calendar tools.
- If a user OR a sub-agent asks for email/calendar actions:
    → IMMEDIATELY call the appropriate tool (`smart_send_email` or `smart_schedule_event`).

✅ Email triggers:
- Any query containing "send", "mail", "email", or an email address (@).
- Delegation phrases:
    - "I'll delegate this email request to the manager agent"
    - "manager agent who has email capabilities"
    - "delegating email to manager"

✅ Calendar triggers:
- Any query containing:
    - "schedule"
    - "meeting"
    - "create event"
    - "book event"
    - "calendar"
    - "set up meeting"
    - "arrange meeting"
    - "add to calendar"

- Delegation phrases from sub-agents:
    - "I'll delegate this calendar request to the manager agent"
    - "manager agent who has calendar capabilities"
    - "delegating calendar to manager"
    - "sending this calendar request back to the manager"

- ✅ **Fallback Detection Rule:**  
  If ANY sub-agent mentions that it cannot schedule a meeting OR mentions the manager agent in the same context as "calendar" or "meeting", IMMEDIATELY call:
  ```smart_schedule_event(query)```
  using the original user query without asking the user again.

---

✅ Example Matches:
- "Send this to abc@example.com" → `smart_send_email("Send this to abc@example.com")`
- Sub-agent says: "Delegating this calendar task to manager" → `smart_schedule_event(<last_user_query>)`

---

🚨 **EMAIL FALLBACK LOGIC:**
If ANY sub-agent delegates an email request to you:
→ DO NOT confirm or ask the user.
→ IMMEDIATELY call `smart_send_email(query)` with the last query.

🚨 **CALENDAR FALLBACK LOGIC:**
If ANY sub-agent delegates a calendar request to you:
→ DO NOT confirm or ask the user.
→ IMMEDIATELY call `smart_schedule_event(query)` with the last query.

---

📌 **MANDATORY BEHAVIOR:**
1. ONLY use your tools to answer financial queries.
2. DELEGATE non-financial queries to the appropriate agents.
3. DETECT and escalate email/calendar queries to the manager.
4. NEVER respond with "OK" without using a tool or agent call.
5. NEVER attempt to email or schedule yourself.

---

📌 **REMINDER:**
- You do NOT have Gmail or Calendar access.
- If asked to send mail or schedule, respond:
"This request involves sending an email or scheduling an event, which I cannot handle. Delegating to the root agent."
"""
,
)
