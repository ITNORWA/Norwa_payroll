import frappe
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def apply_kenya_structure(doc):
    """
    Applies Kenya 2026 Salary Structure Components and Formulas.
    Expected to be called from the Salary Structure form via button.
    """
    if isinstance(doc, str):
        doc = frappe.parse_json(doc)
    
    # Ensure Components Exist
    create_kenya_components()

    # Define Kenya 2026 Components
    # Earnings
    # We don't overwrite earnings unless empty, or we append key allowances if missing?
    # User said: "It should have salarcy components... create payroll formula"
    # User said: "on the salary structure assignment it should just allow me to use my app structure instead of salary structure on the system."
    # Wait, the prompt said: "Instead of using salary structure... on top of salary structure doctype it gives me a button that allows me to use the calculations of the app"
    # So we should populate the Earnings/Deductions child tables.

    # We will return the list of rows to be added/updated in JS.
    # But since we have the doc here (passed as json), we can modify and return it?
    # Actually, usually simpler to return a dict of components and let JS add them.
    # However, for complex replacement, let's prepare the rows.

    data = {
        "earnings": [],
        "deductions": []
    }

    # Get Tax Regime
    tax_regime = frappe.db.get_single_value("Norwa Payroll Settings", "tax_regime") or "2025"
    
    # NSSF Configuration
    # 2025: Tier I Limit = 8,000. Tier II Limit = 72,000.
    # 2026: Tier I Limit = 9,000. Tier II Limit = 108,000.
    
    if tax_regime == "2026":
        t1_limit = 9000
        t2_limit = 108000
    else:
        # Default 2025
        t1_limit = 8000
        t2_limit = 72000

    default_abbrs = {
        "NSSF Tier I": "NSSF1",
        "NSSF Tier II": "NSSF2",
        "SHIF": "SHIF",
        "Housing Levy": "AHL",
        "PAYE": "PAYE",
        "Personal Relief": "PR",
        "Basic Salary": "BS",
        "House Allowance": "HA",
        "Transport Allowance": "TA",
        "Taxable Pay": "TP",
    }
    abbrs = _get_component_abbrs(default_abbrs)
    nssf1_abbr = abbrs["NSSF Tier I"]
    nssf2_abbr = abbrs["NSSF Tier II"]
    shif_abbr = abbrs["SHIF"]
    ahl_abbr = abbrs["Housing Levy"]
    paye_abbr = abbrs["PAYE"]

    # Earnings
    data["earnings"].append({
        "salary_component": "Basic Salary",
        "abbr": abbrs["Basic Salary"],
        "amount": 0
    })
    data["earnings"].append({
        "salary_component": "House Allowance",
        "abbr": abbrs["House Allowance"],
        "amount": 0
    })
    data["earnings"].append({
        "salary_component": "Transport Allowance",
        "abbr": abbrs["Transport Allowance"],
        "amount": 0
    })
    data["earnings"].append({
        "salary_component": "Taxable Pay",
        "abbr": abbrs["Taxable Pay"],
        "amount_based_on_formula": 1,
        "formula": f"gross_pay - {nssf1_abbr} - {nssf2_abbr} - {shif_abbr}",
        "statistical_component": 1,
        "do_not_include_in_total": 1
    })

    # Deductions
    data["deductions"].append({
        "salary_component": "NSSF Tier I",
        "abbr": nssf1_abbr,
        "amount_based_on_formula": 1,
        "formula": f"min(gross_pay, {t1_limit}) * 0.06",
        "condition": "gross_pay > 0"
    })
    
    data["deductions"].append({
        "salary_component": "NSSF Tier II",
        "abbr": nssf2_abbr,
        "amount_based_on_formula": 1,
        "formula": f"(min(gross_pay, {t2_limit}) - {t1_limit}) * 0.06 if gross_pay > {t1_limit} else 0",
        "condition": f"gross_pay > {t1_limit}"
    })
    
    data["deductions"].append({
        "salary_component": "SHIF",
        "abbr": shif_abbr,
        "amount_based_on_formula": 1,
        "formula": "gross_pay * 0.0275",
        "condition": "gross_pay > 0"
    })
    
    data["deductions"].append({
        "salary_component": "Housing Levy",
        "abbr": ahl_abbr,
        "amount_based_on_formula": 1,
        "formula": "gross_pay * 0.015",
        "condition": "gross_pay > 0"
    })
    
    data["deductions"].append({
        "salary_component": "Personal Relief",
        "abbr": abbrs["Personal Relief"],
        "amount_based_on_formula": 1,
        "formula": f"2400 if (gross_pay - {nssf1_abbr} - {nssf2_abbr} - {shif_abbr}) > 0 else 0",
        "statistical_component": 1,
        "do_not_include_in_total": 1
    })

    # PAYE
    # Formula uses calculated NSSF values (referenced by abbr NSSF1, NSSF2)
    # The logic remains the same: Taxable = Gross - NSSF - SHIF
    # Tax Bands currently assumed same for 2025/2026.
    
    data["deductions"].append({
        "salary_component": "PAYE",
        "abbr": paye_abbr,
        "amount_based_on_formula": 1,
        "formula": (
            "norwa_payroll.norwa_payroll.utils.calculate_paye_2026"
            f"(gross_pay, {nssf1_abbr}, {nssf2_abbr}, {shif_abbr}, {ahl_abbr})"
        ),
        "condition": "gross_pay > 0"
    })

    return data

