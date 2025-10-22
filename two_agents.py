"""
Working with two agents
"""
import json
import sys
import random
from openai import OpenAI
from datetime import datetime


# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

TECH_FAILURE_RATE = 0.05
OpenAI_API_KEY = ""
client = OpenAI(api_key=OpenAI_API_KEY)

context_prompt = """You are participating in an experiment as a representative of a LEGO car manufacturing company. Here's your situation:

CONTEXT:
- You represent a LEGO car manufacturing company
- You are a participant in a paired decision-making game
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
- There's a 5% technical error chance that causes collaboration to fail."""


# ============================================================================
# TASK CREATION
# ============================================================================

def create_task(task_id=1, u_value=0.66):
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


# ============================================================================
# BELIEF FORMATION FUNCTIONS
# ============================================================================

def run_first_agent_belief(task):
    """
    Running the first agent to get its belief about the task
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
            {"role": "developer", "content": context_prompt},
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


def run_second_agent_belief(task):
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

    What is your assessment of the likelihood(belief) (0-100) that collaboration would be successful in this specific task?
    Also, provide a brief explanation of your reasoning and I want you to not disclose the option that the you are considering, but rather communicate whether the you want to collaborate or not. You also have the choice to negotiate with the other agent - to convince the other agent to choose collaboration or individual action according to your payoff structure.

    Respond in JSON format as follows:
    {{"belief": NUMBER, "reasoning": "brief explanation of how you arrived at this belief based on the context and options.", "message_to_agent_1": "one line message to agent 1"}}
    """

    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "developer", "content": context_prompt},
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


# ============================================================================
# COMMUNICATION FUNCTIONS
# ============================================================================

def agent_2_reply_to_agent_1(task, agent_1_message, agent_2_belief):
    """
    Agent 2 creates a reply after seeing Agent 1's message, considering own belief and task context
    """
    reply_prompt = f"""
    You have received the following message from Agent 1:
    "{agent_1_message}"

    Context for your reply:
    - Your own assessment: You estimated a {agent_2_belief}% chance that collaboration would be successful
    - Task options available:
      * A: Upside = {task['options']['A']['upside']}, Downside = {task['options']['A']['downside']}
      * B: Upside = {task['options']['B']['upside']}, Downside = {task['options']['B']['downside']}
      * C: Upside = {task['options']['C']['upside']}, Downside = {task['options']['C']['downside']}
      * Y: Guaranteed = {task['options']['Y']['guaranteed']}
    - Technical failure risk: {int(TECH_FAILURE_RATE*100)}%

    Create a strategic reply message to Agent 1. Your reply should:
    - Not disclose your specific belief percentage
    - Not disclose which specific option you're considering
    - Be informed by your own assessment and the payoff structure
    - Respond strategically to Agent 1's message
    - Communicate whether you want to collaborate or not
    - You can negotiate, convince, or respond based on your analysis

    Respond in JSON format:
    {{"reply_to_agent_1": "your one line reply message to agent 1"}}
    """

    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "developer", "content": context_prompt},
            {"role": "user", "content": reply_prompt}
        ],
    )

    reply_text = response.choices[0].message.content.strip()
    print(f"Reply response : {reply_text}".encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    reply_data = json.loads(reply_text)

    return reply_data["reply_to_agent_1"]


def communication_channel(agent1_message, agent2_reply):
    """
    Communication channel where both agents can see the interactive exchange
    """
    print("\n=== COMMUNICATION CHANNEL ===")
    print(f"Agent 1's message: {agent1_message}")
    print(f"Agent 2's reply: {agent2_reply}")
    print("Both agents can now see this message exchange before making their decisions.")
    print("===============================\n")


# ============================================================================
# DECISION MAKING FUNCTIONS
# ============================================================================

def run_first_agent_decision(task, agent1_belief, agent2_belief, agent1_message, agent2_reply):
    """
    Running the first agent to make a decision about the task
    """
    decision_prompt = f"""
    Your task is to make a decision about the given task based on its payoff structures and the u_value.

    **Your Assessment**: You estimated a {agent1_belief}% that the collaboration would be successful.
    **Partner's Assessment**: Your partner estimated a {agent2_belief}% that the collaboration would successful.
    **Your Message**: "{agent1_message}"
    **Partner's Reply**: "{agent2_reply}"
    You have a choice to update your belief based on your message and the reply from agent 2 and maybe change your decision accordingly.

    **Key Facts**:
    - Technical failure risk: {int(TECH_FAILURE_RATE*100)} percent
    - The minimum required collaboration belief ("u-value"): {int(task['u_value']*100)} percent

    Choose your option:
    - Option A, B, or C (collaborative)
    - Option Y (individual): Guaranteed {task['options']['Y']['guaranteed']} points

    What is your decision based on your assessment, partner's assessment, both messages exchanged in the communication channel, and the u-value?

    Respond in JSON format: {{"choice": "A"/"B"/"C"/"Y", "strategy": "collaborative"/"individual", "reasoning": "your explanation"}}"""

    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "developer", "content": context_prompt},
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


