#!/usr/bin/env python3
"""
AI Knowledge Diagnostics Endpoints Testing
Testing the new diagnostics endpoints on production
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class DiagnosticsAPITester:
    def __init__(self, base_url="https://audiobot-qci2.onrender.com"):
        self.base_url = base_url.rstrip('/')
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {name}")
        if details:
            print(f"   Details: {details}")
        
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append({"name": name, "details": details})
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                return False, {}, 0
                
            return True, response.json() if response.content else {}, response.status_code
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}, 0
        except Exception as e:
            return False, {"error": str(e)}, 0
    
    def test_db_check_endpoint(self):
        """Test GET /api/ai-knowledge/db-check endpoint"""
        print("\n🔍 Testing GET /api/ai-knowledge/db-check")
        print("=" * 60)
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            # Check required fields in response
            required_fields = ['connected', 'pgvector_available', 'pgvector_installed', 'ai_tables', 'embedding_dims', 'errors']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                # Log all the diagnostic information
                connected = data.get('connected', False)
                pgvector_available = data.get('pgvector_available', False)
                pgvector_installed = data.get('pgvector_installed', False)
                ai_tables = data.get('ai_tables', [])
                embedding_dims = data.get('embedding_dims', 0)
                errors = data.get('errors', [])
                
                details = f"""
                Connected: {connected}
                PGVector Available: {pgvector_available}
                PGVector Installed: {pgvector_installed}
                AI Tables: {ai_tables}
                Embedding Dimensions: {embedding_dims}
                Errors: {errors}
                """
                
                self.log_test("DB Check - Response Structure", True, details.strip())
                
                # Return the data for further processing
                return True, data
            else:
                self.log_test("DB Check - Response Structure", False, f"Missing fields: {missing_fields}")
                return False, {}
        else:
            self.log_test("DB Check - Endpoint", False, f"Status: {status}, Data: {data}")
            return False, {}
    
    def test_db_install_vector_endpoint(self, should_install=False):
        """Test POST /api/ai-knowledge/db-install-vector endpoint"""
        print("\n🔧 Testing POST /api/ai-knowledge/db-install-vector")
        print("=" * 60)
        
        if not should_install:
            print("   Skipping installation - pgvector already installed or not available")
            return True, {}
        
        install_data = {"confirm": True}
        success, data, status = self.make_request('POST', '/api/ai-knowledge/db-install-vector', install_data)
        
        if success and status == 200:
            self.log_test("DB Install Vector - Installation", True, f"Installation response: {data}")
            return True, data
        elif status == 400:
            # May return 400 if already installed or other validation error
            detail = data.get('detail', '')
            self.log_test("DB Install Vector - Already Installed", True, f"Installation not needed: {detail}")
            return True, data
        else:
            self.log_test("DB Install Vector - Installation", False, f"Status: {status}, Data: {data}")
            return False, {}
    
    def run_diagnostics_test(self):
        """Run the complete diagnostics test as per review request"""
        print("🚀 Starting AI Knowledge Diagnostics Test")
        print("=" * 60)
        print(f"Testing production URL: {self.base_url}")
        print("=" * 60)
        
        # Step 1: GET /api/ai-knowledge/db-check
        print("\n📋 STEP 1: Initial Database Check")
        success, db_check_data = self.test_db_check_endpoint()
        
        if not success:
            print("\n❌ CRITICAL: Cannot proceed - db-check endpoint failed")
            return self.generate_final_report()
        
        # Analyze the results
        connected = db_check_data.get('connected', False)
        pgvector_available = db_check_data.get('pgvector_available', False)
        pgvector_installed = db_check_data.get('pgvector_installed', False)
        
        print(f"\n📊 Initial State Analysis:")
        print(f"   Database Connected: {connected}")
        print(f"   PGVector Available: {pgvector_available}")
        print(f"   PGVector Installed: {pgvector_installed}")
        
        # Step 2: Conditional installation
        should_install = pgvector_installed == False and pgvector_available == True
        
        if should_install:
            print("\n🔧 STEP 2: Installing PGVector Extension")
            print("   Condition met: pgvector_installed=false and pgvector_available=true")
            
            install_success, install_data = self.test_db_install_vector_endpoint(should_install=True)
            
            if install_success:
                print("   ✅ Installation completed, waiting 5 seconds before re-check...")
                time.sleep(5)
                
                # Step 3: Re-check after installation
                print("\n🔄 STEP 3: Re-checking Database State After Installation")
                final_success, final_db_check_data = self.test_db_check_endpoint()
                
                if final_success:
                    final_pgvector_installed = final_db_check_data.get('pgvector_installed', False)
                    if final_pgvector_installed:
                        self.log_test("PGVector Installation - Verification", True, "PGVector successfully installed and verified")
                    else:
                        self.log_test("PGVector Installation - Verification", False, "PGVector installation may have failed - still shows as not installed")
                else:
                    self.log_test("PGVector Installation - Re-check", False, "Failed to re-check database state after installation")
            else:
                print("   ❌ Installation failed")
        else:
            print("\n⏭️  STEP 2: Skipping PGVector Installation")
            if pgvector_installed:
                print("   Reason: PGVector already installed")
            elif not pgvector_available:
                print("   Reason: PGVector not available on this database")
            else:
                print("   Reason: Conditions not met for installation")
            
            # Use initial check data as final state
            final_db_check_data = db_check_data
        
        # Step 3: Report final state
        print("\n📋 FINAL STATE REPORT")
        print("=" * 60)
        
        if 'final_db_check_data' in locals():
            self.report_final_state(final_db_check_data)
        else:
            self.report_final_state(db_check_data)
        
        return self.generate_final_report()
    
    def report_final_state(self, data):
        """Report the final database state"""
        connected = data.get('connected', False)
        pgvector_available = data.get('pgvector_available', False)
        pgvector_installed = data.get('pgvector_installed', False)
        ai_tables = data.get('ai_tables', [])
        embedding_dims = data.get('embedding_dims', 0)
        errors = data.get('errors', [])
        
        print(f"🔗 Database Connected: {'✅ YES' if connected else '❌ NO'}")
        print(f"📦 PGVector Available: {'✅ YES' if pgvector_available else '❌ NO'}")
        print(f"⚡ PGVector Installed: {'✅ YES' if pgvector_installed else '❌ NO'}")
        print(f"🗃️  AI Tables Present: {len(ai_tables)} tables")
        if ai_tables:
            for table in ai_tables:
                print(f"   - {table}")
        print(f"📏 Embedding Dimensions: {embedding_dims}")
        
        if errors:
            print(f"⚠️  Errors Detected: {len(errors)}")
            for i, error in enumerate(errors, 1):
                print(f"   {i}. {error}")
        else:
            print("✅ No Errors Detected")
        
        # Overall status assessment
        if connected and pgvector_installed and ai_tables and embedding_dims > 0:
            print("\n🎉 OVERALL STATUS: ✅ FULLY OPERATIONAL")
            print("   The AI Knowledge system is ready for use!")
        elif connected and pgvector_available and not pgvector_installed:
            print("\n⚠️  OVERALL STATUS: 🔧 NEEDS SETUP")
            print("   Database connected but PGVector needs installation")
        elif connected:
            print("\n⚠️  OVERALL STATUS: 🔄 PARTIALLY READY")
            print("   Database connected but AI features may be limited")
        else:
            print("\n❌ OVERALL STATUS: 🚫 NOT OPERATIONAL")
            print("   Database connection issues detected")
    
    def generate_final_report(self):
        """Generate final test report"""
        print("\n" + "=" * 60)
        print("📊 DIAGNOSTICS TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test['name']}")
                if test['details']:
                    print(f"      Details: {test['details']}")
        
        if success_rate >= 80:
            print(f"\n✅ DIAGNOSTICS RESULT: SUCCESS")
        else:
            print(f"\n❌ DIAGNOSTICS RESULT: ISSUES DETECTED")
        
        return success_rate >= 80

def main():
    """Main function to run diagnostics tests"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://audiobot-qci2.onrender.com"
    
    print(f"🔍 AI Knowledge Diagnostics Test")
    print(f"Target URL: {base_url}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = DiagnosticsAPITester(base_url)
    success = tester.run_diagnostics_test()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()