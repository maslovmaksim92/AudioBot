#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

## user_problem_statement: "Display correct brigade name on house cards and details by resolving Bitrix24 ASSIGNED_BY_ID to full brigade name (e.g., '4 бригада') and ensure endpoints return enriched data without breaking pagination and filters."

## backend:
##   - task: "Brigade name mapping in list endpoint (/api/cleaning/houses)"
##     implemented: true
##     working: true
##     file: "/app/backend/server.py"
##     stuck_count: 0
##     priority: "high"
##     needs_retesting: false
##     status_history:
##         -working: false
##         -agent: "main"
##         -comment: "Implemented BRIGADE_NAME_ENRICHED enrichment via BitrixService.get_user_details and returning 'brigade' from enriched field. Ready for backend testing."
##         -working: true
##         -agent: "testing"
##         -comment: "✅ PASSED - Houses endpoint returns correct HousesResponse shape with houses[], total, page, limit, pages as integers. All brigade fields are strings (no raw ASSIGNED_BY_ID leaks). Sample enriched brigades: '4 бригада', '6 бригада'. Brigade name enrichment working correctly."
##   - task: "Brigade name mapping in details endpoint (/api/cleaning/house/{id}/details)"
##     implemented: true
##     working: true
##     file: "/app/backend/server.py"
##     stuck_count: 0
##     priority: "high"
##     needs_retesting: false
##     status_history:
##         -working: false
##         -agent: "main"
##         -comment: "Added ASSIGNED_BY_ID to select and computed brigade via get_user_details with safe fallbacks; details returns house.brigade as resolved name."
##         -working: true
##         -agent: "testing"
##         -comment: "✅ PASSED - House details endpoint returns house.brigade as string (e.g., '4 бригада' for house 13112). Correctly returns 404 for non-existent houses (not 500). Brigade name resolution working with proper fallbacks."

## frontend:
##   - task: "Works list uses brigade name field"
##     implemented: true
##     working: "NA"
##     file: "/app/frontend/src/components/Works/Works.js"
##     stuck_count: 0
##     priority: "high"
##     needs_retesting: false
##     status_history:
##         -working: true
##         -agent: "main"
##         -comment: "Works.js already uses house.brigade on cards and in details modal; backend now supplies enriched names."

## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 1
##   run_ui: false

## test_plan:
##   current_focus:
##     - "Verify /api/cleaning/houses supports filters brigade, management_company, cleaning_date and date_from/date_to; pagination returns bottom-only pages with correct total/pages"
##     - "Verify /api/cleaning/house/{id}/details includes bitrix_url and details payload is stable"
##   stuck_tasks:
##     - "Past 503 Bitrix24 instabilities; verify fallbacks don't break responses"
##   test_all: false
##   test_priority: "high_first"

## agent_communication:
##     -agent: "main"
##     -message: "Please run backend tests for the updated filters and pagination: 1) /api/cleaning/houses with brigade, management_company, cleaning_date=2025-09-05 and date range (2025-09-01..2025-09-30); verify pages/total integers and non-empty when Bitrix responds; 2) /api/cleaning/house/{id}/details returns bitrix_url when available. Validate schema stability and no 500s on Bitrix 503 (fallbacks)."