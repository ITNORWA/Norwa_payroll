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
frappe.db.exists = lambda dt, n: False # Mock: Component doesn't exist
frappe.parse_json = lambda x: x if isinstance(x, (dict, list)) else {} # Simple mock

sys.modules["frappe"] = frappe
sys.modules["frappe.model"] = frappe.model
sys.modules["frappe.model.mapper"] = frappe.model.mapper
sys.modules["frappe.db"] = frappe.db

# Mock Document for new_doc
class MockDoc:
    def __init__(self, doctype):
        self.flags = types.SimpleNamespace()
    def save(self): pass

frappe.new_doc = lambda dt: MockDoc(dt)

# Now import the logic
import os
sys.path.append(os.getcwd()) # Append Root for package discovery

# Note: We can't import `apply_kenya_structure` easily because it calls db.get_single_value at runtime.
# But `calculate_paye_2026` is pure math.
# To verify the formula dynamic generation, we should import `apply_kenya_structure`.
# However, importing utils might execute top level code? No functions only.
from norwa_payroll.norwa_payroll.utils import calculate_paye_2026, apply_kenya_structure

def verify_payroll():
    print("Verifying Kenya Payroll Logic (2025 vs 2026)...")
    
    # ---------------------------
    # Test Cases: User Requested Salaries
    # ---------------------------
    test_salaries = [20000, 45000, 65000, 75000, 100000, 150000, 200000]
    
    for year, nssf_limits in [("2025", (8000, 72000)), ("2026", (9000, 108000))]:
        mock_settings["tax_regime"] = year
        print(f"\n{'='*50}")
        print(f"  TESTING {year} REGIME (NSSF Limits: {nssf_limits})")
        print(f"{'='*50}")
        print(f"{'Gross':<10} | {'NSSF':<10} | {'SHIF':<10} | {'AHL':<10} | {'Taxable':<10} | {'PAYE':<10} | {'Net Pay':<10}")
        print("-" * 80)
        
        t1_lim, t2_lim = nssf_limits
        
        for gross in test_salaries:
            # 1. NSSF
            # Tier I
            nssf1 = min(gross, t1_lim) * 0.06
            # Tier II
            if gross > t1_lim:
                nssf2 = (min(gross, t2_lim) - t1_lim) * 0.06
            else:
                nssf2 = 0
            
            nssf_total = nssf1 + nssf2
            
            # 2. SHIF (2.75%)
            shif = gross * 0.0275
            
            # 3. AHL (1.5%)
            ahl = gross * 0.015
            
            # 4. PAYE
            # Note: We call the function, which handles reliefs internally
            paye = calculate_paye_2026(gross, nssf1, nssf2, shif, ahl)
            
            # 5. Net Pay
            net = gross - nssf_total - shif - ahl - paye
            
            # Taxable (For display comparison) is Gross - NSSF - SHIF (Deductible)
            taxable = gross - nssf_total - shif
            
            print(f"{gross:<10} | {nssf_total:<10.2f} | {shif:<10.2f} | {ahl:<10.2f} | {taxable:<10.2f} | {paye:<10.2f} | {net:<10.2f}")


if __name__ == "__main__":
    verify_payroll()
