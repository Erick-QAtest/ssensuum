"""Contabilidad de SSENSUUM: catálogo de cuentas y asientos de partida doble.

Los asientos no se guardan: se generan cada vez a partir del registro de servicios, de los pagos al equipo
y de los movimientos capturados en Finanzas. Así, corregir un servicio corrige también los estados financieros.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from .payroll import PAYOUTS_START

# La contabilidad arranca con los contratos del equipo: lo anterior entra como saldo inicial.
FINANCE_START = PAYOUTS_START

ASSET, LIABILITY, EQUITY, INCOME, COST, EXPENSE = "activo", "pasivo", "capital", "ingreso", "costo", "gasto"

# Cuentas de dinero: de aquí sale y aquí entra el flujo de efectivo.
CASH_ACCOUNTS = {"caja": "Caja (efectivo)", "banco": "Banco", "mercadopago": "Mercado Pago"}
# Cómo se cobró un servicio → a qué cuenta entra el dinero.
PAYMENT_METHOD_ACCOUNT = {"efectivo": "caja", "tarjeta": "banco", "transferencia": "banco", "mercadopago": "mercadopago"}
# Los honorarios se pagan por transferencia (cláusula CUARTA).
PAYOUT_ACCOUNT = "banco"

EXPENSE_CATEGORIES = {
    "renta": "Renta",
    "servicios": "Luz, agua, gas e internet",
    "insumos": "Insumos, blancos y aceites",
    "limpieza": "Limpieza y lavandería",
    "publicidad": "Publicidad y marketing",
    "comisiones": "Comisiones bancarias y de cobro",
    "mantenimiento": "Mantenimiento y reparaciones",
    "nomina": "Sueldos administrativos",
    "software": "Software y suscripciones",
    "impuestos": "Impuestos y derechos",
    "intereses": "Intereses",
    "otros": "Otros gastos",
}
OTHER_INCOME_CATEGORIES = {
    "limpieza": "Aportaciones de limpieza cobradas aparte",
    "otros": "Otros ingresos",
}

ACCOUNTS: dict[str, tuple[str, str]] = {
    **{code: (ASSET, label) for code, label in CASH_ACCOUNTS.items()},
    "activo_fijo": (ASSET, "Mobiliario y equipo"),
    "honorarios_por_pagar": (LIABILITY, "Honorarios por pagar a masajistas"),
    "propinas_por_pagar": (LIABILITY, "Propinas por entregar"),
    "prestamos": (LIABILITY, "Préstamos por pagar"),
    "capital": (EQUITY, "Capital aportado"),
    "retiros": (EQUITY, "Retiros del dueño"),
    "ingresos_servicios": (INCOME, "Ingresos por servicios"),
    "ingreso_limpieza": (INCOME, "Aportaciones de limpieza"),
    "otros_ingresos": (INCOME, "Otros ingresos"),
    "honorarios": (COST, "Honorarios de masajistas"),
    **{f"gasto:{code}": (EXPENSE, label) for code, label in EXPENSE_CATEGORIES.items()},
}

# Movimientos que se capturan a mano: (etiqueta, sección del flujo de efectivo).
MOVEMENT_KINDS = {
    "gasto": ("Gasto", "operacion"),
    "ingreso": ("Otro ingreso", "operacion"),
    "saldo_inicial": ("Saldo inicial", "inicial"),
    "aportacion": ("Aportación de capital", "financiamiento"),
    "retiro": ("Retiro del dueño", "financiamiento"),
    "prestamo": ("Préstamo recibido", "financiamiento"),
    "pago_prestamo": ("Pago de préstamo", "financiamiento"),
    "activo": ("Compra de mobiliario o equipo", "inversion"),
    "traspaso": ("Traspaso entre cuentas", "traspaso"),
}


@dataclass
class Entry:
    """Asiento contable. flow agrupa su efecto en el flujo de efectivo (sección, concepto)."""

    day: date
    memo: str
    flow: tuple[str, str]
    lines: list[tuple[str, int, int]] = field(default_factory=list)  # (cuenta, debe, haber)

    def debit(self, account: str, amount: int) -> "Entry":
        if amount:
            self.lines.append((account, amount, 0))
        return self

    def credit(self, account: str, amount: int) -> "Entry":
        if amount:
            self.lines.append((account, 0, amount))
        return self

    def cash_delta(self) -> int:
        return sum(debit - credit for account, debit, credit in self.lines if account in CASH_ACCOUNTS)


def movement_entry(day: date, kind: str, amount: int, account: str, category: Optional[str], to_account: Optional[str], memo: str) -> Entry:
    section = MOVEMENT_KINDS[kind][1]
    if kind == "gasto":
        return Entry(day, memo, (section, EXPENSE_CATEGORIES[category])).debit(f"gasto:{category}", amount).credit(account, amount)
    if kind == "ingreso":
        income = "ingreso_limpieza" if category == "limpieza" else "otros_ingresos"
        return Entry(day, memo, (section, OTHER_INCOME_CATEGORIES[category])).debit(account, amount).credit(income, amount)
    if kind in ("saldo_inicial", "aportacion"):
        return Entry(day, memo, (section, MOVEMENT_KINDS[kind][0])).debit(account, amount).credit("capital", amount)
    if kind == "retiro":
        return Entry(day, memo, (section, "Retiros del dueño")).debit("retiros", amount).credit(account, amount)
    if kind == "prestamo":
        return Entry(day, memo, (section, "Préstamos recibidos")).debit(account, amount).credit("prestamos", amount)
    if kind == "pago_prestamo":
        return Entry(day, memo, (section, "Pagos de préstamos")).debit("prestamos", amount).credit(account, amount)
    if kind == "activo":
        return Entry(day, memo, (section, "Compra de mobiliario y equipo")).debit("activo_fijo", amount).credit(account, amount)
    if kind == "traspaso":
        return Entry(day, memo, (section, "Traspasos")).debit(to_account, amount).credit(account, amount)
    raise ValueError(kind)


def balances(entries: list[Entry]) -> dict[str, int]:
    """Saldo de cada cuenta en su naturaleza: deudora para activo, costo y gasto; acreedora para las demás."""
    result: dict[str, int] = {}
    for entry in entries:
        for account, debit, credit in entry.lines:
            nature = ACCOUNTS[account][0]
            sign = 1 if nature in (ASSET, COST, EXPENSE) or account == "retiros" else -1
            result[account] = result.get(account, 0) + sign * (debit - credit)
    return result


def income_statement(entries: list[Entry]) -> dict:
    totals = balances(entries)
    services = totals.get("ingresos_servicios", 0)
    fees = totals.get("honorarios", 0)
    expenses = [
        {"account": code, "label": ACCOUNTS[code][1], "amount": totals[code]}
        for code in ACCOUNTS if code.startswith("gasto:") and totals.get(code)
    ]
    other = [
        {"account": code, "label": ACCOUNTS[code][1], "amount": totals[code]}
        for code in ("ingreso_limpieza", "otros_ingresos") if totals.get(code)
    ]
    gross_profit = services - fees
    operating_expenses = sum(row["amount"] for row in expenses)
    other_income = sum(row["amount"] for row in other)
    net = gross_profit - operating_expenses + other_income
    return {
        "revenue": services,
        "costOfServices": fees,
        "grossProfit": gross_profit,
        "expenses": expenses,
        "operatingExpenses": operating_expenses,
        "operatingIncome": gross_profit - operating_expenses,
        "otherIncome": other,
        "otherIncomeTotal": other_income,
        "netIncome": net,
        "netMargin": round(net / services * 100, 1) if services else None,
    }


FLOW_SECTIONS = {"inicial": "Saldos iniciales", "operacion": "Operación", "inversion": "Inversión", "financiamiento": "Financiamiento"}


def cash_flow(before: list[Entry], during: list[Entry]) -> dict:
    opening = {code: balances(before).get(code, 0) for code in CASH_ACCOUNTS}
    sections: dict[str, dict[str, int]] = {key: {} for key in FLOW_SECTIONS}
    for entry in during:
        section, concept = entry.flow
        if section == "traspaso":
            continue
        delta = entry.cash_delta()
        if delta:
            sections[section][concept] = sections[section].get(concept, 0) + delta
    closing = {code: opening[code] + balances(during).get(code, 0) for code in CASH_ACCOUNTS}
    rows = [
        {
            "section": key,
            "label": label,
            "items": [{"label": concept, "amount": amount} for concept, amount in sorted(sections[key].items(), key=lambda item: -abs(item[1]))],
            "total": sum(sections[key].values()),
        }
        for key, label in FLOW_SECTIONS.items()
    ]
    return {
        "opening": sum(opening.values()),
        "sections": [row for row in rows if row["items"]],
        "netChange": sum(row["total"] for row in rows),
        "closing": sum(closing.values()),
        "accounts": [
            {"account": code, "label": label, "opening": opening[code], "closing": closing[code]}
            for code, label in CASH_ACCOUNTS.items()
        ],
    }


def balance_sheet(entries: list[Entry]) -> dict:
    totals = balances(entries)

    def group(nature: str) -> list[dict]:
        return [
            {"account": code, "label": label, "amount": totals.get(code, 0)}
            for code, (kind, label) in ACCOUNTS.items()
            if kind == nature and code != "retiros" and (totals.get(code) or code in CASH_ACCOUNTS)
        ]

    assets = group(ASSET)
    liabilities = group(LIABILITY)
    retained = income_statement(entries)["netIncome"]
    equity = [
        {"account": "capital", "label": ACCOUNTS["capital"][1], "amount": totals.get("capital", 0)},
        {"account": "retiros", "label": ACCOUNTS["retiros"][1], "amount": -totals.get("retiros", 0)},
        {"account": "resultados", "label": "Utilidades acumuladas", "amount": retained},
    ]
    total_assets = sum(row["amount"] for row in assets)
    total_liabilities = sum(row["amount"] for row in liabilities)
    total_equity = sum(row["amount"] for row in equity)
    return {
        "assets": assets,
        "totalAssets": total_assets,
        "liabilities": liabilities,
        "totalLiabilities": total_liabilities,
        "equity": [row for row in equity if row["amount"] or row["account"] != "retiros"],
        "totalEquity": total_equity,
        "balanced": total_assets == total_liabilities + total_equity,
    }
