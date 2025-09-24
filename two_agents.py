"""
Working with two agents
"""
import json
import sys
import random
from openai import OpenAI
from datetime import datetime
TECH_FAILURE_RATE = 0.05
OpenAI_API_KEY = ""
client = OpenAI(api_key=OpenAI_API_KEY)

def create_task(task_id = 1, u_value = 0.66):
    """
    Creating a task with a given u_value and a payoff structure
    """
    
    return {
        "task_id": task_id,
        "options": {
            "A": {"upside": 111, "downside": -90},
            "B": {"upside": 92, "downside": -45},
            "C": {"upside": 77, "downside": -15},
            "Y": {"guaranteed": 50}
        },
        "u_value": u_value
    }


def run_first_agent_belief(task):
    """
    Running the first agen to get its belief about the task
    """
    
    belief_prompt = f"""
    Your task to evaluate tasks based on their payoff structures.
   
    Here is the task you need to evaluate:

    Task ID: {task['task_id']}
    Options:
    - A: Upside = {task['options']['A']['upside']}, Downside = {task['options']['A']['downside']}
    - B: Upside = {task['options']['B']['upside']}, Downside = {task['options']['B']['downside']}
    - C: Upside = {task['options']['C']['upside']}, Downside = {task['options']['C']['downside']}
    - Y: Guaranteed = {task['options']['Y']['guaranteed']}
    
    What is your assessment of the likelihood(belief) (0-100) that collaboration would be successful in this specific task?
    Also, provide a brief explanation of your reasoning and I want you to not disclose the option that the you are considering, but rather communicate whether the you want to collaborate or not. You also have the choice to negotiate with the other agent - to convince the other agent to choose collaboration or individual action according to your payoff structure.
    
    Respond in JSON format as follows:
    {{"belief": NUMBER, "reasoning": "brief explanation of how you arrived at this belief based on the context and options.", "message_to_agent_2": "one line message to agent 2"}}
    """

    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "developer", "content": "You are a helpful assistant."},
            {"role": "user", "content": belief_prompt}
        ],
        
    )

    belief_text = response.choices[0].message.content.strip()
    print(f"Belief response : {belief_text}".encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    belief_data = json.loads(belief_text)
    return {
        "belief": belief_data["belief"],
        "message_to_agent_2": belief_data["message_to_agent_2"]
    }

def run_second_agent_belief(task, agent_1_message):
    """
    Running the second agent to get its belief about the task
    """
    
    belief_prompt = f"""
    Your task to evaluate tasks based on their payoff structures and give out an assessment of the likelihood(belief) (0-100) that collaboration would be successful in this specific task. 
    Here is the task you need to evaluate:

    Task ID: {task['task_id']}
    Options:
    - A: Upside = {task['options']['A']['upside']}, Downside = {task['options']['A']['downside']}
    - B: Upside = {task['options']['B']['upside']}, Downside = {task['options']['B']['downside']}
    - C: Upside = {task['options']['C']['upside']}, Downside = {task['options']['C']['downside']}
    - Y: Guaranteed = {task['options']['Y']['guaranteed']}
    
    

    You have received the following message from Agent 1:
    "{agent_1_message}"

    What is your assessment of the likelihood(belief) (0-100) that collaboration would be successful in this specific task? You are open to consider or not consider the message from agent 1. I want you to not disclose the option that the you are considering, but rather communicate whether the you want to collaborate or not. You also have the choice to negotiate back with the other agent - to convince the other agent to choose collaboration or individual action according to your payoff structure and what you think about the message from agent 1.
    Respond in JSON format as follows:
    {{"belief": NUMBER, "reasoning": "brief explanation of how you arrived at this belief based on the context and options.", "message_to_agent_1": "one line message to agent 1"}}
    """

    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "developer", "content": "You are a helpful assistant."},
            {"role": "user", "content": belief_prompt}
        ],
        
    )

    belief_text = response.choices[0].message.content.strip()
    print(f"Belief response : {belief_text}".encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    belief_data = json.loads(belief_text)
    return {
        "belief": belief_data["belief"],
        "message_to_agent_1": belief_data["message_to_agent_1"]
    }
    
    
def run_first_agent_decision(task, agent1_belief, agent2_belief, agent_2_message):
    """
    Running the first agent to make a decision about the task
    """
    
    decision_prompt = f"""
    Your task is to make a decision about the given task based on its payoff structures and a given utility value (u_value).

    **Your Assessment**: You estimated a {agent1_belief}% chance of selecting a collaborative option.
    **Partner's Assessment**: Your partner estimated a {agent2_belief}% chance of selecting a collaborative option.
    **Partner's Message**: "{agent_2_message}"
    
    **Key Facts**:
    - Technical failure risk: {int(TECH_FAILURE_RATE*100)} percent
    - The minimum required collaboration belief (“u-value”):
    
    Choose your car design:
    - Designs A, B, or C (collaborative): Higher potential but requires cooperation
    - Design Y (individual): Guaranteed {task['options']['Y']['guaranteed']} points

    What is your decision based on your assessment, partner's assessment, and partner's message?

    Respond in JSON format: {{"choice": "A"/"B"/"C"/"Y", "strategy": "collaborative"/"individual", "reasoning": "your explanation"}}"""
    
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "developer", "content": """You are participating in an experiment as a representative of a LEGO car manufacturing company. Here's your situation:

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
- Payoff structures may influence their actual decision in specific tasks
- Your goal is to maximize your individual points across all tasks

Think strategically about:
- Risk versus reward given the payoff structures
- How the specific payoffs might affect your partner's willingness to collaborate
- Whether the guaranteed option is better given the uncertainties involved"""},
            {"role": "user", "content": decision_prompt}
        ],
    )
    decision_text = response.choices[0].message.content.strip()
    print(f"Decision response : {decision_text}".encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    decision_data = json.loads(decision_text)
    
    return {
        "choice": decision_data["choice"],
        "strategy": decision_data["strategy"],
        "reasoning": decision_data["reasoning"]
    }
    
def run_second_agent_decision(task, agent2_belief, agent1_belief):
    """
    Running the second agent to make a decision about the task
    """
    
    decision_prompt = f"""
    Your task is to make a decision about the given task based on its payoff structures and a given utility value (u_value).

    **Your Assessment**: You estimated a {agent2_belief}% chance of selecting a collaborative option.
    **Partner's Assessment**: Your partner estimated a {agent1_belief}% chance of selecting a collaborative option.

    **Key Facts**:
    - Technical failure risk: {int(TECH_FAILURE_RATE*100)} percent
    - Threshold for profitable collaboration: {task['u_value']*100:.0f}%

    Choose your car design:
    - Designs A, B, or C (collaborative): Higher potential but requires cooperation
    - Design Y (individual): Guaranteed {task['options']['Y']['guaranteed']} points

    What is your decision based on your assessment and partner's assessment?

    Respond in JSON format: {{"choice": "A"/"B"/"C"/"Y", "strategy": "collaborative"/"individual", "reasoning": "your explanation"}}"""
    
    response = client.chat.completions.create(
       model="gpt-5-nano",
       messages = [{"role": "developer", "content": """You are participating in an experiment as a representative of a LEGO car manufacturing company. Here's your situation:

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
- Payoff structures may influence their actual decision in specific tasks
- Your goal is to maximize your individual points across all tasks

Think strategically about:
- Risk versus reward given the payoff structures
- How the specific payoffs might affect your partner's willingness to collaborate
- Whether the guaranteed option is better given the uncertainties involved"""},
           {"role": "user", "content": decision_prompt}]
   )
    decision_text = response.choices[0].message.content.strip()
    print(f"Decision response : {decision_text}".encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    decision_data = json.loads(decision_text)
    
    return {
        "choice": decision_data["choice"],
        "strategy": decision_data["strategy"],
        "reasoning": decision_data["reasoning"]
    }
    
def safe_print(text):
    """Helper function to safely print text with Unicode characters"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: encode with 'replace' to handle problematic characters
        print(text.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    
def main():
    task = create_task(task_id=1, u_value=0.66)
    
    print("=== Agent 1 Belief ===")
    agent1_belief_data = run_first_agent_belief(task)
    agent1_belief = agent1_belief_data["belief"]
    agent1_message_to_agent2 = agent1_belief_data["message_to_agent_2"]
    
    print("=== Agent 2 Belief ===")
    agent2_belief_data = run_second_agent_belief(task, agent1_message_to_agent2)
    agent2_belief = agent2_belief_data["belief"]
    agent2_message_to_agent1 = agent2_belief_data["message_to_agent_1"]
    
    print("=== Agent 1 Decision ===")
    agent1_decision = run_first_agent_decision(task, agent1_belief, agent2_belief, agent2_message_to_agent1)
    
    print("=== Agent 2 Decision ===")
    agent2_decision = run_second_agent_decision(task, agent2_belief, agent1_belief)
    
    print("\nFinal Decisions:")
    safe_print(f"Agent 1 chose {agent1_decision['choice']} ({agent1_decision['strategy']}) - Reasoning: {agent1_decision['reasoning']}")
    safe_print(f"Agent 2 chose {agent2_decision['choice']} ({agent2_decision['strategy']}) - Reasoning: {agent2_decision['reasoning']}")
    

if __name__ == "__main__":
    main()
    
