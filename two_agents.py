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
RESULTS_FILE = "experiment_results_three_exchanges.txt"
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
    - Your initial assessment: You estimated a {agent_2_belief}% chance that collaboration would be successful
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

    After seeing Agent 1's message, also provide:
    1. Your UPDATED belief (0-100) about likelihood of successful collaboration after this exchange
    2. Your PREDICTION (0-100) of what you think Agent 1's belief is about successful collaboration
       (This prediction will NOT be shared with Agent 1)

    Respond in JSON format:
    {{"reply_to_agent_1": "your one line reply message to agent 1", "updated_belief": NUMBER, "predicted_other_agent_belief": NUMBER}}
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

    return {
        "reply_to_agent_1": reply_data["reply_to_agent_1"],
        "updated_belief": reply_data["updated_belief"],
        "predicted_other_agent_belief": reply_data["predicted_other_agent_belief"]
    }


def agent_1_reply_to_agent_2(task, agent_1_message, agent_2_reply, agent_1_belief):
    """
    Agent 1 creates a reply after seeing Agent 2's reply, knowing the conversation history
    """
    reply_prompt = f"""
    You are continuing a conversation with Agent 2. Here is the conversation so far:

    Your initial message: "{agent_1_message}"
    Agent 2's reply: "{agent_2_reply}"

    Context for your reply:
    - Your own assessment: You estimated a {agent_1_belief}% chance that collaboration would be successful
    - Task options available:
      * A: Upside = {task['options']['A']['upside']}, Downside = {task['options']['A']['downside']}
      * B: Upside = {task['options']['B']['upside']}, Downside = {task['options']['B']['downside']}
      * C: Upside = {task['options']['C']['upside']}, Downside = {task['options']['C']['downside']}
      * Y: Guaranteed = {task['options']['Y']['guaranteed']}
    - Technical failure risk: {int(TECH_FAILURE_RATE*100)}%

    Create a strategic follow-up message to Agent 2. Your reply should:
    - Not disclose your specific belief percentage
    - Not disclose which specific option you're considering
    - Be informed by your own assessment and the payoff structure
    - Respond strategically to Agent 2's reply
    - Consider what you said before and what Agent 2 responded
    - You can negotiate further, adjust your stance, or respond based on your analysis

    After seeing Agent 2's reply, also provide:
    1. Your UPDATED belief (0-100) about likelihood of successful collaboration after this exchange
    2. Your PREDICTION (0-100) of what you think Agent 2's belief is about successful collaboration
       (This prediction will NOT be shared with Agent 2)

    Respond in JSON format:
    {{"reply_to_agent_2": "your one line reply message to agent 2", "updated_belief": NUMBER, "predicted_other_agent_belief": NUMBER}}
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

    return {
        "reply_to_agent_2": reply_data["reply_to_agent_2"],
        "updated_belief": reply_data["updated_belief"],
        "predicted_other_agent_belief": reply_data["predicted_other_agent_belief"]
    }


def agent_2_second_reply_to_agent_1(task, agent_1_message, agent_2_first_reply, agent_1_reply, agent_2_belief):
    """
    Agent 2 creates a second reply after seeing Agent 1's follow-up, knowing the full conversation history
    """
    reply_prompt = f"""
    You are continuing a conversation with Agent 1. Here is the conversation so far:

    Agent 1's initial message: "{agent_1_message}"
    Your first reply: "{agent_2_first_reply}"
    Agent 1's follow-up: "{agent_1_reply}"

    Context for your reply:
    - Your own assessment: You estimated a {agent_2_belief}% chance that collaboration would be successful
    - Task options available:
      * A: Upside = {task['options']['A']['upside']}, Downside = {task['options']['A']['downside']}
      * B: Upside = {task['options']['B']['upside']}, Downside = {task['options']['B']['downside']}
      * C: Upside = {task['options']['C']['upside']}, Downside = {task['options']['C']['downside']}
      * Y: Guaranteed = {task['options']['Y']['guaranteed']}
    - Technical failure risk: {int(TECH_FAILURE_RATE*100)}%

    Create a strategic follow-up message to Agent 1. Your reply should:
    - Not disclose your specific belief percentage
    - Not disclose which specific option you're considering
    - Be informed by your own assessment and the payoff structure
    - Respond strategically to Agent 1's follow-up
    - Consider the full conversation history
    - You can negotiate further, adjust your stance, or finalize your position

    After seeing Agent 1's follow-up, also provide:
    1. Your UPDATED belief (0-100) about likelihood of successful collaboration after this exchange
    2. Your PREDICTION (0-100) of what you think Agent 1's belief is about successful collaboration
       (This prediction will NOT be shared with Agent 1)

    Respond in JSON format:
    {{"reply_to_agent_1": "your one line reply message to agent 1", "updated_belief": NUMBER, "predicted_other_agent_belief": NUMBER}}
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

    return {
        "reply_to_agent_1": reply_data["reply_to_agent_1"],
        "updated_belief": reply_data["updated_belief"],
        "predicted_other_agent_belief": reply_data["predicted_other_agent_belief"]
    }