@frappe.whitelist()
def calculate_paye_2026(gross_pay, nssf1, nssf2, shif, ahl):
    """
    Calculates PAYE for Kenya 2026 based on Taxable Income.
    Taxable = Gross - Allowable Deductions (NSSF, SHIF).
    Deducts Personal Relief and Housing Relief.
    """
    taxable = gross_pay - nssf1 - nssf2 - shif
    if taxable <= 0:
        return 0

    tax = 0
    # Band 1: 0 - 24,000 @ 10%
    b1 = 24000
    if taxable > 0:
        tax += min(taxable, b1) * 0.10
    
    # Band 2: 24,001 - 32,333 @ 25% (Width 8,333)
    b2 = 8333
    if taxable > 24000:
        tax += min(taxable - 24000, b2) * 0.25
        
    # Band 3: 32,334 - 500,000 @ 30% (Width 467,667)
    b3 = 467667
    if taxable > 32333:
        tax += min(taxable - 32333, b3) * 0.30
        
    # Band 4: 500,001 - 800,000 @ 32.5% (Width 300,000)
    b4 = 300000
    if taxable > 500000:
        tax += min(taxable - 500000, b4) * 0.325
        
    # Band 5: > 800,000 @ 35%
    if taxable > 800000:
        tax += (taxable - 800000) * 0.35

    # Reliefs
    personal_relief = 2400
    housing_relief = min(ahl * 0.15, 9000) # Cap at 9k/month? (Check law, search said 9000/month or 108k/annum. Correct).

    net_tax = tax - personal_relief - housing_relief
    return max(net_tax, 0)

def create_kenya_components():
    """ Creates Salary Components if not existing """
    components = [
        {"name": "NSSF Tier I", "type": "Deduction", "abbr": "NSSF1"},
        {"name": "NSSF Tier II", "type": "Deduction", "abbr": "NSSF2"},
        {"name": "SHIF", "type": "Deduction", "abbr": "SHIF"},
        {"name": "Housing Levy", "type": "Deduction", "abbr": "AHL"},
        {"name": "PAYE", "type": "Deduction", "abbr": "PAYE"},
        {"name": "Personal Relief", "type": "Deduction", "abbr": "PR", "statistical": True},
        {"name": "Basic Salary", "type": "Earning", "abbr": "BS"},
        {"name": "House Allowance", "type": "Earning", "abbr": "HA"},
        {"name": "Transport Allowance", "type": "Earning", "abbr": "TA"},
        {"name": "Taxable Pay", "type": "Earning", "abbr": "TP", "statistical": True},
    ]

    for comp in components:
        existing = frappe.db.exists("Salary Component", comp["name"])
        if existing:
            if comp.get("statistical"):
                doc = frappe.get_doc("Salary Component", comp["name"])
                if _set_statistical_flags(doc):
                    doc.flags.ignore_permissions = True
                    doc.save()
            continue

        doc = frappe.new_doc("Salary Component")
        doc.salary_component = comp["name"]
        doc.type = comp["type"]
        doc.salary_component_abbr = comp["abbr"]
        if comp.get("statistical"):
            _set_statistical_flags(doc)
        doc.flags.ignore_permissions = True
        doc.save()


def _set_statistical_flags(doc):
    updated = False
    for fieldname in ("statistical_component", "is_statistical_component", "do_not_include_in_total"):
        if doc.meta.get_field(fieldname) and not doc.get(fieldname):
            doc.set(fieldname, 1)
            updated = True
    return updated


def _get_component_abbrs(default_abbrs):
    abbrs = {}
    for name, fallback in default_abbrs.items():
        abbr = frappe.db.get_value("Salary Component", name, "salary_component_abbr")
        abbrs[name] = abbr or fallback
    return abbrs


# Alias for Hooks
setup_payroll = create_kenya_components
