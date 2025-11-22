import unittest
from unittest.mock import patch
from verity_check.knowledge_graph import build_graph
from verity_check.consistency_check import run_checks

class TestVerityGraph(unittest.TestCase):
    
    def test_full_pipeline_logic(self):
        # Mock extracted data representing a problematic application
        extracted_data = [
            # 1. Passport (Identity)
            {
                "data": {
                    "surname": "Mustermann",
                    "given_names": "Hans",
                    "date_of_birth": "1980-01-01",
                    "valid_from": "2020-01-01",
                    "valid_until": "2030-01-01"
                },
                "metadata": {"filename": "passport.jpg", "category": "Identity"}
            },
            # 2. Payslip (Identity Mismatch + Low Income)
            {
                "data": {
                    "employee_name": "Meier", # Mismatch with Mustermann (surname only or full name? Code expects full name usually, but let's put just Meier to trigger mismatch)
                    # Actually, knowledge_graph constructs full name for Identity, but for Livelihood it takes the raw string.
                    # Identity: "Hans Mustermann"
                    # Livelihood: "Meier"
                    # Ratio("Hans Mustermann", "Meier") -> < 0.9
                    "net_income": 1000.00,
                    "total_warm_rent": 0 
                },
                "metadata": {"filename": "payslip.jpg", "category": "Livelihood"}
            },
            # 3. Rent Contract (High Rent)
            {
                "data": {
                    "total_warm_rent": 600.00,
                    "net_income": 0
                },
                "metadata": {"filename": "rent.jpg", "category": "Livelihood"}
            },
            # 4. Residence Permit 1 (Gap)
            {
                "data": {
                    "valid_from": "2015-01-01",
                    "valid_until": "2017-01-01"
                },
                "metadata": {"filename": "permit1.jpg", "category": "Identity"}
            },
            # 5. Residence Permit 2 (Gap start 2018)
            {
                "data": {
                    "valid_from": "2018-01-01", # 1 year gap
                    "valid_until": "2020-01-01"
                },
                "metadata": {"filename": "permit2.jpg", "category": "Identity"}
            }
        ]
        
        # Build Graph
        G = build_graph(extracted_data)
        
        # Run Checks
        alerts = run_checks(G)
        
        print("\n=== Test Alerts Generated ===")
        for a in alerts:
            print(f"[{a['check']}] {a['message']}")
            
        # Assertions
        alert_types = [a['check'] for a in alerts]
        
        # 1. Identity Check
        self.assertIn("Identity Consistency", alert_types)
        # 2. Residence Check (Gap + Duration < 5 years (2+2=4))
        self.assertIn("Residence Timeline", alert_types)
        # 3. Livelihood Check (1000 - 600 = 400 < 563)
        self.assertIn("Livelihood Calculation", alert_types)
        
if __name__ == "__main__":
    unittest.main()
