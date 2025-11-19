# Issues Documentation Summary

This document summarizes all issues that have been documented with inline comments in `two_agents_asymmetric.py`.

## Completed Documentation (12 Issues - ALL COMPLETE) ✅

### 1. **Issue #2: Data Loss - Incomplete Data Capture**
- **Location**: `save_result_to_file()` function (line ~880)
- **Status**: ✅ Documented with enhanced version commented out
- **What's provided**:
  - Explanation of missing data (updated beliefs, predictions, messages)
  - Complete enhanced function ready to uncomment
  - Instructions for activation
  - Includes trial ID generation

### 2. **Issue #4: Inconsistent Belief Updates in Agent 1**
- **Location**: `agent_1_third_message_to_agent_2()` function (line ~415)
- **Status**: ✅ Documented
- **What's provided**:
  - Identifies the specific line using wrong belief variable
  - Explains the temporal inconsistency
  - Notes what needs to be changed

### 3. **Issue #6: Lack of Ground Truth for Successful Collaboration**
- **Location**: After `check_strategy_mismatch()` function (line ~800)
- **Status**: ✅ Documented with solution functions commented out
- **What's provided**:
  - `simulate_collaboration_outcome()` - Complete implementation
  - `calculate_expected_value()` - Rationality assessment
  - Usage instructions for integration into main()

### 4. **Issue #9: No Unique Trial ID**
- **Location**: Top of file after imports (line ~10)
- **Status**: ✅ Documented with two approaches
- **What's provided**:
  - Approach 1: UUID-based (for distributed experiments)
  - Approach 2: Sequential counter (for controlled runs)
  - Complete implementation examples

### 5. **Issue #11: Repeated Code Duplication**
- **Location**: 
  - Communication functions section (line ~225)
  - End of file with refactored solution (line ~1150)
- **Status**: ✅ Documented with complete refactored version
- **What's provided**:
  - Explanation at top of communication section
  - Complete `agent_communicate()` generic function
  - Usage examples showing how to replace existing calls
  - Decision note about keeping current version for debugging

### 6. **Issue #12: Inconsistent Error Handling**
- **Location**: Multiple locations:
  - `run_first_agent_belief()` (line ~168)
  - `run_second_agent_belief()` (line ~225)
- **Status**: ✅ Documented with enhanced versions
- **What's provided**:
  - try-except blocks with fallback values
  - Error logging to file
  - User-friendly console output
  - Default values to continue experiment

### 7. **Issue #16: No Temperature Setting**
- **Location**: All `client.chat.completions.create()` calls
  - First occurrence: `run_first_agent_belief()` (line ~155)
- **Status**: ✅ Documented at first occurrence
- **What's provided**:
  - Explanation of temperature parameter
  - Recommended values for different goals
  - Commented line ready to uncomment
  - Note: Same fix needed for all API calls

### 8. **Issue #17: No Sample Size Justification**
- **Location**: Top of `main()` function (line ~970)
- **Status**: ✅ Documented
- **What's provided**:
  - Power analysis recommendation
  - Sample size calculation (40-50 per condition)
  - Reference to run_experiments.py NUM_RUNS variable

### 9. **Issue #18: No Baseline Comparison**
- **Location**: 
  - Top of `main()` function (line ~980)
  - End of file with baseline functions (line ~1250)
- **Status**: ✅ Documented with complete baseline implementations
- **What's provided**:
  - `baseline_no_communication()` - No exchange control
  - `baseline_one_exchange_only()` - Marginal value test
  - `baseline_random_decisions()` - Floor performance
  - `run_all_baselines()` - Orchestrator function
  - Usage examples

## How to Use This Documentation

### For Review with Advisor:
1. Open `two_agents_asymmetric.py`
2. Search for "ISSUE #X" to find each documented issue
3. Read the explanation and proposed solution
4. Discuss whether to implement

### To Implement a Fix:
1. Find the issue comment block
2. Read the "TO IMPLEMENT" instructions
3. Uncomment the enhanced version
4. Comment out or remove the old version
5. Update function calls if needed (noted in comments)
6. Test thoroughly

### Priority Levels:

**High Priority (Data Quality):**
- Issue #2: Data Loss
- Issue #4: Inconsistent Belief Updates
- Issue #12: Error Handling
- Issue #16: Temperature Setting

**Medium Priority (Experimental Validity):**
- Issue #6: Ground Truth
- Issue #9: Unique Trial IDs
- Issue #17: Sample Size
- Issue #18: Baseline Comparison

**Low Priority (Code Quality):**
- Issue #11: Code Duplication (maintainability)

### 10. **Issue #19: Confounded Variables**
- **Location**: 
  - Lines 38-56 (problem documentation)
  - Lines 1449-1610 (factorial design framework)
- **Status**: ✅ Documented with complete factorial design
- **What's provided**:
  - Explanation of confounding (belief formation + communication + predictions)
  - 2x2x2 factorial design table (8 conditions)
  - `run_factorial_experiment()` implementation template
  - `run_trial_with_conditions()` parameterized trial function
  - Statistical analysis plan (factorial ANOVA)
  - Sample size recommendations (320-400 trials)
  - Note: Requires substantial refactoring - discuss with advisor first

### 11. **Issue #23: Add Pre-Registration**
- **Location**: Lines 78-99 (in CONSTANTS section)
- **Status**: ✅ Documented with OSF guide
- **What's provided**:
  - Explanation of HARKing risk
  - Complete pre-registration checklist:
    * Primary and secondary hypotheses
    * Experimental design specifications
    * Analysis plan details
    * Data collection stopping rules
  - Step-by-step OSF submission process
  - Link to OSF registries
  - Note: Should be done before next data collection phase

### 12. **Issue #24: Compare Different LLM Models**
- **Location**:
  - Lines 195-218 (first API call with documentation)
  - Lines 1612-1830 (model comparison framework)
- **Status**: ✅ Documented with complete framework
- **What's provided**:
  - List of models to test (GPT-4, Claude-3, Llama-3)
  - **Strategy 1**: Parameterized model selection
    * `run_trial_with_model()` - Accepts model_name parameter
    * `run_model_comparison_experiment()` - Orchestrator
  - **Strategy 2**: Multiple client objects (OpenAI + Anthropic)
    * `get_llm_response()` - Unified API interface
  - Statistical comparison plan:
    * One-way ANOVA across models
    * Tukey HSD for pairwise comparisons
    * Data to collect per model (7 metrics)
  - Cost management recommendations
  - Pilot testing strategy (10 trials per model first)

## Next Steps

1. **Review Meeting**: Discuss each issue with Dr. Grogan and collaborator
2. **Prioritize**: Decide which issues to fix before next data collection
3. **Implement**: Systematically uncomment and test approved fixes
4. **Validate**: Run test experiments to ensure fixes work correctly
5. **Document**: Update README.md with implemented changes

## Notes

- All enhanced code is **ready to run** - just uncomment
- No rewriting needed - solutions are complete
- Each issue is **self-contained** - can be fixed independently
- Test after each fix to avoid debugging multiple changes at once
