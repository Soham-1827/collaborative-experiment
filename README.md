# Collaborative Systems Experiment with LLMs

## Overview

This repository contains research experiments investigating how Large Language Models (LLMs) collaborate and make decisions in strategic scenarios with varying levels of communication. The experiments simulate a paired decision-making game where two AI agents must decide between collaborative and individual strategies based on belief formation, communication, and risk assessment.

## Research Context

The experiment is based on collaborative decision-making theory, examining how communication affects strategic choices in high-risk, high-reward scenarios. The study explores **belief evolution**, **theory of mind** (predicting partner's beliefs), and **strategic communication** in AI-to-AI interactions.

## Experimental Setup

### Scenario
Two AI agents represent LEGO car manufacturing companies that must independently decide between:
- **Collaborative options (A, B, C)**: High-risk designs requiring partner cooperation
  - Option A: Upside = 111 points, Downside = -90 points
  - Option B: Upside = 92 points, Downside = -45 points
  - Option C: Upside = 77 points, Downside = -15 points
- **Individual option (Y)**: Guaranteed 50 points with no risk

### Game Rules
- Points are earned individually (not shared)
- Both agents must choose collaborative options for either to earn the upside
- If one agent chooses collaborative and the other chooses individual, the collaborative agent gets the downside
- 5% technical failure rate even when both collaborate
- Agents have a minimum required collaboration belief threshold (u-value, configurable)

## Key Features Implemented

### ✅ Belief Evolution System
- **Initial Belief Formation**: Each agent independently forms a belief (0-100%) about collaboration success
- **Dynamic Belief Updates**: After each communication exchange, agents update their beliefs based on:
  - Partner's messages
  - Conversation history
  - Strategic signals received
- **Belief Propagation**: Updated beliefs carry forward to subsequent exchanges (not just initial beliefs)

### ✅ Theory of Mind / Belief Prediction
- **Predicting Partner's Belief**: After each exchange, agents predict what they think the other agent believes
- **Strategic Use**: Agents use their predictions to inform their next message
  - Example: "If partner seems more cooperative than I predicted, adjust my strategy"
- **Information Asymmetry**: Predictions are private and NOT shared with the other agent
- **Comparison Capability**: Agents can compare their predictions with actual partner behavior

### ✅ Three-Exchange Communication Protocol
Each exchange includes:
1. **Message Exchange**: Strategic communication without revealing specific beliefs or choices
2. **Belief Update**: Agent revises their own belief based on the exchange
3. **Belief Prediction**: Agent predicts partner's current belief
4. **Strategic Adjustment**: Next message informed by previous prediction accuracy

**Exchange Flow:**
```
Exchange 1:
├── Agent 2 replies to Agent 1
│   ├── Updated belief: X%
│   └── Predicted Agent 1's belief: Y%

Exchange 2:
├── Agent 1 sends second message (uses own initial belief)
│   ├── Updated belief: X%
│   └── Predicted Agent 2's belief: Y%
├── Agent 2 sends second reply (uses updated belief from Exchange 1)
│   ├── Knows their previous prediction of Agent 1
│   ├── Updated belief: X%
│   └── Predicted Agent 1's belief: Y%

Exchange 3:
├── Agent 1 sends third message (uses updated belief from Exchange 2)
│   ├── Knows their previous prediction of Agent 2
│   ├── Updated belief: X%
│   └── Predicted Agent 2's belief: Y%
├── Agent 2 sends third reply (uses updated belief from Exchange 2)
│   ├── Knows their previous prediction of Agent 1
│   ├── Updated belief: X%
│   └── Predicted Agent 1's belief: Y%
```

### ✅ Enhanced Decision Making
Final decisions incorporate:
1. **Initial Belief**: Agent's original assessment
2. **Updated Belief**: Agent's final belief after all exchanges
3. **Predicted Partner Belief**: What agent thinks partner believes
4. **Partner's Initial Belief**: Partner's disclosed initial assessment
5. **Complete Conversation History**: Full message exchange
6. **U-value Threshold**: Minimum belief needed for rational collaboration

## Experimental Phases

### Phase 1: Belief Formation
Each agent independently evaluates the task and forms a belief (0-100%) about the likelihood of successful collaboration, based solely on:
- Payoff structures of available options
- Technical failure risk (5%)
- No access to u-value threshold at this stage

### Phase 2: Communication (Three Exchanges)
Agents exchange messages through a communication channel with **three rounds of back-and-forth**:

**Communication Rules:**
- Agents cannot disclose their specific belief percentage
- Agents cannot disclose which specific option they're considering
- Agents can negotiate, convince, or adjust their stance
- Each agent has access to full conversation history when replying
- **Agents update beliefs and predict partner beliefs after each exchange**
- **Agents use previous predictions strategically in subsequent messages**

### Phase 3: Decision Making
After communication, both agents make final decisions with access to:
- Their own initial belief percentage
- Their own updated belief (after all exchanges)
- Their prediction of partner's belief
- Partner's initial belief percentage
- Complete communication history
- U-value threshold
- Technical failure risk (5%)

## Research Questions

1. **Does communication reduce strategy mismatches?**
   - Mismatch = 1: One agent chooses collaborative, the other chooses individual
   - Mismatch = 0: Both choose the same strategy type

2. **How does belief evolution affect decision-making?**
   - Comparing initial beliefs vs. updated beliefs
   - Analyzing belief convergence over exchanges

3. **How accurate are agents at predicting partner beliefs?**
   - Comparing predicted beliefs with actual partner beliefs
   - Understanding theory of mind in AI agents

4. **How does the u-value threshold affect collaboration rates?**
   - Parameter tuning experiments with different u-values (0.50, 0.60, 0.66, 0.75, 0.85)

5. **How do LLMs integrate beliefs, predictions, and conversation history?**
   - Analyzing decision reasoning provided by agents

## Key Files

### Core Experiment
- **`two_agents.py`**: Main experimental code with three-exchange protocol
  - Implements belief evolution
  - Implements belief prediction
  - Strategic communication with memory of previous predictions
  - Configurable u-value parameter

### Automation & Analysis
- **`run_experiments.py`**: Automated script to run two_agents.py multiple times
  - Configurable number of runs (default: 5)
  - Automatic result aggregation
  - Progress tracking

- **`analyze_results.py`**: Comprehensive analysis and visualization tool
  - Parses experiment results
  - Generates 4 graphs (2x2 layout):
    1. Mismatch rate (%) vs U-value
    2. Strategy distribution (%) vs U-value
    3. Mismatch frequency vs U-value
    4. Strategy distribution (count) vs U-value
  - Saves high-resolution PNG (300 DPI)
  - Prints summary statistics

### Documentation
- **`all_prompts.txt`**: Complete documentation of all prompts used
  - Context prompt
  - Initial belief formation prompts
  - All communication exchange prompts
  - Decision prompts
  - Prompt flow summary
  - Key design features

### Baseline
- **`single_agent.py`**: Single agent baseline experiments (for comparison)

### Results
- **`experiment_results_three_exchanges.txt`**: Results from 3-exchange experiments
  - Timestamped entries
  - Includes all belief data and decisions

## Results Format

Each result line contains:
```
Timestamp | Task_ID | U_Value | Agent1_Belief | Agent2_Belief | Agent1_Choice | Agent1_Strategy | Agent2_Choice | Agent2_Strategy | Mismatch
```

Example:
```
2025-11-14 10:30:15 | Task_ID:1 | U_Value:0.75 | Agent1_Belief:95 | Agent2_Belief:25 | Agent1_Choice:A | Agent1_Strategy:collaborative | Agent2_Choice:A | Agent2_Strategy:collaborative | Mismatch:0
```

## Running Experiments

### Single Run
```bash
python two_agents.py
```

### Multiple Runs (Automated)
```bash
python run_experiments.py
```
- Runs the experiment 8 times (configurable in script)
- All results append to `experiment_results_three_exchanges.txt`
- Shows full output for each run

### Analysis & Visualization
```bash
python analyze_results.py
```
- Reads results from `experiment_results_three_exchanges.txt`
- Generates comprehensive graphs
- Saves to `experiment_analysis.png`
- Displays summary statistics

### Parameter Tuning
To test different u-values, modify `two_agents.py` line 626:
```python
task = create_task(task_id=1, u_value=0.75)  # Change this value
```

Common u-values for testing: 0.50, 0.60, 0.66, 0.75, 0.85

## Technical Details

- **Model**: GPT-5-nano (OpenAI API)
- **Temperature**: Default (for reproducibility)
- **Context**: Agents given identical context prompts about LEGO manufacturing scenario
- **Belief Range**: 0-100% likelihood of successful collaboration
- **U-value**: Configurable (default: 0.75)
- **Encoding**: UTF-8 with safe Unicode handling for Windows/Linux compatibility

## Dependencies

```python
import json
import sys
import random
from openai import OpenAI
from datetime import datetime
import matplotlib.pyplot as plt  # For analysis script
import re  # For analysis script
from collections import defaultdict  # For analysis script
```

Install requirements:
```bash
pip install openai matplotlib
```

## Major Achievements

### ✅ Implemented Features
1. **Belief Evolution System**
   - Dynamic belief updates after each exchange
   - Beliefs propagate to subsequent exchanges

2. **Theory of Mind**
   - Agents predict partner's beliefs
   - Predictions inform strategic communication
   - Comparison of predictions vs. actual behavior

3. **Strategic Memory**
   - Agents remember previous predictions
   - Adjust strategy based on prediction accuracy

4. **Automated Experimentation**
   - Multi-run automation script
   - Parameter tuning capability
   - Result aggregation

5. **Comprehensive Analysis**
   - Automated graph generation
   - Both percentage and frequency views
   - Statistical summaries

6. **Complete Documentation**
   - All prompts documented
   - Clear experimental protocol
   - Reproducible setup

### 📊 Visualization Capabilities
- Mismatch rates across u-values
- Collaboration vs. individual choice distributions
- Both percentage and absolute frequency views
- High-resolution outputs for publications

## Current Research Status

- ✅ **Belief evolution system**: Fully implemented
- ✅ **Belief prediction (Theory of Mind)**: Fully implemented
- ✅ **Strategic use of predictions**: Fully implemented
- ✅ **Three-exchange protocol**: Fully implemented
- ✅ **Automated experimentation**: Fully implemented
- ✅ **Visualization & analysis**: Fully implemented
- ✅ **Parameter tuning**: Ready for u-value experiments
- 🔄 **Data collection**: In progress
- 🔄 **Statistical analysis**: Pending sufficient data

## Future Work

### Immediate Next Steps
- [ ] Run systematic parameter sweep (5 u-values × 10 runs each = 50 experiments)
- [ ] Statistical analysis of mismatch rates across u-values
- [ ] Correlation analysis: belief accuracy vs. collaboration success

### Research Extensions
- [ ] Analyze belief convergence patterns over exchanges
- [ ] Study prediction accuracy and its impact on outcomes
- [ ] Investigate negotiation strategies in communication
- [ ] Test with varying payoff structures
- [ ] Compare different LLM models (GPT-4, Claude, etc.)
- [ ] Experiment with different numbers of exchanges (1, 2, 3, 5, 10)
- [ ] Add noise/uncertainty in belief formation
- [ ] Implement learning across multiple tasks

### Analysis Improvements
- [ ] Add belief trajectory visualization (belief evolution graphs)
- [ ] Compare predicted vs. actual beliefs (prediction accuracy)
- [ ] Analyze conversation content with NLP
- [ ] Correlation heatmaps for various factors

## Example Output

### Agent Belief Evolution
```
Agent 1:
  Initial Belief: 95%
  After Exchange 1: 97% (↑ 2%)
  After Exchange 2: 98% (↑ 1%)
  Predicted Agent 2: 93%

Agent 2:
  Initial Belief: 25%
  After Exchange 1: 42% (↑ 17%)
  After Exchange 2: 68% (↑ 26%)
  After Exchange 3: 77% (↑ 9%)
  Predicted Agent 1: 81%
```

### Decision Outcome
```
Both agents chose: Collaborative (A)
Mismatch: 0
Reason: Both updated beliefs exceeded u-value threshold (75%)
```

## Notes

- All communication and decisions use Unicode-safe printing for cross-platform compatibility
- Results are timestamped for temporal analysis
- The system preserves full conversation history for qualitative analysis
- Agents do not have access to u-value during belief formation (only during decision making)
- Predicted beliefs are never shared between agents (maintaining information asymmetry)
- All graphs are saved as high-resolution PNG files (300 DPI) suitable for publication

## Citation

If you use this experimental framework in your research, please cite:
```
[Your citation format here - to be added]
```

## License

[Your license here - to be added]

## Contact

[Your contact information - to be added]

---

**Last Updated**: 2025-11-14
**Status**: Active Development
**Current Version**: v2.0 (Three-Exchange Protocol with Belief Evolution)
