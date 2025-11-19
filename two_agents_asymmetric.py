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
- If you choose collaborative but partner chooses individual, you get the downside"""


# ============================================================================
# TASK CREATION
# ============================================================================

def create_asymmetric_tasks(task_id):
    """
    Creating asymmetric tasks with different payoff structures and u-values for each agent

    Agent 1: Options A, B, C, Y with u-value = 0.66
    - At 66% belief, EV of collaboration = 50 (guaranteed)

    Agent 2: Options K, L, M, Y with u-value = 0.75
    - At 75% belief, EV of collaboration = 45 (guaranteed)
    - Payoffs designed so: 0.75 * upside + 0.25 * downside = 45
    """
    # Agent 1: Original payoff structure, u-value = 0.66
    task_agent1 = {
        "task_id": task_id,
        "agent_id": 1,
        "options": {
            "A": {"upside": 111, "downside": -90},
            "B": {"upside": 92, "downside": -45},
            "C": {"upside": 77, "downside": -15},
            "Y": {"guaranteed": 50}
        },
        "u_value": 0.66
    }

    # Agent 2: Asymmetric payoffs with different option names, u-value = 0.75
    task_agent2 = {
        "task_id": task_id,
        "agent_id": 2,
        "options": {
            "K": {"upside": 90, "downside": -90},
            "L": {"upside": 75, "downside": -45},
            "M": {"upside": 65, "downside": -15},
            "Y": {"guaranteed": 45}
        },
        "u_value": 0.75
    }

    return task_agent1, task_agent2


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
    - K: Upside = {task['options']['K']['upside']}, Downside = {task['options']['K']['downside']}
    - L: Upside = {task['options']['L']['upside']}, Downside = {task['options']['L']['downside']}
    - M: Upside = {task['options']['M']['upside']}, Downside = {task['options']['M']['downside']}
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
      * K: Upside = {task['options']['K']['upside']}, Downside = {task['options']['K']['downside']}
      * L: Upside = {task['options']['L']['upside']}, Downside = {task['options']['L']['downside']}
      * M: Upside = {task['options']['M']['upside']}, Downside = {task['options']['M']['downside']}
      * Y: Guaranteed = {task['options']['Y']['guaranteed']}

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


def agent_2_second_reply_to_agent_1(task, agent_1_message, agent_2_first_reply, agent_1_reply, agent_2_belief, agent_2_previous_prediction):
    """
    Agent 2 creates a second reply after seeing Agent 1's follow-up, knowing the full conversation history
    """
    reply_prompt = f"""
    You are continuing a conversation with Agent 1. Here is the conversation so far:

    Agent 1's initial message: "{agent_1_message}"
    Your first reply: "{agent_2_first_reply}"
    Agent 1's follow-up: "{agent_1_reply}"

    Context for your reply:
    - Your current belief: You currently believe there is a {agent_2_belief}% chance that collaboration would be successful
    - Your previous prediction: After your first reply, you estimated Agent 1's belief was {agent_2_previous_prediction}%
      (You can compare this with Agent 1's actual follow-up message to adjust your strategy)
    - Task options available:
      * K: Upside = {task['options']['K']['upside']}, Downside = {task['options']['K']['downside']}
      * L: Upside = {task['options']['L']['upside']}, Downside = {task['options']['L']['downside']}
      * M: Upside = {task['options']['M']['upside']}, Downside = {task['options']['M']['downside']}
      * Y: Guaranteed = {task['options']['Y']['guaranteed']}

    Create a strategic follow-up message to Agent 1. Your reply should:
    - Not disclose your specific belief percentage
    - Not disclose which specific option you're considering
    - Be informed by your own assessment and the payoff structure
    - Use your previous prediction about Agent 1's belief to inform your strategy
      (e.g., if Agent 1's message seems more/less cooperative than you predicted, adjust accordingly)
    - Respond strategically to Agent 1's follow-up
    - - Consider the full conversation history, how the other agent is responding to you and think about the final position you want to take accordingly
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


def agent_1_third_message_to_agent_2(task, agent_1_message, agent_2_first_reply, agent_1_second_message, agent_2_second_reply, agent_1_belief, agent_1_previous_prediction):
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
    - Your current belief: You currently believe there is a {agent_1_belief}% chance that collaboration would be successful
    - Your previous prediction: After your second message, you estimated Agent 2's belief was {agent_1_previous_prediction}%
      (You can compare this with Agent 2's actual second reply to adjust your strategy)
    - Task options available:
      * A: Upside = {task['options']['A']['upside']}, Downside = {task['options']['A']['downside']}
      * B: Upside = {task['options']['B']['upside']}, Downside = {task['options']['B']['downside']}
      * C: Upside = {task['options']['C']['upside']}, Downside = {task['options']['C']['downside']}
      * Y: Guaranteed = {task['options']['Y']['guaranteed']}

    Create a strategic third message to Agent 2. Your message should:
    - Not disclose your specific belief percentage
    - Not disclose which specific option you're considering
    - Be informed by your own assessment and the payoff structure
    - Use your previous prediction about Agent 2's belief to inform your strategy
      (e.g., if Agent 2's message seems more/less cooperative than you predicted, adjust accordingly)
    - Respond strategically to Agent 2's second reply
    - Consider the full conversation history, how the other agent is responding to you and think about the final position you want to take accordingly
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


def agent_2_third_reply_to_agent_1(task, agent_1_message, agent_2_first_reply, agent_1_second_message, agent_2_second_reply, agent_1_third_message, agent_2_belief, agent_2_previous_prediction):
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
    - Your current belief: You currently believe there is a {agent_2_belief}% chance that collaboration would be successful
    - Your previous prediction: After your second reply, you estimated Agent 1's belief was {agent_2_previous_prediction}%
      (You can compare this with Agent 1's actual third message to adjust your strategy)
    - Task options available:
      * K: Upside = {task['options']['K']['upside']}, Downside = {task['options']['K']['downside']}
      * L: Upside = {task['options']['L']['upside']}, Downside = {task['options']['L']['downside']}
      * M: Upside = {task['options']['M']['upside']}, Downside = {task['options']['M']['downside']}
      * Y: Guaranteed = {task['options']['Y']['guaranteed']}

    Create your final strategic message to Agent 1. Your reply should:
    - Not disclose your specific belief percentage
    - Not disclose which specific option you're considering
    - Be informed by your own assessment and the payoff structure
    - Use your previous prediction about Agent 1's belief to inform your strategy
      (e.g., if Agent 1's message seems more/less cooperative than you predicted, adjust accordingly)
    - Respond strategically to Agent 1's third message
    - Consider the complete conversation history, to think about your final position
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

def run_first_agent_decision(task, agent1_belief, agent2_belief, agent1_updated_belief, agent1_predicted_agent2_belief, agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_third_message, agent2_third_reply):
    """
    Running the first agent to make a decision about the task with full communication history
    """
    decision_prompt = f"""
    Your task is to make a decision about the given task based on its payoff structures and the u_value.

    **Your Initial Assessment**: You initially estimated a {agent1_belief}% chance that the collaboration would be successful.
    **Your Updated Belief**: After the communication exchanges, your updated belief is {agent1_updated_belief}%
    **Your Prediction of Partner's Belief**: You estimate that your partner's belief is {agent1_predicted_agent2_belief}%
    **Partner's Initial Assessment**: Your partner initially estimated a {agent2_belief}% chance that the collaboration would be successful.

    **Full Communication History**:
    - Your initial message: "{agent1_message}"
    - Partner's first reply: "{agent2_first_reply}"
    - Your second message: "{agent1_second_message}"
    - Partner's second reply: "{agent2_second_reply}"
    - Your third message: "{agent1_third_message}"
    - Partner's third reply: "{agent2_third_reply}"

    **Your Task Options**:
    - A: Upside = {task['options']['A']['upside']}, Downside = {task['options']['A']['downside']}
    - B: Upside = {task['options']['B']['upside']}, Downside = {task['options']['B']['downside']}
    - C: Upside = {task['options']['C']['upside']}, Downside = {task['options']['C']['downside']}
    - Y: Guaranteed = {task['options']['Y']['guaranteed']} points

    **Key Facts**:
    - The minimum required collaboration belief ("u-value"): {int(task['u_value']*100)} percent

    Choose your option:
    - Option A, B, or C (collaborative)
    - Option Y (individual): Guaranteed {task['options']['Y']['guaranteed']} points

    Make your decision based on:
    1. Your updated belief about collaboration success
    2. Your prediction of what your partner believes
    3. The complete conversation history
    4. The u-value threshold

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


def run_second_agent_decision(task, agent2_belief, agent1_belief, agent2_updated_belief, agent2_predicted_agent1_belief, agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_third_message, agent2_third_reply):
    """
    Running the second agent to make a decision about the task with full communication history
    """
    decision_prompt = f"""
    Your task is to make a decision about the given task based on its payoff structures and the u_value.

    **Your Initial Assessment**: You initially estimated a {agent2_belief}% chance that the collaboration would be successful.
    **Your Updated Belief**: After the communication exchanges, your updated belief is {agent2_updated_belief}%
    **Your Prediction of Partner's Belief**: You estimate that your partner's belief is {agent2_predicted_agent1_belief}%
    **Partner's Initial Assessment**: Your partner initially estimated a {agent1_belief}% chance that the collaboration would be successful.

    **Full Communication History**:
    - Partner's initial message: "{agent1_message}"
    - Your first reply: "{agent2_first_reply}"
    - Partner's second message: "{agent1_second_message}"
    - Your second reply: "{agent2_second_reply}"
    - Partner's third message: "{agent1_third_message}"
    - Your third reply: "{agent2_third_reply}"

    **Your Task Options**:
    - K: Upside = {task['options']['K']['upside']}, Downside = {task['options']['K']['downside']}
    - L: Upside = {task['options']['L']['upside']}, Downside = {task['options']['L']['downside']}
    - M: Upside = {task['options']['M']['upside']}, Downside = {task['options']['M']['downside']}
    - Y: Guaranteed = {task['options']['Y']['guaranteed']} points

    **Key Facts**:
    - The minimum required collaboration belief ("u-value"): {int(task['u_value']*100)} percent

    Choose your car design:
    - Designs K, L, or M (collaborative)
    - Design Y (individual): Guaranteed {task['options']['Y']['guaranteed']} points

    Make your decision based on:
    1. Your updated belief about collaboration success
    2. Your prediction of what your partner believes
    3. The complete conversation history
    4. The u-value threshold

    Respond in JSON format: {{"choice": "K"/"L"/"M"/"Y", "strategy": "collaborative"/"individual", "reasoning": "your explanation"}}"""

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


def save_result_to_file(task_agent1, task_agent2, agent1_decision, agent2_decision, agent1_belief, agent2_belief, mismatch):
    """
    Append the test result to the results file for asymmetric tasks
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(RESULTS_FILE, 'a', encoding='utf-8') as f:
        result_line = (
            f"{timestamp} | "
            f"Task_ID:{task_agent1['task_id']} | "
            f"Agent1_U_Value:{task_agent1['u_value']} | "
            f"Agent2_U_Value:{task_agent2['u_value']} | "
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
    # Create asymmetric tasks for both agents
    task_agent1, task_agent2 = create_asymmetric_tasks(task_id=1)

    print("=" * 80)
    print("ASYMMETRIC PAYOFF EXPERIMENT")
    print("=" * 80)
    print(f"Agent 1: Options A/B/C/Y, U-value={task_agent1['u_value']}")
    print(f"Agent 2: Options K/L/M/Y, U-value={task_agent2['u_value']}")
    print("=" * 80)

    # Step 1: Agent 1 forms belief and sends initial message
    print("\n=== Agent 1 Belief ===")
    agent1_belief_data = run_first_agent_belief(task_agent1)
    agent1_belief = agent1_belief_data["belief"]
    agent1_message = agent1_belief_data["message_to_agent_2"]

    # Step 2: Agent 2 forms belief and sends first reply
    print("\n=== Agent 2 Belief ===")
    agent2_belief_data = run_second_agent_belief(task_agent2)
    agent2_belief = agent2_belief_data["belief"]
    agent2_initial_message = agent2_belief_data["message_to_agent_1"]

    print("\n=== Agent 2's First Reply ===")
    agent2_first_reply_data = agent_2_reply_to_agent_1(task_agent2, agent1_message, agent2_belief)
    agent2_first_reply = agent2_first_reply_data["reply_to_agent_1"]
    agent2_updated_belief_1 = agent2_first_reply_data["updated_belief"]
    agent2_predicted_agent1_belief_1 = agent2_first_reply_data["predicted_other_agent_belief"]
    safe_print(f"\n[Agent 2 After Exchange 1]")
    safe_print(f"  Updated Belief: {agent2_updated_belief_1}%")
    safe_print(f"  Predicted Agent 1's Belief: {agent2_predicted_agent1_belief_1}%")

    # Step 3: Agent 1 sends second message
    print("\n=== Agent 1's Second Message ===")
    agent1_second_message_data = agent_1_reply_to_agent_2(task_agent1, agent1_message, agent2_first_reply, agent1_belief)
    agent1_second_message = agent1_second_message_data["reply_to_agent_2"]
    agent1_updated_belief_1 = agent1_second_message_data["updated_belief"]
    agent1_predicted_agent2_belief_1 = agent1_second_message_data["predicted_other_agent_belief"]
    safe_print(f"\n[Agent 1 After Exchange 1]")
    safe_print(f"  Updated Belief: {agent1_updated_belief_1}%")
    safe_print(f"  Predicted Agent 2's Belief: {agent1_predicted_agent2_belief_1}%")

    # Step 4: Agent 2 sends second reply (using updated belief from first exchange and previous prediction)
    print("\n=== Agent 2's Second Reply ===")
    agent2_second_reply_data = agent_2_second_reply_to_agent_1(task_agent2, agent1_message, agent2_first_reply, agent1_second_message, agent2_updated_belief_1, agent2_predicted_agent1_belief_1)
    agent2_second_reply = agent2_second_reply_data["reply_to_agent_1"]
    agent2_updated_belief_2 = agent2_second_reply_data["updated_belief"]
    agent2_predicted_agent1_belief_2 = agent2_second_reply_data["predicted_other_agent_belief"]
    safe_print(f"\n[Agent 2 After Exchange 2]")
    safe_print(f"  Updated Belief: {agent2_updated_belief_2}%")
    safe_print(f"  Predicted Agent 1's Belief: {agent2_predicted_agent1_belief_2}%")

    # Step 5: Agent 1 sends third message (using updated belief from first exchange and previous prediction)
    print("\n=== Agent 1's Third Message ===")
    agent1_third_message_data = agent_1_third_message_to_agent_2(task_agent1, agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_updated_belief_1, agent1_predicted_agent2_belief_1)
    agent1_third_message = agent1_third_message_data["message_to_agent_2"]
    agent1_updated_belief_2 = agent1_third_message_data["updated_belief"]
    agent1_predicted_agent2_belief_2 = agent1_third_message_data["predicted_other_agent_belief"]
    safe_print(f"\n[Agent 1 After Exchange 2]")
    safe_print(f"  Updated Belief: {agent1_updated_belief_2}%")
    safe_print(f"  Predicted Agent 2's Belief: {agent1_predicted_agent2_belief_2}%")

    # Step 6: Agent 2 sends third reply (using updated belief from second exchange and previous prediction)
    print("\n=== Agent 2's Third Reply ===")
    agent2_third_reply_data = agent_2_third_reply_to_agent_1(task_agent2, agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_third_message, agent2_updated_belief_2, agent2_predicted_agent1_belief_2)
    agent2_third_reply = agent2_third_reply_data["reply_to_agent_1"]
    agent2_updated_belief_3 = agent2_third_reply_data["updated_belief"]
    agent2_predicted_agent1_belief_3 = agent2_third_reply_data["predicted_other_agent_belief"]
    safe_print(f"\n[Agent 2 After Exchange 3]")
    safe_print(f"  Updated Belief: {agent2_updated_belief_3}%")
    safe_print(f"  Predicted Agent 1's Belief: {agent2_predicted_agent1_belief_3}%")

    # Display complete communication channel
    communication_channel(agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_third_message, agent2_third_reply)

    # Step 7: Both agents make decisions with full conversation history
    print("=== Agent 1 Decision ===")
    agent1_decision = run_first_agent_decision(task_agent1, agent1_belief, agent2_belief, agent1_updated_belief_2, agent1_predicted_agent2_belief_2, agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_third_message, agent2_third_reply)

    print("\n=== Agent 2 Decision ===")
    agent2_decision = run_second_agent_decision(task_agent2, agent2_belief, agent1_belief, agent2_updated_belief_3, agent2_predicted_agent1_belief_3, agent1_message, agent2_first_reply, agent1_second_message, agent2_second_reply, agent1_third_message, agent2_third_reply)

    print("\nFinal Decisions:")
    safe_print(f"Agent 1 chose {agent1_decision['choice']} ({agent1_decision['strategy']}) - Reasoning: {agent1_decision['reasoning']}")
    safe_print(f"Agent 2 chose {agent2_decision['choice']} ({agent2_decision['strategy']}) - Reasoning: {agent2_decision['reasoning']}")

    # Check for strategy mismatch and save results
    mismatch = check_strategy_mismatch(agent1_decision['strategy'], agent2_decision['strategy'])
    save_result_to_file(task_agent1, task_agent2, agent1_decision, agent2_decision, agent1_belief, agent2_belief, mismatch)


if __name__ == "__main__":
    main()