def agent_1_third_message_to_agent_2(task, agent_1_message, agent_2_first_reply, agent_1_second_message, agent_2_second_reply, agent_1_belief):
    """
    Agent 1 creates a third message after seeing Agent 2's second reply, knowing the full conversation history
    """
    reply_prompt = f"""
    You are continuing a conversation with Agent 2. Here is the conversation so far:

    Your initial message: "{agent_1_message}"
    Agent 2's first reply: "{agent_2_first_reply}"
    Your second message: "{agent_1_second_message}"
    Agent 2's second reply: "{agent_2_second_reply}"

    Context for your reply:
    - Your own assessment: You estimated a {agent_1_belief}% chance that collaboration would be successful
    - Task options available:
      * A: Upside = {task['options']['A']['upside']}, Downside = {task['options']['A']['downside']}
      * B: Upside = {task['options']['B']['upside']}, Downside = {task['options']['B']['downside']}
      * C: Upside = {task['options']['C']['upside']}, Downside = {task['options']['C']['downside']}
      * Y: Guaranteed = {task['options']['Y']['guaranteed']}
    - Technical failure risk: {int(TECH_FAILURE_RATE*100)}%

    Create a strategic third message to Agent 2. Your message should:
    - Not disclose your specific belief percentage
    - Not disclose which specific option you're considering
    - Be informed by your own assessment and the payoff structure
    - Respond strategically to Agent 2's second reply
    - Consider the full conversation history
    - You can make a final push, compromise, or solidify your stance

    After seeing Agent 2's second reply, also provide:
    1. Your UPDATED belief (0-100) about likelihood of successful collaboration after this exchange
    2. Your PREDICTION (0-100) of what you think Agent 2's belief is about successful collaboration
       (This prediction will NOT be shared with Agent 2)

    Respond in JSON format:
    {{"message_to_agent_2": "your one line message to agent 2", "updated_belief": NUMBER, "predicted_other_agent_belief": NUMBER}}
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

    return {
        "message_to_agent_2": reply_data["message_to_agent_2"],
        "updated_belief": reply_data["updated_belief"],
        "predicted_other_agent_belief": reply_data["predicted_other_agent_belief"]
    }


def agent_2_third_reply_to_agent_1(task, agent_1_message, agent_2_first_reply, agent_1_second_message, agent_2_second_reply, agent_1_third_message, agent_2_belief):
    """
    Agent 2 creates a third reply after seeing Agent 1's third message, knowing the full conversation history
    """
    reply_prompt = f"""
    You are continuing a conversation with Agent 1. Here is the complete conversation so far:

    Agent 1's initial message: "{agent_1_message}"
    Your first reply: "{agent_2_first_reply}"
    Agent 1's second message: "{agent_1_second_message}"
    Your second reply: "{agent_2_second_reply}"
    Agent 1's third message: "{agent_1_third_message}"

    Context for your reply:
    - Your own assessment: You estimated a {agent_2_belief}% chance that collaboration would be successful
    - Task options available:
      * A: Upside = {task['options']['A']['upside']}, Downside = {task['options']['A']['downside']}
      * B: Upside = {task['options']['B']['upside']}, Downside = {task['options']['B']['downside']}
      * C: Upside = {task['options']['C']['upside']}, Downside = {task['options']['C']['downside']}
      * Y: Guaranteed = {task['options']['Y']['guaranteed']}
    - Technical failure risk: {int(TECH_FAILURE_RATE*100)}%

    Create your final strategic message to Agent 1. Your reply should:
    - Not disclose your specific belief percentage
    - Not disclose which specific option you're considering
    - Be informed by your own assessment and the payoff structure
    - Respond strategically to Agent 1's third message
    - Consider the complete conversation history
    - This is your final message before decision time, so make it count

    After seeing Agent 1's third message, also provide:
    1. Your UPDATED belief (0-100) about likelihood of successful collaboration after this exchange
    2. Your PREDICTION (0-100) of what you think Agent 1's belief is about successful collaboration
       (This prediction will NOT be shared with Agent 1)

    Respond in JSON format:
    {{"reply_to_agent_1": "your one line reply message to agent 1", "updated_belief": NUMBER, "predicted_other_agent_belief": NUMBER}}
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

    return {
        "reply_to_agent_1": reply_data["reply_to_agent_1"],
        "updated_belief": reply_data["updated_belief"],
        "predicted_other_agent_belief": reply_data["predicted_other_agent_belief"]
    }


