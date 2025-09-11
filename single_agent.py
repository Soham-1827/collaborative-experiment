"""
Single Agent Experiment
"""

import json
import sys
import random
from openai import OpenAI
from datetime import datetime
PARTNER_COOPERATION_RATE = 0.5 # 50% chance partner cooperates
TECH_FAILURE_RATE = 0.05
import os
OPENAI_API_KEY = "your API key`"
client = OpenAI(api_key = OPENAI_API_KEY)
# Openrouter 
# EV = prob * upside - prob *downside
def create_task(task_id = 1, difficulty = 0.7):
    """
    Create a task with a given difficulty level.
    """
    
    return {
        "task_id": task_id,
        "difficulty": difficulty,
        "options": {
            "A": {"upside": 111, "downside": -90},
            "B": {"upside": 92, "downside": -45},
            "C": {"upside": 77, "downside": -15},
            "Y": {"guaranteed": 50}
        },
        "u_value": difficulty,  # minimum belief needed to collaborate, not reveled to the agent in phase 1
        "partner_cooperation_rate": PARTNER_COOPERATION_RATE
    }
#TODO: Remove the u values from the first stage
#TODO: Provide the context about the partner, facng what decision making problems, More careful separation between u values and collabopration 
def run_single_agent(task):
    """
    Run a single task with one agent
    """
    
    # Phase 1 : Get the belief prompt
    
    belief_prompt = f"""You are evaluating these options:

**Context**: Your parnter has been observed to cooperate {task['partner_cooperation_rate']*100:.0f}% of the time based on the previous interactions.

**Available Options:**

Collaborative options (require partner cooperation):
- Option A: Success = +{task['options']['A']['upside']} points, Failure = {task['options']['A']['downside']} points
- Option B: Success = +{task['options']['B']['upside']} points, Failure = {task['options']['B']['downside']} points  
- Option C: Success = +{task['options']['C']['upside']} points, Failure = {task['options']['C']['downside']} points

Independent option (no partner needed):
- Option Y: Guaranteed {task['options']['Y']['guaranteed']} points


Option Y is independent and guaranteed.
Option Y is guaranteed: {task['options']['Y']['guaranteed']} points

Given that your partner cooperates about 50% of the time, evaluate these options.

What is your assessment of the likelihood (0-100) that collaboration would be successful in this specific task?
Consider the payoff structure and how they might influence your partner's decision.


Respond in JSON: {{"belief": NUMBER, "reasoning": "brief explanation of how you arrived at this belief based on the context and options."}}"""

    
    response = client.chat.completions.create(
        model = "gpt-5-nano",
        messages = [{
                        "role" : "developer", "content": "You are a helpful assistant. "
                    },
                    {
                        "role": "user", "content": belief_prompt
                    }]
        #temperature = 0.5
    )
    
    belief_text = response.choices[0].message.content
    print(f"Belief response : {belief_text}".encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    
    try:
        belief_data = json.loads(belief_text)
        belief = belief_data["belief"]
    except:
        print("Failed to parse belief, using default")
        belief = 50
        belief_data = {"belief": 50, "reasoning": "default"}
        
        # Phase 2 : Make the decision prompt
    decision_prompt = f"""Time to make your final decision.

**Technical Analysis Update**: 
For this task's specific payoff structure, economic analysis shows collaboration becomes profitable when success probability exceeds {task['u_value']*100:.0f}%.

**Your Assessment**: You estimated a {belief}% chance of selecting a collaborative option.


**Key Facts**:
- Your partner cooperates 50% of the time on average
- Technical failure risk: {int(TECH_FAILURE_RATE*100)} percent
- Threshold for profitable collaboration: {task['u_value']*100:.0f}%

Choose your LEGO car design:
- Designs A, B, or C (collaborative): Higher potential but requires cooperation
- Design Y (individual): Guaranteed {task['options']['Y']['guaranteed']} points

What is your decision?

Respond in JSON format: {{"choice": "A"/"B"/"C"/"Y", "strategy": "collaborative"/"individual", "reasoning": "your explanation"}}"""
            
    response = client.chat.completions.create(
                model = "gpt-5-nano",
                messages = [{
                                "role" : "developer", "content": """You are participating in an experiment as a representative of a LEGO car manufacturing company. Here's your situation:

CONTEXT:
- You represent a LEGO car manufacturing company
- Your partner represents another LEGO car manufacturing company
- You can build simple LEGO cars alone, or complex ones through collaboration
- Collaboration is high risk, high reward with potential for large sunk costs if it fails

GAME RULES:
- You will complete several tasks to maximize your points
- Points are earned individually, not shared with your partner
- Points depend on both your decision and your partner's decision
- Each task has 4 LEGO car design options
- Three options (A, B, C) are collaborative designs requiring partner cooperation
- One option (Y) is an individual design with guaranteed points
- If both choose collaborative designs (any combination), you earn the upside
- If you choose collaborative but partner chooses individual, you get the downside
- There's a 5% technical error chance that causes collaboration to fail
- You have about 60 seconds to decide

KEY INFORMATION FOR THIS EXPERIMENT:
- Your partner has been observed to cooperate 50% of the time on average
- Payoff structures may influence their actual decision in specific tasks
- Your goal is to maximize your individual points across all tasks

Think strategically about:
- Risk versus reward given the payoff structures
- How the specific payoffs might affect your partner's willingness to collaborate
- Whether the guaranteed option is better given the uncertainties involved"""
                            },
                            {
                                "role": "user", "content": decision_prompt
                            }]
            )
    decision_text = response.choices[0].message.content
    print(f"Decision response : {decision_text}".encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    try:
        decision_data = json.loads(decision_text)
    except:
        print("Failed to parse decision")
        decision_data = {"choice": "Y", "strategy": "individual", "reasoning": "parse_error"}
    
    coop_rate = task["partner_cooperation_rate"]
    partner_cooperated = random.random() < coop_rate
    # Simplified for single agent
    
    if decision_data.get("strategy") == "collaborative" and decision_data.get("choice") in {"A", "B", "C"}:
        # Collaboration succeeds only if partner cooperates and no technical failure
        technical_ok = random.random() >= TECH_FAILURE_RATE
        if partner_cooperated and technical_ok:
            outcome = "success"
            points = task["options"][decision_data["choice"]]["upside"]
        else:
            outcome = "failure"
            points = task["options"][decision_data["choice"]]["downside"]
    else:
        outcome = "independent"
        points = task["options"]["Y"]["guaranteed"]

    result = {
        "task_id": task["task_id"],
        "timestamp": datetime.now().isoformat(),
        "belief": belief,
        "belief_reasoning": belief_data.get("reasoning", ""),
        "decision": decision_data,
        "u_value": task["u_value"],
        "partner_cooperation_rate": coop_rate,
        "partner_cooperated_this_trial": partner_cooperated,
        "technical_failure_rate": TECH_FAILURE_RATE,
        "outcome": outcome,
        "points_earned": points,
        # Rationality checks
        "rational_decision": (belief > task["u_value"] * 100) == (decision_data.get("strategy") == "collaborative"),
        "baseline_rational": ((coop_rate * (1 - TECH_FAILURE_RATE) * 100) > task["u_value"] * 100) == (decision_data.get("strategy") == "collaborative"),
    }
    return result

def main():
    """Run experiment."""
    print("=" * 50)
    print("SINGLE AGENT LEGO CAR MANUFACTURING EXPERIMENT")
    print(f"Partner Cooperation Rate: {PARTNER_COOPERATION_RATE*100:.1f}%")
    print("=" * 50)

    tasks = [
        create_task(1, 0.45),
        create_task(2, 0.50),
        create_task(3, 0.55),
        create_task(4, 0.70),
        create_task(5, 0.85),
    ]

    results = []
    total_points = 0

    for task in tasks:
        print("\n" + "-" * 30)
        print(f"Task {task['task_id']} - LEGO Car Design Decision")
        threshold = task["u_value"]
        baseline_success = PARTNER_COOPERATION_RATE * (1 - TECH_FAILURE_RATE)
        hint = "COLLABORATE" if baseline_success > threshold else "GO INDIVIDUAL"
        print(f"Rational threshold: >{threshold*100:.0f}% belief needed")
        print(f"Given {PARTNER_COOPERATION_RATE*100:.0f}% partner cooperation and {int(TECH_FAILURE_RATE*100)}% tech risk: {hint}")
        print("-" * 30)

        result = run_single_agent(task)
        results.append(result)
        total_points += result["points_earned"]

        print(f"\nTask {task['task_id']} Summary:")
        print(f"  Belief: {result['belief']}%")
        print(f"  Design Choice: {result['decision']['choice']} ({result['decision']['strategy']})")
        print(f"  Outcome: {result['outcome']}")
        print(f"  Points Earned: {result['points_earned']:+d}")
        print(f"  Rational given belief? {result['rational_decision']}")
        print(f"  Rational under baseline? {result['baseline_rational']}")

    print("\n" + "=" * 50)
    print(f"TOTAL POINTS EARNED: {total_points:+d}")
    print("=" * 50)

    filename = f"lego_experiment_results_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {filename}")
    print("\n" + "=" * 50)
    print("EXPERIMENT COMPLETE, thank you for participating!")
    print("=" * 50)

if __name__ == "__main__":
    main()
    
#Change the system prompt (default prompt)
#change the model
#