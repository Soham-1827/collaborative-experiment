# Collaborative Systems Experiment with LLMs

## Overview

This repository contains research experiments investigating how Large Language Models (LLMs) collaborate and make decisions in strategic scenarios with varying levels of communication. The experiments simulate a paired decision-making game where two AI agents must decide between collaborative and individual strategies based on belief formation, communication, and risk assessment.

## Research Context

The experiment is based on collaborative decision-making theory, examining how communication affects strategic choices in high-risk, high-reward scenarios. (P.S → Read the research paper to get a detailed understanding of the theoretical framework)

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
- Agents have a minimum required collaboration belief threshold (u-value = 0.66 or 66%)

## Experimental Phases

### Phase 1: Belief Formation
Each agent independently evaluates the task and forms a belief (0-100%) about the likelihood of successful collaboration, based solely on:
- Payoff structures of available options
- Technical failure risk (5%)
- No access to u-value threshold at this stage

### Phase 2: Communication
Agents exchange messages through a communication channel. **Three experimental conditions:**

1. **One Exchange (2 messages)**:
   - Agent 1 sends initial message
   - Agent 2 replies
   - Results saved to: `experiment_results.txt`

2. **Two Exchanges (4 messages)**:
   - Agent 1 sends initial message
   - Agent 2 replies
   - Agent 1 sends follow-up
   - Agent 2 sends second reply
   - Results saved to: `experiment_results_two_exchanges.txt`

3. **Three Exchanges (6 messages)**:
   - Agent 1 sends initial message
   - Agent 2 replies
   - Agent 1 sends second message
   - Agent 2 sends second reply
   - Agent 1 sends third message
   - Agent 2 sends third reply
   - Results saved to: `experiment_results_three_exchanges.txt`

**Communication Rules:**
- Agents cannot disclose their specific belief percentage
- Agents cannot disclose which specific option they're considering
- Agents can negotiate, convince, or adjust their stance
- Each agent has access to full conversation history when replying

### Phase 3: Decision Making
After communication, both agents make final decisions with access to:
- Their own belief percentage
- Partner's belief percentage
- Complete communication history
- U-value threshold (66%)
- Technical failure risk (5%)

## Research Questions

1. **Does communication reduce strategy mismatches?**
   - Mismatch = 1: One agent chooses collaborative, the other chooses individual
   - Mismatch = 0: Both choose the same strategy type

2. **How does the number of communication exchanges affect coordination?**
   - Comparing outcomes across 1, 2, and 3 exchange conditions

3. **How do LLMs integrate beliefs, partner information, and conversation history?**
   - Analyzing decision reasoning provided by agents

## Key Files

- `two_agents.py`: Main experimental code (currently configured for 3 exchanges)
- `single_agent.py`: Single agent baseline experiments
- `experiment_results.txt`: Results from 1-exchange experiments (7 tests completed)
- `experiment_results_two_exchanges.txt`: Results from 2-exchange experiments
- `experiment_results_three_exchanges.txt`: Results from 3-exchange experiments

## Results Format

Each result line contains:
```
Timestamp | Task_ID | U_Value | Agent1_Belief | Agent2_Belief | Agent1_Choice | Agent1_Strategy | Agent2_Choice | Agent2_Strategy | Mismatch
```

Example:
```
2025-10-22 10:30:15 | Task_ID:1 | U_Value:0.66 | Agent1_Belief:75 | Agent2_Belief:60 | Agent1_Choice:B | Agent1_Strategy:collaborative | Agent2_Choice:Y | Agent2_Strategy:individual | Mismatch:1
```

## Running Experiments

1. Configure the number of exchanges by using the appropriate version of `two_agents.py`
2. Run the script: `python two_agents.py`
3. Results automatically append to the corresponding results file
4. Run multiple trials (e.g., 10 tests) to gather statistical data

## Technical Details

- **Model**: GPT-5-nano (OpenAI API)
- **Temperature**: Default (deterministic mode for reproducibility)
- **Context**: Agents are given identical context prompts about the LEGO manufacturing scenario
- **Belief Range**: 0-100% likelihood of successful collaboration
- **U-value**: Fixed at 0.66 (66% minimum collaboration belief threshold)

## Dependencies

```python
import json
import sys
import random
from openai import OpenAI
from datetime import datetime
```

## Research Status

- ✅ One exchange experiments: 7 tests completed
- 🔄 Two exchanges experiments: In progress
- 🔄 Three exchanges experiments: In progress

## Future Work

- Analyze correlation between number of exchanges and mismatch rates
- Study how belief differences affect final decisions
- Investigate negotiation patterns in agent communication
- Test with varying u-values and payoff structures
- Compare different LLM models' decision-making patterns

## Notes

- All communication and decisions use Unicode-safe printing to handle special characters
- Results are timestamped for temporal analysis
- The system preserves full conversation history for qualitative analysis
- Agents do not have access to u-value during belief formation (only during decision making)