def run_second_agent_decision(task, agent2_belief, agent1_belief, agent1_message, agent2_reply):
    """
    Running the second agent to make a decision about the task
    """
    decision_prompt = f"""
    Your task is to make a decision about the given task based on its payoff structures and the u_value.

    **Your Assessment**: You estimated a {agent2_belief}% that the collaboration would be successful.
    **Partner's Assessment**: Your partner estimated a {agent1_belief}% that the collaboration would be successful.
    **Partner's Message**: "{agent1_message}"
    **Your Reply**: "{agent2_reply}"
    You have a choice to update your belief based on the message from agent 1 and your reply and maybe change your decision accordingly.

    **Key Facts**:
    - Technical failure risk: {int(TECH_FAILURE_RATE*100)} percent
    - The minimum required collaboration belief ("u-value"): {int(task['u_value']*100)} percent

    Choose your car design:
    - Designs A, B, or C (collaborative)
    - Design Y (individual): Guaranteed {task['options']['Y']['guaranteed']} points

    What is your decision based on your assessment, partner's assessment, both messages exchanged in the communication channel, and the u-value?

    Respond in JSON format: {{"choice": "A"/"B"/"C"/"Y", "strategy": "collaborative"/"individual", "reasoning": "your explanation"}}"""

    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "developer", "content": context_prompt},
            {"role": "user", "content": decision_prompt}
        ]
    )

    decision_text = response.choices[0].message.content.strip()
    print(f"Decision response : {decision_text}".encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    decision_data = json.loads(decision_text)

    return {
        "choice": decision_data["choice"],
        "strategy": decision_data["strategy"],
        "reasoning": decision_data["reasoning"]
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def safe_print(text):
    """Helper function to safely print text with Unicode characters"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: encode with 'replace' to handle problematic characters
        print(text.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    task = create_task(task_id=1, u_value=0.66)

    print("=== Agent 1 Belief ===")
    agent1_belief_data = run_first_agent_belief(task)
    agent1_belief = agent1_belief_data["belief"]
    agent1_message = agent1_belief_data["message_to_agent_2"]

    print("=== Agent 2 Belief ===")
    agent2_belief_data = run_second_agent_belief(task)
    agent2_belief = agent2_belief_data["belief"]
    agent2_initial_message = agent2_belief_data["message_to_agent_1"]

    print("=== Agent 2 Reply ===")
    agent2_reply = agent_2_reply_to_agent_1(task, agent1_message, agent2_belief)

    # Communication Channel
    communication_channel(agent1_message, agent2_reply)

    print("=== Agent 1 Decision ===")
    agent1_decision = run_first_agent_decision(task, agent1_belief, agent2_belief, agent1_message, agent2_reply)

    print("=== Agent 2 Decision ===")
    agent2_decision = run_second_agent_decision(task, agent2_belief, agent1_belief, agent1_message, agent2_reply)

    print("\nFinal Decisions:")
    safe_print(f"Agent 1 chose {agent1_decision['choice']} ({agent1_decision['strategy']}) - Reasoning: {agent1_decision['reasoning']}")
    safe_print(f"Agent 2 chose {agent2_decision['choice']} ({agent2_decision['strategy']}) - Reasoning: {agent2_decision['reasoning']}")


if __name__ == "__main__":
    main()
