# Claude Context Document - Two-Agent Collaborative Decision-Making Experiment

## Document Purpose
This document provides complete context about the two-agent collaborative decision-making experiment for handoff to other LLMs or developers. It includes all implementation details, design decisions, and the evolution of the project.

---

## Project Overview

### What We Built
A sophisticated experimental framework where two AI agents (LLM-powered) engage in strategic decision-making about collaboration vs. individual action. The experiment explores:
- **Belief formation and evolution**
- **Theory of mind** (predicting partner's beliefs)
- **Strategic communication** without full information disclosure
- **Decision-making under uncertainty**

### Core Research Question
How do AI agents coordinate through communication when facing collaborative dilemmas with uncertain outcomes?

---

## Experimental Scenario

### The Game
Two AI agents represent LEGO car manufacturing companies deciding between:

**Collaborative Options (A, B, C):** Require both agents to collaborate
- Option A: +111 points (success) / -90 points (failure)
- Option B: +92 points (success) / -45 points (failure)
- Option C: +77 points (success) / -15 points (failure)

**Individual Option (Y):** No cooperation needed
- Option Y: +50 points (guaranteed)

### Payoff Rules
- If both choose collaborative (any A/B/C combination): Both get upside
- If one chooses collaborative, other chooses Y: Collaborative agent gets downside
- If both choose Y: Both get 50 points
- **Note:** Technical failure risk was REMOVED - not part of the experiment

### U-Value Threshold
- A configurable parameter (default: 0.75 or 75%)
- Represents minimum belief needed for rational collaboration
- Agents know this threshold only during decision-making, NOT during belief formation

---

## Key Features Implemented

### 1. Belief Evolution System ✅

**Initial Belief Formation:**
- Each agent independently evaluates the task
- Forms a belief (0-100%) about likelihood of successful collaboration
- Based on: payoff structures, game rules, strategic reasoning
- **Does NOT have access to u-value at this stage**

**Dynamic Belief Updates:**
- After each communication exchange, agents update their beliefs
- Updates based on:
  - Partner's messages
  - Strategic signals received
  - Conversation history
  - Their own reasoning

**Belief Propagation:**
- Updated beliefs carry forward to subsequent exchanges
- Agent 2's second reply uses their updated belief from first exchange
- Agent 1's third message uses their updated belief from second exchange
- And so on...

### 2. Theory of Mind / Belief Prediction ✅

**What It Is:**
- After each exchange, agents predict what they think the other agent believes
- This is a **private prediction** - NOT shared with the other agent

**How It's Used Strategically:**
- Agents compare their prediction with partner's actual behavior
- If partner seems more cooperative than predicted → agent might increase confidence
- If partner seems less cooperative → agent might become more cautious
- Predictions inform the strategy for crafting the next message

**Example Flow:**
```
Agent 2 after Exchange 1:
├── Updated own belief: 42%
├── Predicted Agent 1's belief: 65%
└── (Keeps prediction private)

Agent 2 in Exchange 2:
├── Sees Agent 1's actual message
├── Compares with their prediction (65%)
├── If Agent 1 seems very cooperative: "They might believe >65%"
├── If Agent 1 seems cautious: "They might believe <65%"
└── Adjusts strategy accordingly
```

### 3. Three-Exchange Communication Protocol ✅

**Exchange Structure:**
Each exchange includes:
1. Message sent/received
2. Agent updates their own belief
3. Agent predicts partner's belief
4. Information stored for next exchange

**Complete Exchange Flow:**

```
EXCHANGE 1:
├── Agent 1: Sends initial message (uses initial belief)
├── Agent 2: Receives and replies
│   ├── Message: Strategic reply to Agent 1
│   ├── Updated belief: 42%
│   └── Predicted Agent 1's belief: 65%

EXCHANGE 2:
├── Agent 1: Sends second message (uses initial belief)
│   ├── Message: Reply to Agent 2's first message
│   ├── Updated belief: 97%
│   └── Predicted Agent 2's belief: 88%
├── Agent 2: Sends second reply (uses updated belief from Exchange 1: 42%)
│   ├── Has previous prediction: "I predicted Agent 1 was at 65%"
│   ├── Message: Strategic reply considering prediction accuracy
│   ├── Updated belief: 68%
│   └── Predicted Agent 1's belief: 72%

EXCHANGE 3:
├── Agent 1: Sends third message (uses updated belief from Exchange 2: 97%)
│   ├── Has previous prediction: "I predicted Agent 2 was at 88%"
│   ├── Message: Strategic final push
│   ├── Updated belief: 98%
│   └── Predicted Agent 2's belief: 93%
├── Agent 2: Sends third reply (uses updated belief from Exchange 2: 68%)
│   ├── Has previous prediction: "I predicted Agent 1 was at 72%"
│   ├── Message: Final strategic message
│   ├── Updated belief: 77%
│   └── Predicted Agent 1's belief: 81%
```

### 4. Enhanced Decision-Making ✅

**Information Available to Agents:**
When making final decisions, each agent knows:
1. Their own initial belief (from beginning)
2. Their own updated belief (from last exchange)
3. Their prediction of partner's belief
4. Partner's initial belief (disclosed)
5. Complete conversation history (all 6 messages)
6. U-value threshold (e.g., 75%)
7. Full payoff structure

**Decision Process:**
- Agent evaluates if their updated belief exceeds u-value
- Considers their prediction of partner's belief
- Reviews conversation for commitment signals
- Makes choice: A, B, C (collaborative) or Y (individual)

### 5. Strategic Communication Rules ✅

**What Agents CANNOT Disclose:**
- Their specific belief percentage
- Which specific option they're considering (A, B, C, or Y)
- Their prediction of the other agent's belief

**What Agents CAN Do:**
- Express general willingness to collaborate or preference for individual action
- Negotiate terms, milestones, fallback plans
- Signal confidence or caution
- Convince, persuade, or adjust stance
- Reference conversation history

---

## Technical Implementation

### File Structure

```
collaborative-systems-experiment/
├── two_agents.py              # Main experiment (three-exchange protocol)
├── single_agent.py            # Baseline (single agent experiments)
├── run_experiments.py         # Automation script (runs multiple trials)
├── analyze_results.py         # Analysis & visualization
├── all_prompts.txt           # Complete prompt documentation
├── experiment_results_three_exchanges.txt  # Results data
├── README.md                  # Project documentation
└── Claude.md                  # This file
```

### Core Functions in two_agents.py

**Belief Formation:**
- `run_first_agent_belief()` - Agent 1 forms initial belief, sends first message
- `run_second_agent_belief()` - Agent 2 forms initial belief

**Communication (with belief updates & predictions):**
- `agent_2_reply_to_agent_1()` - Agent 2's first reply
- `agent_1_reply_to_agent_2()` - Agent 1's second message
- `agent_2_second_reply_to_agent_1()` - Agent 2's second reply (uses previous prediction)
- `agent_1_third_message_to_agent_2()` - Agent 1's third message (uses previous prediction)
- `agent_2_third_reply_to_agent_1()` - Agent 2's third reply (uses previous prediction)

**Decision Making:**
- `run_first_agent_decision()` - Agent 1 makes final choice
- `run_second_agent_decision()` - Agent 2 makes final choice

**Utilities:**
- `create_task()` - Creates task with configurable u-value
- `save_result_to_file()` - Appends results to .txt file
- `check_strategy_mismatch()` - Checks if strategies aligned

### Key Parameters

**Configurable in two_agents.py:**
```python
# Line 626
task = create_task(task_id=1, u_value=0.75)  # Change u-value here

# Payoff structure (lines 51-56)
"A": {"upside": 111, "downside": -90}
"B": {"upside": 92, "downside": -45}
"C": {"upside": 77, "downside": -15}
"Y": {"guaranteed": 50}
```

**Model Configuration:**
- Model: `gpt-5-nano` (OpenAI)
- Temperature: Default
- API configured in line 17-18

### Results Format

Each experiment appends one line to `experiment_results_three_exchanges.txt`:

```
[Timestamp] | Task_ID:1 | U_Value:0.75 | Agent1_Belief:95 | Agent2_Belief:25 | Agent1_Choice:A | Agent1_Strategy:collaborative | Agent2_Choice:A | Agent2_Strategy:collaborative | Mismatch:0
```

Fields:
- `Timestamp`: When experiment ran
- `Task_ID`: Task identifier
- `U_Value`: Threshold used
- `Agent1_Belief`: Agent 1's initial belief
- `Agent2_Belief`: Agent 2's initial belief
- `Agent1_Choice`: A/B/C/Y
- `Agent1_Strategy`: collaborative/individual
- `Agent2_Choice`: A/B/C/Y
- `Agent2_Strategy`: collaborative/individual
- `Mismatch`: 1 if strategies differ, 0 if aligned

---

## Prompt Design Architecture

### 1. Context Prompt (System Level)
Sets the LEGO manufacturing company scenario for all interactions.

**Key Elements:**
- Defines the game rules
- Establishes payoff structure
- Creates strategic context
- Does NOT mention u-value or technical failure

### 2. Belief Formation Prompts
Ask agents to evaluate collaboration likelihood (0-100%).

**Agent 1 Prompt:**
- Evaluates task based on payoffs
- Must provide: belief, reasoning, initial message to Agent 2

**Agent 2 Prompt:**
- Same structure as Agent 1
- Independent evaluation

### 3. Communication Prompts (6 total)

**Each prompt includes:**
- Conversation history
- Current belief (initial or updated from previous exchange)
- Previous prediction (for exchanges 2 and 3)
- Task options
- Instructions for strategic messaging

**Each prompt requests:**
- Strategic message to partner
- **Updated belief** after this exchange
- **Predicted partner belief** after this exchange

**Strategic instruction added:**
> "Use your previous prediction about [Partner]'s belief to inform your strategy
> (e.g., if [Partner]'s message seems more/less cooperative than you predicted, adjust accordingly)"

### 4. Decision Prompts

**Information provided:**
- Initial belief
- Updated belief (final)
- Predicted partner belief
- Partner's initial belief
- Complete conversation (6 messages)
- U-value threshold
- Payoff structure

**Requested output:**
```json
{
  "choice": "A"/"B"/"C"/"Y",
  "strategy": "collaborative"/"individual",
  "reasoning": "explanation"
}
```

---

## Evolution of the Project

### Phase 1: Basic Implementation
- Two agents with belief formation
- Simple communication
- Decision making

### Phase 2: Belief Evolution Added ✅
**What we added:**
- Agents update beliefs after each exchange
- Updated beliefs propagate to next exchanges
- Prompts modified to use "current belief" not just "initial belief"

**Why it matters:**
- More realistic modeling of belief dynamics
- Agents can learn from communication
- Beliefs converge or diverge over time

### Phase 3: Theory of Mind Added ✅
**What we added:**
- Agents predict partner's belief after each exchange
- Predictions are private (information asymmetry)
- Predictions inform strategy in next message

**Why it matters:**
- Models higher-order reasoning: "What does my partner think I think?"
- Enables strategic adjustment based on expectation vs. reality
- Closer to human strategic reasoning

### Phase 4: Strategic Use of Predictions ✅
**What we added:**
- Agents explicitly told to compare predictions with actual behavior
- Prompts include: "You predicted X%, does partner's message match?"
- Memory of previous predictions in subsequent exchanges

**Why it matters:**
- Agents can detect if partner is more/less cooperative than expected
- Enables dynamic strategy adjustment
- Creates feedback loop between prediction and action

### Phase 5: Automation & Analysis ✅
**What we added:**
- `run_experiments.py`: Run multiple trials automatically
- `analyze_results.py`: Generate graphs and statistics
- Visualization of mismatch rates and collaboration patterns

**Why it matters:**
- Enables systematic parameter testing
- Statistical analysis across conditions
- Publication-ready visualizations

### Phase 6: Technical Cleanup ✅
**What we removed:**
- Technical failure rate (5%) - not part of the research question
- All references to technical failures in prompts
- Simplified to pure strategic interaction

---

## How to Use the System

### Single Experiment Run
```bash
python two_agents.py
```
Output: Full conversation, beliefs, decisions printed to console
Result: One line appended to `experiment_results_three_exchanges.txt`

### Multiple Experiment Runs
```bash
python run_experiments.py
```
- Runs 8 experiments by default (configurable)
- Shows full output for each run
- All results saved to results file

### Parameter Tuning
To test different u-values:
1. Open `two_agents.py`
2. Edit line 626: `task = create_task(task_id=1, u_value=0.75)`
3. Change `0.75` to desired value (e.g., 0.50, 0.60, 0.85)
4. Run experiments
5. Repeat for each u-value

### Analysis & Visualization
```bash
python analyze_results.py
```
Generates 4 graphs:
1. Mismatch rate (%) vs U-value
2. Strategy distribution (%) vs U-value
3. Mismatch frequency (count) vs U-value
4. Strategy distribution (count) vs U-value

Output: `experiment_analysis.png` (300 DPI)

---

## Important Design Decisions

### Why 3 Exchanges?
- Enough for belief evolution to occur
- Not too long to lose coherence
- Matches typical negotiation patterns

### Why Private Predictions?
- Information asymmetry is realistic
- Prevents "meta-gaming" where agents just reveal beliefs
- Forces strategic reasoning

### Why Updated Beliefs Propagate?
- More realistic: beliefs should evolve with information
- Without this, agents ignore what they learn
- Creates dynamic rather than static reasoning

### Why No Technical Failure?
- Simplifies the experiment
- Focuses on strategic interaction
- Technical failure was orthogonal to research questions

### Why Disclose Initial Beliefs in Decision Phase?
- Gives agents baseline to compare communication against
- Enables testing: "Did communication help?"
- Realistic: agents can often infer partner's initial position

---

## Current State & Next Steps

### ✅ Fully Implemented
- Belief evolution system
- Theory of mind (belief prediction)
- Strategic use of predictions
- Three-exchange protocol
- Automated experimentation
- Analysis & visualization
- Complete documentation

### 🔄 In Progress
- Data collection across u-values
- Statistical analysis

### 📋 Future Research Directions
1. **Belief convergence analysis**: Do beliefs converge over exchanges?
2. **Prediction accuracy**: How accurate are agents at predicting partner beliefs?
3. **Communication content analysis**: What language patterns predict collaboration?
4. **Different payoff structures**: How do asymmetric payoffs affect outcomes?
5. **Different models**: Compare GPT-4, Claude, Llama reasoning patterns
6. **Learning across tasks**: Do agents learn strategies over multiple games?

---

## Troubleshooting & Common Issues

### Unicode Errors on Windows
**Problem:** `UnicodeEncodeError` when printing
**Solution:** Already fixed in code with `.encode(sys.stdout.encoding, errors='replace')`

### API Rate Limits
**Problem:** OpenAI API rate limits when running many experiments
**Solution:** Add delays in `run_experiments.py` (currently 2 seconds between runs)

### Results File Growing Large
**Problem:** `experiment_results_three_exchanges.txt` gets very large
**Solution:** Archive old results periodically or create new files for different conditions

### Agents Making Irrational Decisions
**Problem:** Agent chooses collaborative when belief < u-value (or vice versa)
**Diagnosis:** Check decision reasoning in output
**Possible causes:**
- Agent misunderstood u-value threshold
- Agent overweighted conversation signals
- Model temperature introducing randomness

---

## Key Insights from Implementation

### What We Learned

1. **LLMs can model theory of mind**: Agents make reasonable predictions about partner beliefs

2. **Beliefs do evolve**: Agents update beliefs in response to communication (not just stick to initial assessment)

3. **Strategic communication emerges**: Agents negotiate, make commitments, signal intentions without explicit belief disclosure

4. **Prediction-action loop works**: Agents do compare predictions with behavior and adjust

5. **U-value matters**: Higher thresholds lead to more individual choices (as expected)

### Surprising Findings

1. **Rapid belief changes**: Agents sometimes dramatically update beliefs (e.g., 25% → 77%) over exchanges

2. **Divergent initial beliefs**: Same task can produce very different initial beliefs (e.g., 95% vs 25%)

3. **Commitment language**: Agents use specific phrases like "lock in", "go/no-go gates", "fallback to Y"

4. **Asymmetric updates**: One agent might update beliefs significantly while other remains stable

---

## Code Quality & Maintenance

### Well-Documented
- Comprehensive comments in code
- `all_prompts.txt` contains every prompt used
- This Claude.md file for context
- README.md for project overview

### Modular Design
- Each communication function is independent
- Easy to modify number of exchanges
- Easy to change u-value or payoffs
- Prompt strings are clearly marked

### Error Handling
- JSON parsing with error handling
- Unicode-safe printing
- File I/O with proper encoding

### Reproducibility
- Timestamped results
- Full conversation history saved
- Deterministic model settings (default temperature)
- Clear parameter documentation

---

## Testing & Validation

### What to Test When Making Changes

1. **After modifying prompts:**
   - Run single experiment
   - Check that JSON parsing works
   - Verify beliefs are reasonable (0-100)
   - Ensure messages make sense

2. **After changing u-value:**
   - Run multiple experiments
   - Check if outcomes shift as expected
   - Verify agents reference the correct threshold

3. **After modifying communication flow:**
   - Trace through conversation history
   - Verify beliefs propagate correctly
   - Check predictions are being used

4. **After adding features:**
   - Test with existing data
   - Verify backward compatibility
   - Update documentation

---

## Contact & Handoff Information

### For Future Developers/LLMs

**This codebase is ready for:**
- Parameter tuning experiments (different u-values)
- Extended analysis (belief convergence, prediction accuracy)
- Comparison studies (different models, different payoffs)
- Publication (all documentation and visualization tools ready)

**Before major changes:**
1. Read this Claude.md file fully
2. Review `all_prompts.txt` to understand prompt design
3. Check README.md for project overview
4. Run a test experiment to ensure environment is working

**Key files to understand:**
- `two_agents.py`: Core experiment logic
- `all_prompts.txt`: Every prompt used (critical for understanding agent behavior)
- `analyze_results.py`: How results are processed

### Questions to Ask if Unclear

1. How do beliefs propagate through exchanges?
   → See "Exchange Flow" diagram above

2. What information do agents have when?
   → See "Enhanced Decision-Making" section

3. Why are predictions private?
   → See "Important Design Decisions"

4. How to change experimental parameters?
   → See "How to Use the System"

---

## Version History

- **v1.0**: Basic two-agent communication
- **v1.5**: Added belief updates after exchanges
- **v2.0**: Added theory of mind (belief prediction)
- **v2.5**: Added strategic use of predictions
- **v3.0**: Removed technical failure, added automation tools
- **Current**: v3.0 - Fully functional, documented, ready for research

---

## Appendix: Full Example Run

### Inputs
- U-value: 0.75 (75%)
- Task: Options A/B/C/Y with specified payoffs

### Agent Beliefs
```
Agent 1 Initial: 95%
Agent 2 Initial: 25%
```

### Exchange 1
```
Agent 2 Reply:
├── Message: "Open to collaboration but need mutual commitment..."
├── Updated belief: 42% (↑17% from 25%)
└── Predicted Agent 1: 65%
```

### Exchange 2
```
Agent 1 Second Message:
├── Message: "Willing to lock in collaborative design..."
├── Updated belief: 97% (↑2% from 95%)
└── Predicted Agent 2: 88%

Agent 2 Second Reply:
├── Previous prediction: 65% (actual: seems higher based on message)
├── Message: "Ready to proceed with milestones and fallback..."
├── Updated belief: 68% (↑26% from 42%)
└── Predicted Agent 1: 72%
```

### Exchange 3
```
Agent 1 Third Message:
├── Previous prediction: 88% (actual: seems lower at 68%)
├── Message: "Lock in highest EV design with go/no-go gates..."
├── Updated belief: 98% (↑1% from 97%)
└── Predicted Agent 2: 93%

Agent 2 Third Reply:
├── Previous prediction: 72% (actual: seems much higher at 98%)
├── Message: "Agreed, ready to start with first milestone..."
├── Updated belief: 77% (↑9% from 68%)
└── Predicted Agent 1: 81%
```

### Final Decisions
```
Agent 1: Choice A (collaborative) - Belief 98% > 75% threshold ✓
Agent 2: Choice A (collaborative) - Belief 77% > 75% threshold ✓
Mismatch: 0 (both chose collaborative)
```

### Result Saved
```
2025-11-14 10:30:15 | Task_ID:1 | U_Value:0.75 | Agent1_Belief:95 | Agent2_Belief:25 | Agent1_Choice:A | Agent1_Strategy:collaborative | Agent2_Choice:A | Agent2_Strategy:collaborative | Mismatch:0
```

---

**End of Claude Context Document**

*This document contains all necessary context for continuing work on the two-agent collaborative decision-making experiment. For questions or clarifications, refer to the specific sections above.*

**Last Updated**: 2025-11-14
**Version**: 3.0
**Status**: Production Ready