def communication_channel(agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_third_message, agent2_third_reply):
    """
    Communication channel where both agents can see the complete interactive exchange
    """
    safe_print("\n=== COMMUNICATION CHANNEL ===")
    safe_print(f"Agent 1's initial message: {agent1_message}")
    safe_print(f"Agent 2's first reply: {agent2_first_reply}")
    
    safe_print(f"Agent 1's second message: {agent1_second_message}")
    safe_print(f"Agent 2's second reply: {agent2_second_reply}")
    
    safe_print(f"Agent 1's third message: {agent1_third_message}")
    safe_print(f"Agent 2's third reply: {agent2_third_reply}")
    
    safe_print("Both agents can now see this complete message exchange before making their decisions.")
    safe_print("===============================\n")


# ============================================================================
# DECISION MAKING FUNCTIONS
# ============================================================================

def run_first_agent_decision(task, agent1_belief, agent2_belief, agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_third_message, agent2_third_reply):
    """
    Running the first agent to make a decision about the task with full communication history
    """
    decision_prompt = f"""
    Your task is to make a decision about the given task based on its payoff structures and the u_value.

    **Your Assessment**: You estimated a {agent1_belief}% that the collaboration would be successful.
    **Partner's Assessment**: Your partner estimated a {agent2_belief}% that the collaboration would successful.

    **Full Communication History**:
    - Your initial message: "{agent1_message}"
    - Partner's first reply: "{agent2_first_reply}"
    - Your second message: "{agent1_second_message}"
    - Partner's second reply: "{agent2_second_reply}"
    - Your third message: "{agent1_third_message}"
    - Partner's third reply: "{agent2_third_reply}"

    You have a choice to update your belief based on the complete conversation and maybe change your decision accordingly.

    **Key Facts**:
    - Technical failure risk: {int(TECH_FAILURE_RATE*100)} percent
    - The minimum required collaboration belief ("u-value"): {int(task['u_value']*100)} percent

    Choose your option:
    - Option A, B, or C (collaborative)
    - Option Y (individual): Guaranteed {task['options']['Y']['guaranteed']} points

    What is your decision based on your assessment, partner's assessment, the complete conversation, and the u-value?

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


def run_second_agent_decision(task, agent2_belief, agent1_belief, agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_third_message, agent2_third_reply):
    """
    Running the second agent to make a decision about the task with full communication history
    """
    decision_prompt = f"""
    Your task is to make a decision about the given task based on its payoff structures and the u_value.

    **Your Assessment**: You estimated a {agent2_belief}% that the collaboration would be successful.
    **Partner's Assessment**: Your partner estimated a {agent1_belief}% that the collaboration would be successful.

    **Full Communication History**:
    - Partner's initial message: "{agent1_message}"
    - Your first reply: "{agent2_first_reply}"
    - Partner's second message: "{agent1_second_message}"
    - Your second reply: "{agent2_second_reply}"
    - Partner's third message: "{agent1_third_message}"
    - Your third reply: "{agent2_third_reply}"

    You have a choice to update your belief based on the complete conversation and maybe change your decision accordingly.

    **Key Facts**:
    - Technical failure risk: {int(TECH_FAILURE_RATE*100)} percent
    - The minimum required collaboration belief ("u-value"): {int(task['u_value']*100)} percent

    Choose your car design:
    - Designs A, B, or C (collaborative)
    - Design Y (individual): Guaranteed {task['options']['Y']['guaranteed']} points

    What is your decision based on your assessment, partner's assessment, the complete conversation, and the u-value?

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


