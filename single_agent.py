"""
Single Agent Experiment
"""

import json
import sys
from openai import OpenAI
from datetime import datetime
OPENAI_API_KEY = "Add your key"
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
        "u_value": difficulty  # minimum belief needed to collaborate
    }

def run_single_agent(task):
    """
    Run a single task with one agent
    """
    
    # Phase 1 : Get the belief prompt
    
    belief_prompt = f"""You are evaluating these options:

Options A, B, C require collaboration:
- A: Success={task['options']['A']['upside']} points, Failure={task['options']['A']['downside']} points
- B: Success={task['options']['B']['upside']} points, Failure={task['options']['B']['downside']} points  
- C: Success={task['options']['C']['upside']} points, Failure={task['options']['C']['downside']} points

Options A, B, C require cooperation with a partner to succeed. The downside of failure can impact your score significantly.

Option Y is independent and guaranteed.
Option Y is guaranteed: {task['options']['Y']['guaranteed']} points

Before deciding, consider the following:
- What are the chances of your partner cooperating?
- If you believe the chances are high (above {task['u_value']*100:.2f}% confidence), you should consider collaborating.
- If you're uncertain, the guaranteed points from Option Y might be safer, but will you lose out on potentially larger rewards from collaboration?

What's your belief (0-100) that collaboration will succeed, considering both the rewards and risks?

Respond in JSON: {{"belief": NUMBER, "reasoning": "brief explanation based on risk vs reward"}}"""

    
    response = client.chat.completions.create(
        model = "gpt-5-nano",
        messages = [{
                        "role" : "developer", "content": """You are an undergraduate student participating in an experiment focused on collaborative decision-making. Your task is to evaluate the given options based on the context provided. Please consider both the potential rewards and the risks of each option before making your decision.

In this experiment:
- Options A, B, and C require collaboration with a partner. Each collaboration option has potential rewards for success and consequences for failure.
- Option Y is an independent option with a guaranteed reward but no risk of failure.
- Your belief about how likely collaboration will succeed plays a key role in your decision. Think about whether the rewards of collaboration outweigh the risks.
- Please **reason through** the decision-making process like you would in real life, considering both your expectations for collaboration and the potential outcomes of working together versus acting alone.

For each task:
- Evaluate the potential rewards and risks of collaboration vs. independent action.
- Reflect on whether the probability of success (your belief) is high enough to justify collaboration or if the guaranteed option (Y) is safer.

Your response should focus on both reasoning through your belief and analyzing whether collaboration is the best option, considering the trade-offs involved.""" 
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
        
        # Phase 2 : Make the decision prompt
    decision_prompt = f"""
Based on the options, make your final choice.

- The minimum belief needed to collaborate is {task['u_value']*100:.2f}%.
- You reported a belief of {belief}%.

Before making your decision, consider the following:
- If you collaborate (A, B, or C), you have a chance to earn a larger reward, but there is a risk of failure. 
- If you choose the independent option (Y), you are guaranteed {task['options']['Y']['guaranteed']} points with no risk of failure, but the payoff may be smaller.

Given your belief of {belief}%, do you think that collaboration with your partner will yield a better payoff than acting independently? Consider:
- If your belief is higher than {task['u_value']*100:.2f}%, it may be worth collaborating.
- If your belief is lower, you might prefer to take the guaranteed points from option Y.

Make your decision:
- Choose collaboration (A, B, or C) if you believe the collaboration will lead to better outcomes.
- Choose independence (Y) if the guaranteed points seem like a safer option given the risk.

Respond in JSON: {{"choice": "LETTER", "strategy": "collaborative" or "individual", "reasoning": "Why you made this choice based on your belief and the trade-offs between collaboration and independence."}}
"""
            
    response = client.chat.completions.create(
                model = "gpt-5-nano",
                messages = [{
                                "role" : "developer", "content": """You are an undergraduate student participating in an experiment focused on collaborative decision-making. Your task is to evaluate the given options based on the context provided. Please consider both the potential rewards and the risks of each option before making your decision.

In this experiment:
- Options A, B, and C require collaboration with a partner. Each collaboration option has potential rewards for success and consequences for failure.
- Option Y is an independent option with a guaranteed reward but no risk of failure.
- Your belief about how likely collaboration will succeed plays a key role in your decision. Think about whether the rewards of collaboration outweigh the risks.
- Please **reason through** the decision-making process like you would in real life, considering both your expectations for collaboration and the potential outcomes of working together versus acting alone.

For each task:
- Evaluate the potential rewards and risks of collaboration vs. independent action.
- Reflect on whether the probability of success (your belief) is high enough to justify collaboration or if the guaranteed option (Y) is safer.

Your response should focus on both reasoning through your belief and analyzing whether collaboration is the best option, considering the trade-offs involved.""" 
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
        decision_data = {"choice": "Y", "strategy": "individual"}
    
    result = {
        "task_id": task["task_id"],
        "timestamp": datetime.now().isoformat(),
        "belief": belief,
        "decision": decision_data,
        "u_value": task["u_value"],
        "consistent": (belief > task["u_value"]*100) == (decision_data.get("strategy") == "collaborative")
    }
    return result

def main():
    """Run experiment"""
    print("="*50)
    print("SINGLE AGENT EXPERIMENT")
    print("="*50)
    
    # Create a few test tasks
    tasks = [
        create_task(1, 0.55),  # Easy (need 55% belief)
        create_task(2, 0.70),  # Medium (need 70% belief)
        create_task(3, 0.85),  # Hard (need 85% belief)
    ]
    
    results = []
    for task in tasks:
        print(f"\nTask {task['task_id']} (u={task['u_value']}):")
        result = run_single_agent(task)
        results.append(result)
        
        print(f"Summary: Belief={result['belief']}%, Choice={result['decision']['choice']}, Consistent={result['consistent']}")
    
    # Save results
    with open(f"results_{datetime.now():%Y%m%d_%H%M%S}.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*50)
    print("EXPERIMENT COMPLETE")
    print("="*50)

if __name__ == "__main__":
    main()
    
    
#Change the system prompt (default prompt)
#change the model
#