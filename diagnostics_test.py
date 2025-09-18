#!/usr/bin/env python3
"""
Production Diagnostics Testing - Review Request
Test AI Knowledge diagnostics endpoints after URL normalization logic
Base: https://audiobot-qci2.onrender.com
"""

import requests
import json
import sys
from datetime import datetime

class DiagnosticsTester:
    def __init__(self, base_url="https://audiobot-qci2.onrender.com"):
        self.base_url = base_url.rstrip('/')
        self.results = []
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: dict = None):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    def make_request(self, method: str, endpoint: str, data: dict = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            print(f"   🔍 {method} {url}")
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                return False, {"error": "Unsupported method"}, 0
            
            print(f"   📊 Status: {response.status_code}")
            
            # Try to parse JSON response
            try:
                response_data = response.json() if response.content else {}
            except json.JSONDecodeError:
                response_data = {"raw_content": response.text[:500]}
            
            return True, response_data, response.status_code
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError as e:
            return False, {"error": f"Connection error: {str(e)}"}, 0
        except Exception as e:
            return False, {"error": f"Request failed: {str(e)}"}, 0
    
    def test_db_check_endpoint(self):
        """Test 1: GET /api/ai-knowledge/db-check"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-check")
        print("   Expected: Different errors or connected=true if DATABASE_URL now correct")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            # Analyze the response
            connected = data.get('connected', False)
            pgvector_available = data.get('pgvector_available', False)
            pgvector_installed = data.get('pgvector_installed', False)
            errors = data.get('errors', [])
            
            analysis = f"connected={connected}, pgvector_available={pgvector_available}, pgvector_installed={pgvector_installed}"
            if errors:
                analysis += f", errors_count={len(errors)}"
            
            self.log_result("DB Check - Endpoint Response", True, analysis, data)
            
            # Check for specific error patterns
            if errors:
                sslmode_errors = [e for e in errors if 'sslmode' in str(e).lower()]
                if sslmode_errors:
                    self.log_result("DB Check - SSL Mode Errors", True, 
                                  f"Found {len(sslmode_errors)} sslmode errors (URL normalization issue)", 
                                  {"sslmode_errors": sslmode_errors})
                else:
                    self.log_result("DB Check - Error Analysis", True, 
                                  f"No sslmode errors found. Other errors: {len(errors)}")
            
            return data
            
        elif success and status == 500:
            detail = data.get('detail', '')
            if 'sslmode' in detail.lower():
                self.log_result("DB Check - SSL Mode Error", True, 
                              f"Expected sslmode error: {detail}", data)
            else:
                self.log_result("DB Check - 500 Error", False, 
                              f"Unexpected 500 error: {detail}", data)
            return data
            
        elif status == 404:
            self.log_result("DB Check - Endpoint Missing", False, 
                          "db-check endpoint not found (404) - not deployed", data)
            
        else:
            self.log_result("DB Check - Request Failed", False, 
                          f"Status: {status}, Success: {success}", data)
        
        return None
    
    def test_db_install_vector_endpoint(self):
        """Test 2: POST /api/ai-knowledge/db-install-vector"""
        print("\n2️⃣ Testing POST /api/ai-knowledge/db-install-vector")
        print("   Expected: Installation attempt or error if connected=true and pgvector_available=true but installed=false")
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/db-install-vector')
        
        if success and status == 200:
            # Installation successful
            self.log_result("DB Install Vector - Success", True, 
                          "pgvector installation successful", data)
            return data
            
        elif success and status == 500:
            detail = data.get('detail', '')
            if 'sslmode' in detail.lower():
                self.log_result("DB Install Vector - SSL Mode Error", True, 
                              f"Expected sslmode error: {detail}", data)
            elif 'permission' in detail.lower() or 'privilege' in detail.lower():
                self.log_result("DB Install Vector - Permission Error", True, 
                              f"Expected permission error: {detail}", data)
            else:
                self.log_result("DB Install Vector - 500 Error", False, 
                              f"Unexpected 500 error: {detail}", data)
            return data
            
        elif status == 404:
            self.log_result("DB Install Vector - Endpoint Missing", False, 
                          "db-install-vector endpoint not found (404) - not deployed", data)
            
        else:
            self.log_result("DB Install Vector - Request Failed", False, 
                          f"Status: {status}, Success: {success}", data)
        
        return None
    
    def test_db_check_after_install(self):
        """Test 3: Re-check db-check after installation attempt"""
        print("\n3️⃣ Re-testing GET /api/ai-knowledge/db-check after installation attempt")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            connected = data.get('connected', False)
            pgvector_available = data.get('pgvector_available', False)
            pgvector_installed = data.get('pgvector_installed', False)
            
            if connected and pgvector_available and pgvector_installed:
                self.log_result("DB Check After Install - Full Setup", True, 
                              "Database now fully configured with pgvector", data)
            elif connected and pgvector_available and not pgvector_installed:
                self.log_result("DB Check After Install - Install Failed", False, 
                              "pgvector installation failed - check permissions", data)
            else:
                status_info = f"connected={connected}, available={pgvector_available}, installed={pgvector_installed}"
                self.log_result("DB Check After Install - Status", True, 
                              f"Post-install status: {status_info}", data)
            
            return data
        else:
            self.log_result("DB Check After Install - Request Failed", False, 
                          f"Status: {status}, Success: {success}", data)
        
        return None
    
    def run_diagnostics_tests(self):
        """Run the complete diagnostics test suite"""
        print("🔍 PRODUCTION DIAGNOSTICS TESTING - URL NORMALIZATION REVIEW")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Testing AI Knowledge diagnostics endpoints after URL normalization fix")
        print("-" * 70)
        
        # Test 1: GET /api/ai-knowledge/db-check
        db_status = self.test_db_check_endpoint()
        
        # Test 2: POST /api/ai-knowledge/db-install-vector
        install_result = self.test_db_install_vector_endpoint()
        
        # Test 3: Re-check after installation attempt
        if install_result is not None:
            final_status = self.test_db_check_after_install()
        
        # Analysis and recommendations
        self.analyze_results(db_status)
        
        return self.results
    
    def analyze_results(self, db_status):
        """Analyze results and provide recommendations"""
        print("\n" + "=" * 70)
        print("📊 DIAGNOSTICS ANALYSIS & RECOMMENDATIONS")
        print("=" * 70)
        
        if db_status:
            connected = db_status.get('connected', False)
            pgvector_available = db_status.get('pgvector_available', False)
            pgvector_installed = db_status.get('pgvector_installed', False)
            errors = db_status.get('errors', [])
            
            print(f"Database Status:")
            print(f"  - Connected: {connected}")
            print(f"  - PGVector Available: {pgvector_available}")
            print(f"  - PGVector Installed: {pgvector_installed}")
            print(f"  - Errors Count: {len(errors)}")
            
            if not connected:
                print("\n⚠️  RECOMMENDATION:")
                print("  Database not connected. This could be due to:")
                print("  1. DATABASE_URL still has old/invalid format in Render environment")
                print("  2. URL normalization only fixes runtime URL if provided")
                print("  3. Render environment variables need to be updated manually")
                
                # Check for specific error patterns
                if errors:
                    sslmode_errors = [e for e in errors if 'sslmode' in str(e).lower()]
                    if sslmode_errors:
                        print("  4. SSL mode parameter issues detected - update DATABASE_URL with valid sslmode")
                        print("     Valid sslmode values: disable, allow, prefer, require, verify-ca, verify-full")
                
            elif connected and pgvector_available and not pgvector_installed:
                print("\n✅ RECOMMENDATION:")
                print("  Database connected but pgvector not installed.")
                print("  The POST /api/ai-knowledge/db-install-vector endpoint should handle installation.")
                
            elif connected and pgvector_available and pgvector_installed:
                print("\n🎉 SUCCESS:")
                print("  Database fully configured and ready for AI Knowledge operations!")
                
        else:
            print("❌ Could not retrieve database status.")
            print("   Possible issues:")
            print("   1. Diagnostics endpoints not deployed")
            print("   2. Network connectivity issues")
            print("   3. Server configuration problems")
        
        # Summary
        passed_tests = len([r for r in self.results if r['success']])
        total_tests = len(self.results)
        
        print(f"\n📈 TEST SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {total_tests - passed_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "  Success Rate: 0%")

def main():
    """Main entry point"""
    tester = DiagnosticsTester()
    results = tester.run_diagnostics_tests()
    
    # Return appropriate exit code
    failed_tests = [r for r in results if not r['success']]
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())