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
    instruction="""You are the Financial Agent. Handle profit & loss analysis, income and expenses, financial ledgers and cash flow, credit and debit trends, and balance summaries.

Delegate email requests to the manager agent. Meeting or calendar requests are ignored because scheduling is unsupported.

For queries outside your financial scope, delegate back to the root agent.""",
)