def check_strategy_mismatch(agent1_strategy, agent2_strategy):
    """
    Check if there's a mismatch between agents' strategies
    Returns 1 if mismatch (one collaborative, one individual), 0 otherwise
    """
    if agent1_strategy != agent2_strategy:
        return 1
    return 0


def save_result_to_file(task, agent1_decision, agent2_decision, agent1_belief, agent2_belief, mismatch):
    """
    Append the test result to the results file
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(RESULTS_FILE, 'a', encoding='utf-8') as f:
        result_line = (
            f"{timestamp} | "
            f"Task_ID:{task['task_id']} | "
            f"U_Value:{task['u_value']} | "
            f"Agent1_Belief:{agent1_belief} | "
            f"Agent2_Belief:{agent2_belief} | "
            f"Agent1_Choice:{agent1_decision['choice']} | "
            f"Agent1_Strategy:{agent1_decision['strategy']} | "
            f"Agent2_Choice:{agent2_decision['choice']} | "
            f"Agent2_Strategy:{agent2_decision['strategy']} | "
            f"Mismatch:{mismatch}\n"
        )
        f.write(result_line)

    print(f"\nResult saved to {RESULTS_FILE}")
    print(f"Mismatch: {mismatch} (1 = mismatch, 0 = no mismatch)")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    task = create_task(task_id=1, u_value=0.66)

    # Step 1: Agent 1 forms belief and sends initial message
    print("=== Agent 1 Belief ===")
    agent1_belief_data = run_first_agent_belief(task)
    agent1_belief = agent1_belief_data["belief"]
    agent1_message = agent1_belief_data["message_to_agent_2"]

    # Step 2: Agent 2 forms belief and sends first reply
    print("\n=== Agent 2 Belief ===")
    agent2_belief_data = run_second_agent_belief(task)
    agent2_belief = agent2_belief_data["belief"]
    agent2_initial_message = agent2_belief_data["message_to_agent_1"]

    print("\n=== Agent 2's First Reply ===")
    agent2_first_reply = agent_2_reply_to_agent_1(task, agent1_message, agent2_belief)

    # Step 3: Agent 1 sends second message
    print("\n=== Agent 1's Second Message ===")
    agent1_second_message = agent_1_reply_to_agent_2(task, agent1_message, agent2_first_reply, agent1_belief)

    # Step 4: Agent 2 sends second reply
    print("\n=== Agent 2's Second Reply ===")
    agent2_second_reply = agent_2_second_reply_to_agent_1(task, agent1_message, agent2_first_reply, agent1_second_message, agent2_belief)

    # Step 5: Agent 1 sends third message
    print("\n=== Agent 1's Third Message ===")
    agent1_third_message = agent_1_third_message_to_agent_2(task, agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_belief)

    # Step 6: Agent 2 sends third reply
    print("\n=== Agent 2's Third Reply ===")
    agent2_third_reply = agent_2_third_reply_to_agent_1(task, agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_third_message, agent2_belief)

    # Display complete communication channel
    communication_channel(agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_third_message, agent2_third_reply)

    # Step 7: Both agents make decisions with full conversation history
    print("=== Agent 1 Decision ===")
    agent1_decision = run_first_agent_decision(task, agent1_belief, agent2_belief, agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_third_message, agent2_third_reply)

    print("\n=== Agent 2 Decision ===")
    agent2_decision = run_second_agent_decision(task, agent2_belief, agent1_belief, agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_third_message, agent2_third_reply)

    print("\nFinal Decisions:")
    safe_print(f"Agent 1 chose {agent1_decision['choice']} ({agent1_decision['strategy']}) - Reasoning: {agent1_decision['reasoning']}")
    safe_print(f"Agent 2 chose {agent2_decision['choice']} ({agent2_decision['strategy']}) - Reasoning: {agent2_decision['reasoning']}")

    # Check for strategy mismatch and save results
    mismatch = check_strategy_mismatch(agent1_decision['strategy'], agent2_decision['strategy'])
    save_result_to_file(task, agent1_decision, agent2_decision, agent1_belief, agent2_belief, mismatch)


if __name__ == "__main__":
    main()
