import sys
import types

# Mock frappe module structure
frappe = types.ModuleType("frappe")
frappe.whitelist = lambda: lambda x: x
frappe.model = types.ModuleType("frappe.model")
frappe.model.mapper = types.ModuleType("frappe.model.mapper")
frappe.model.mapper.get_mapped_doc = lambda x: x
frappe.db = types.ModuleType("frappe.db")

# Mock Settings State
mock_settings = {"tax_regime": "2025"}
frappe.db.get_single_value = lambda dt, f: mock_settings.get(f)

sys.modules["frappe"] = frappe
sys.modules["frappe.model"] = frappe.model
sys.modules["frappe.model.mapper"] = frappe.model.mapper
sys.modules["frappe.db"] = frappe.db

# Now import the logic
import os
sys.path.append(os.path.join(os.getcwd(), "norwa_payroll"))

# Note: We can't import `apply_kenya_structure` easily because it calls db.get_single_value at runtime.
# But `calculate_paye_2026` is pure math.
# To verify the formula dynamic generation, we should import `apply_kenya_structure`.
# However, importing utils might execute top level code? No functions only.
from norwa_payroll.utils import calculate_paye_2026, apply_kenya_structure

def verify_payroll():
    print("Verifying Kenya Payroll Logic (2025 vs 2026)...")
    
    # ---------------------------
    # Test 1: 2025 Regime (NSSF Limit 72,000 / 8,000)
    # ---------------------------
    mock_settings["tax_regime"] = "2025"
    print("\n--- Testing 2025 Regime (NSSF Max 72k/8k) ---")
    
    # Check Formulas
    data = apply_kenya_structure("{}")
    
    # Extract NSSF Formula strings to verify
    nssf1_f = next(d['formula'] for d in data['deductions'] if d['abbr'] == 'NSSF1')
    nssf2_f = next(d['formula'] for d in data['deductions'] if d['abbr'] == 'NSSF2')
    
    print(f"NSSF1 Formula: {nssf1_f}")
    print(f"NSSF2 Formula: {nssf2_f}")
    
    if "8000" in nssf1_f and "72000" in nssf2_f:
         print("[PASS] 2025 Formulas use 8,000 and 72,000 limits.")
    else:
         print("[FAIL] 2025 Formulas incorrect.")

    # ---------------------------
    # Test 2: 2026 Regime (NSSF Limit 108,000 / 9,000)
    # ---------------------------
    mock_settings["tax_regime"] = "2026"
    print("\n--- Testing 2026 Regime (NSSF Max 108k/9k) ---")
    
    data = apply_kenya_structure("{}")
    nssf1_f = next(d['formula'] for d in data['deductions'] if d['abbr'] == 'NSSF1')
    nssf2_f = next(d['formula'] for d in data['deductions'] if d['abbr'] == 'NSSF2')
    
    print(f"NSSF1 Formula: {nssf1_f}")
    print(f"NSSF2 Formula: {nssf2_f}")
    
    if "9000" in nssf1_f and "108000" in nssf2_f:
         print("[PASS] 2026 Formulas use 9,000 and 108,000 limits.")
    else:
         print("[FAIL] 2026 Formulas incorrect.")

    # ---------------------------
    # Test 3: PAYE Calculation (Unchanged logic, just verification of import)
    # ---------------------------
    paye = calculate_paye_2026(50000, 540, 2460, 1375, 750)
    if paye > 1000:
        print(f"\n[PASS] PAYE Calc Functional: {paye}")

if __name__ == "__main__":
    verify_payroll()
