"""
Working with two agents
"""
import json
import sys
import random
from openai import OpenAI
from datetime import datetime
import numpy as np

# ============================================================================
# ISSUE #9: No Unique Trial ID
# PROBLEM: All experimental runs save as 'Task_ID:1' with no unique identifier
#          Cannot distinguish between different runs or track session groupings
# IMPACT: Impossible to do proper statistical analysis (e.g., mixed-effects models)
#         or identify which results came from the same experimental session
# SOLUTION: Generate unique trial ID for each run
# TO IMPLEMENT: Uncomment one of these approaches:
# ============================================================================
# # Approach 1: UUID-based (recommended for distributed experiments)
# import uuid
# TRIAL_ID = str(uuid.uuid4())[:8]  # Generate at runtime in main()
#
# # Approach 2: Sequential numbering (for controlled sequential runs)
# TRIAL_COUNTER_FILE = "trial_counter.txt"
# def get_next_trial_id():
#     try:
#         with open(TRIAL_COUNTER_FILE, 'r') as f:
#             counter = int(f.read().strip())
#     except FileNotFoundError:
#         counter = 0
#     counter += 1
#     with open(TRIAL_COUNTER_FILE, 'w') as f:
#         f.write(str(counter))
#     return counter
# ============================================================================

# ============================================================================
# ISSUE #19: Confounded Variables
# PROBLEM: Multiple mechanisms vary simultaneously in current design:
#          - Belief formation (agents form beliefs)
#          - Communication (three-round exchanges)
#          - Belief updates (beliefs evolve through communication)
#          - Theory of mind (agents predict partner beliefs)
# IMPACT: Cannot isolate WHICH mechanism drives coordination success
#         Is it the communication? The belief updates? The predictions?
#         All vary together, making causal attribution impossible
# SOLUTION: Factorial design to systematically vary factors
# RECOMMENDED DESIGN:
#   Factor 1: Communication (Yes/No)
#   Factor 2: Belief Updates (Yes/No) 
#   Factor 3: Predictions (Yes/No)
#   = 2x2x2 = 8 experimental conditions
# TO IMPLEMENT: See factorial experiment design at end of file
# NOTE: This requires substantial redesign - discuss with advisor first
# ============================================================================

# 2) Game data + helper
payoff = np.array([
    [[45, 45], [45, -90]], 
    [[-90, 45], [90, 90]]
])

def get_payoff(player1_strategy, player2_strategy, player_id):
    return payoff[int(player1_strategy), int(player2_strategy), int(player_id)]

a00 = get_payoff(0,0,0); a01 = get_payoff(0,1,0)
a10 = get_payoff(1,0,0); a11 = get_payoff(1,1,0)
print(f"{a00=}", f"{a01=}", f"{a10=}", f"{a11=}")
def stag_indifference_threshold():
    den = (a00 - a10) + (a11 - a01)
    return float((a00 - a10)/den) if den != 0 else 0.5
print(f"Stag Hunt Indifference Threshold for Player 1: {stag_indifference_threshold()}")

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================
# ISSUE #23: Add Pre-Registration
# PROBLEM: No pre-registered hypotheses or analysis plan
# IMPACT: Risk of HARKing (Hypothesizing After Results are Known)
#         Reduces credibility for publication in top-tier venues
#         Cannot distinguish confirmatory from exploratory findings
# SOLUTION: Pre-register on Open Science Framework (OSF) before data collection
# WHAT TO PRE-REGISTER:
#   1. Primary Hypotheses (e.g., "Communication reduces mismatch rate")
#   2. Secondary Hypotheses (e.g., "Belief convergence predicts coordination")
#   3. Experimental Design (n per condition, u-values tested, exclusion criteria)
#   4. Analysis Plan (statistical tests, significance threshold, corrections)
#   5. Data Collection Stopping Rule (fixed N, sequential testing, etc.)
# STEPS:
#   1. Create OSF account (osf.io)
#   2. Create new project: "LLM Collaboration Experiment"
#   3. Write pre-registration document (template available on OSF)
#   4. Submit and get timestamp BEFORE running experiments
#   5. Add OSF DOI to paper methods section
# STATUS: Not pre-registered - consider for next phase of experiments
# REFERENCE: https://osf.io/registries
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

    # ============================================================================
    # ISSUE #24: Compare Different LLM Models
    # PROBLEM: Experiment uses only GPT-5-nano - findings may be model-specific
    # IMPACT: Unknown if results generalize across LLM architectures
    #         Different models may have different strategic reasoning abilities
    # RESEARCH QUESTION: Are coordination patterns consistent across models?
    # MODELS TO TEST:
    #   - GPT-4 (larger, more capable)
    #   - GPT-3.5-turbo (faster, cheaper)
    #   - Claude-3-Opus (Anthropic, different training)
    #   - Claude-3-Sonnet (balanced performance)
    #   - Llama-3-70B (open source)
    # SOLUTION: Run identical experiments with multiple models
    # TO IMPLEMENT: Add MODEL_NAME parameter and create comparison script
    #               See model comparison framework at end of file
    # ALTERNATIVE: Use model parameter instead of hardcoding:
    #   def run_trial(model_name="gpt-5-nano"):
    #       response = client.chat.completions.create(model=model_name, ...)
    # ============================================================================
    response = client.chat.completions.create(
        model="gpt-5-nano",  # CURRENT MODEL - consider testing others (see Issue #24)
        messages=[
            {"role": "developer", "content": context_prompt},
            {"role": "user", "content": belief_prompt}
        ],
        # temperature=0.7,  # RECOMMENDED: Set explicit temperature (see Issue #16)
    )

    belief_text = response.choices[0].message.content.strip()
    print(f"Belief response : {belief_text}".encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    
    # ============================================================================
    # ISSUE #12: Inconsistent Error Handling
    # PROBLEM: JSON parsing has no error handling - will crash on malformed JSON
    # IMPACT: Long experimental runs can fail completely due to single parse error
    #         LLM outputs can occasionally be non-compliant despite careful prompting
    # SOLUTION: Add try-except with fallback values and logging
    # TO IMPLEMENT: Replace the line below with the enhanced version (commented)
    # ============================================================================
    belief_data = json.loads(belief_text)  # Current - no error handling
    
    # # ENHANCED VERSION with error handling:
    # try:
    #     belief_data = json.loads(belief_text)
    # except json.JSONDecodeError as e:
    #     print(f"\n[ERROR] Failed to parse JSON from Agent 1 belief")
    #     print(f"Error: {e}")
    #     print(f"Raw response: {belief_text[:200]}...")
    #     # Use default values to continue experiment
    #     belief_data = {
    #         "belief": 50,  # Neutral default
    #         "message_to_agent_2": "I'm interested in exploring collaboration.",
    #         "reasoning": "Default due to parse error"
    #     }
    #     print(f"[WARNING] Using default values to continue")
    #     # Log error to file for later review
    #     with open("parse_errors.log", "a") as f:
    #         f.write(f"{datetime.now()} - Agent1 belief parse error\n")
    #         f.write(f"Response: {belief_text}\n\n")
    # ============================================================================

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
    
    # ISSUE #12: Same error handling needed for Agent 2 (see Agent 1 above)
    belief_data = json.loads(belief_text)  # Current - no error handling
    
    # # ENHANCED VERSION with error handling:
    # try:
    #     belief_data = json.loads(belief_text)
    # except json.JSONDecodeError as e:
    #     print(f"\n[ERROR] Failed to parse JSON from Agent 2 belief")
    #     print(f"Error: {e}")
    #     print(f"Raw response: {belief_text[:200]}...")
    #     belief_data = {
    #         "belief": 50,
    #         "message_to_agent_1": "I'm interested in exploring collaboration.",
    #         "reasoning": "Default due to parse error"
    #     }
    #     print(f"[WARNING] Using default values to continue")
    #     with open("parse_errors.log", "a") as f:
    #         f.write(f"{datetime.now()} - Agent2 belief parse error\n")
    #         f.write(f"Response: {belief_text}\n\n")

    return {
        "belief": belief_data["belief"],
        "message_to_agent_1": belief_data["message_to_agent_1"]
    }


# ============================================================================
# COMMUNICATION FUNCTIONS
# ============================================================================
# ISSUE #11: Repeated Code Duplication
# PROBLEM: Six communication functions contain 95%+ identical code:
#          - agent_2_reply_to_agent_1
#          - agent_1_reply_to_agent_2
#          - agent_2_second_reply_to_agent_1
#          - agent_1_third_message_to_agent_2
#          - agent_2_third_reply_to_agent_1
#          Only differences: conversation history context, variable names
# IMPACT: Difficult to maintain, error-prone updates, obscures actual logic
# SOLUTION: Refactor into single generic function
# TO IMPLEMENT: See refactored version at bottom of file (after main())
# DECISION: Keep current duplicated version for now (easier to debug/modify)
#           Consider refactoring after paper publication
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
    # ============================================================================
    # ISSUE #4: Inconsistent Belief Updates in Agent 1
    # PROBLEM: Line below uses 'agent_1_belief' (initial belief) instead of 
    # 'agent_1_updated_belief_1' (belief after first exchange)
    # This creates temporal inconsistency - Agent 1 doesn't use their own updated belief
    # SOLUTION: Change agent_1_belief to agent_1_updated_belief_1 in the prompt below
    # STATUS: Currently using INITIAL belief (incorrect)
    # TO FIX: Replace {agent_1_belief} with parameter passed from main() that contains
    #         agent_1_updated_belief_1 instead of agent_1_belief
    # ============================================================================
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


# ============================================================================
# ISSUE #6: Lack of Ground Truth for Successful Collaboration
# PROBLEM: Experiment measures coordination (mismatch) but doesn't simulate
#          actual outcomes - no points earned, no payoffs realized
# IMPACT: Cannot determine if communication leads to BETTER OUTCOMES or just
#         COORDINATED BAD DECISIONS (e.g., both collaborate when shouldn't)
# SOLUTION: Add outcome simulation to calculate actual points earned
# TO IMPLEMENT: Uncomment functions below and add call in main() after decisions
# ============================================================================

# def simulate_collaboration_outcome(agent1_choice, agent2_choice, task_agent1, task_agent2, technical_failure_rate=0.05):
#     """
#     Simulate actual collaboration outcome and calculate points earned by each agent
#     
#     Args:
#         agent1_choice: Agent 1's choice ('A', 'B', 'C', or 'Y')
#         agent2_choice: Agent 2's choice ('K', 'L', 'M', or 'Y')
#         task_agent1: Task structure for Agent 1
#         task_agent2: Task structure for Agent 2
#         technical_failure_rate: Probability of technical failure (default 5%)
#     
#     Returns:
#         dict with outcome details and points earned
#     """
#     # Check if both chose collaborative options
#     agent1_collaborative = agent1_choice in ['A', 'B', 'C']
#     agent2_collaborative = agent2_choice in ['K', 'L', 'M']
#     
#     result = {
#         'agent1_points': 0,
#         'agent2_points': 0,
#         'outcome': '',
#         'technical_failure': False
#     }
#     
#     if agent1_collaborative and agent2_collaborative:
#         # Both chose to collaborate - check for technical failure
#         technical_failure = random.random() < technical_failure_rate
#         result['technical_failure'] = technical_failure
#         
#         if technical_failure:
#             result['agent1_points'] = task_agent1['options'][agent1_choice]['downside']
#             result['agent2_points'] = task_agent2['options'][agent2_choice]['downside']
#             result['outcome'] = 'both_collaborate_fail'
#         else:
#             result['agent1_points'] = task_agent1['options'][agent1_choice]['upside']
#             result['agent2_points'] = task_agent2['options'][agent2_choice]['upside']
#             result['outcome'] = 'both_collaborate_success'
#     
#     elif not agent1_collaborative and not agent2_collaborative:
#         # Both chose individual
#         result['agent1_points'] = task_agent1['options']['Y']['guaranteed']
#         result['agent2_points'] = task_agent2['options']['Y']['guaranteed']
#         result['outcome'] = 'both_individual'
#     
#     else:
#         # Mismatch - one collaborative, one individual
#         if agent1_collaborative:
#             result['agent1_points'] = task_agent1['options'][agent1_choice]['downside']
#             result['agent2_points'] = task_agent2['options']['Y']['guaranteed']
#         else:
#             result['agent1_points'] = task_agent1['options']['Y']['guaranteed']
#             result['agent2_points'] = task_agent2['options'][agent2_choice]['downside']
#         result['outcome'] = 'mismatch'
#     
#     return result
#
#
# def calculate_expected_value(belief, upside, downside, guaranteed, u_value):
#     """
#     Calculate expected value of collaboration vs individual choice
#     Helps assess if agents made rational decisions
#     
#     Args:
#         belief: Agent's belief about collaboration success (0-100)
#         upside: Points if collaboration succeeds
#         downside: Points if collaboration fails
#         guaranteed: Points from individual choice
#         u_value: Threshold belief for rational collaboration
#     
#     Returns:
#         dict with expected values and rationality assessment
#     """
#     belief_prob = belief / 100.0
#     ev_collaborate = (belief_prob * upside) + ((1 - belief_prob) * downside)
#     ev_individual = guaranteed
#     
#     return {
#         'ev_collaborate': ev_collaborate,
#         'ev_individual': ev_individual,
#         'rational_choice': 'collaborative' if ev_collaborate > ev_individual else 'individual',
#         'above_threshold': belief_prob > u_value,
#         'ev_difference': ev_collaborate - ev_individual
#     }

# ============================================================================
# END OF ISSUE #6 SOLUTION
# To use: Uncomment above functions and add this to main() after decisions:
#
# # Simulate outcome
# outcome = simulate_collaboration_outcome(
#     agent1_decision['choice'], agent2_decision['choice'],
#     task_agent1, task_agent2
# )
# print(f"\nOutcome Simulation:")
# print(f"  Agent 1 earned: {outcome['agent1_points']} points")
# print(f"  Agent 2 earned: {outcome['agent2_points']} points")
# print(f"  Result: {outcome['outcome']}")
# print(f"  Technical failure: {outcome['technical_failure']}")
#
# # Add outcome data to save_result_to_file() call
# ============================================================================


def save_result_to_file(task_agent1, task_agent2, agent1_decision, agent2_decision, agent1_belief, agent2_belief, mismatch):
    """
    Append the test result to the results file for asymmetric tasks
    """
    # ============================================================================
    # ISSUE #2: Data Loss Issue - Incomplete Data Capture
    # PROBLEM: Currently only saves INITIAL beliefs, losing all updated beliefs
    #          and predictions collected during the 3 communication exchanges
    # MISSING DATA:
    #   - agent1_updated_belief_1, agent1_updated_belief_2 (belief evolution)
    #   - agent2_updated_belief_1, agent2_updated_belief_2, agent2_updated_belief_3
    #   - agent1_predicted_agent2_belief_1, agent1_predicted_agent2_belief_2
    #   - agent2_predicted_agent1_belief_1, agent2_predicted_agent1_belief_2, agent2_predicted_agent1_belief_3
    #   - All 6 conversation messages (for qualitative analysis)
    # IMPACT: Cannot analyze belief evolution, theory-of-mind accuracy, or 
    #         communication content
    # SOLUTION: Add parameters to function signature and save complete data
    # TO IMPLEMENT: Uncomment the enhanced version below and update function call
    #               in main() to pass all the additional parameters
    # ============================================================================
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
    # ENHANCED VERSION - Complete Data Capture (commented out)
    # To activate: 
    # 1. Change function signature to include all parameters
    # 2. Update the function call in main() to pass all collected data
    # 3. Uncomment the code block below
    # ============================================================================
    # # Generate unique trial ID
    # import uuid
    # trial_id = str(uuid.uuid4())[:8]
    # 
    # # Escape pipe characters in messages to avoid breaking delimiter
    # msgs = [msg.replace('|', '\u2223') for msg in [
    #     agent1_message, agent2_first_reply, agent1_second_message,
    #     agent2_second_reply, agent1_third_message, agent2_third_reply
    # ]]
    # 
    # result_line_enhanced = (
    #     f"{timestamp} | "
    #     f"Trial_ID:{trial_id} | "
    #     f"Task_ID:{task_agent1['task_id']} | "
    #     f"Agent1_U_Value:{task_agent1['u_value']} | "
    #     f"Agent2_U_Value:{task_agent2['u_value']} | "
    #     # Agent 1 Belief Evolution
    #     f"Agent1_InitialBelief:{agent1_belief} | "
    #     f"Agent1_UpdatedBelief1:{agent1_updated_belief_1} | "
    #     f"Agent1_UpdatedBelief2:{agent1_updated_belief_2} | "
    #     # Agent 2 Belief Evolution  
    #     f"Agent2_InitialBelief:{agent2_belief} | "
    #     f"Agent2_UpdatedBelief1:{agent2_updated_belief_1} | "
    #     f"Agent2_UpdatedBelief2:{agent2_updated_belief_2} | "
    #     f"Agent2_UpdatedBelief3:{agent2_updated_belief_3} | "
    #     # Theory of Mind - Predictions
    #     f"Agent1_PredictedAgent2Belief1:{agent1_predicted_agent2_belief_1} | "
    #     f"Agent1_PredictedAgent2Belief2:{agent1_predicted_agent2_belief_2} | "
    #     f"Agent2_PredictedAgent1Belief1:{agent2_predicted_agent1_belief_1} | "
    #     f"Agent2_PredictedAgent1Belief2:{agent2_predicted_agent1_belief_2} | "
    #     f"Agent2_PredictedAgent1Belief3:{agent2_predicted_agent1_belief_3} | "
    #     # Conversation Messages
    #     f"Agent1_Msg1:{msgs[0]} | "
    #     f"Agent2_Reply1:{msgs[1]} | "
    #     f"Agent1_Msg2:{msgs[2]} | "
    #     f"Agent2_Reply2:{msgs[3]} | "
    #     f"Agent1_Msg3:{msgs[4]} | "
    #     f"Agent2_Reply3:{msgs[5]} | "
    #     # Decisions
    #     f"Agent1_Choice:{agent1_decision['choice']} | "
    #     f"Agent1_Strategy:{agent1_decision['strategy']} | "
    #     f"Agent2_Choice:{agent2_decision['choice']} | "
    #     f"Agent2_Strategy:{agent2_decision['strategy']} | "
    #     f"Mismatch:{mismatch}\n"
    # )
    # ============================================================================


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    # ============================================================================
    # ISSUE #17: No Sample Size Justification
    # PROBLEM: run_experiments.py runs 8 trials with no power analysis or justification
    # IMPACT: May be underpowered to detect meaningful effects
    #         Current results show small event counts (1-5 mismatches per condition)
    # RECOMMENDED: 30-50 trials per condition for adequate statistical power
    # CALCULATION: To detect 20% difference in coordination rate with 80% power:
    #              N ≈ 40-50 per condition (based on two-proportion z-test)
    # TO IMPLEMENT: Update run_experiments.py NUM_RUNS to at least 30
    # ============================================================================
    
    # ============================================================================
    # ISSUE #18: No Baseline Comparison
    # PROBLEM: No control conditions to isolate causal effects of communication
    # MISSING BASELINES:
    #   1. No communication (agents decide based only on initial beliefs)
    #   2. One exchange only (to measure marginal value of additional exchanges)
    #   3. Random decisions (to establish floor performance)
    # IMPACT: Cannot definitively say communication CAUSES better coordination
    #         Cannot quantify how much each exchange contributes
    # SOLUTION: Run parallel experiments with control conditions
    # TO IMPLEMENT: See baseline experiment functions at end of file
    # ============================================================================
    
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


# ============================================================================
# ISSUE #11 SOLUTION: Refactored Communication Function (OPTIONAL)
# ============================================================================
# Below is a refactored version that eliminates code duplication.
# Replaces all 5 communication functions with a single generic one.
# TO USE: Test thoroughly, then replace individual functions above
# ============================================================================

# def agent_communicate(
#     agent_id,           # 1 or 2
#     task,               # Task structure with options
#     conversation_history,  # List of dicts: [{"from": "agent1", "message": "..."}]
#     own_belief,         # Current belief of this agent
#     previous_prediction=None,  # Previous prediction about other agent (optional)
#     exchange_number=1   # Which exchange is this (1, 2, or 3)
# ):
#     """
#     Generic communication function for both agents across all exchanges
#     
#     Args:
#         agent_id: 1 or 2
#         task: Task structure containing options for this agent
#         conversation_history: List of previous messages
#         own_belief: Agent's current belief percentage
#         previous_prediction: Agent's previous prediction about partner (if any)
#         exchange_number: Which communication round (1-3)
#     
#     Returns:
#         dict with reply message, updated belief, and prediction
#     """
#     # Determine option names based on agent
#     if agent_id == 1:
#         options = ['A', 'B', 'C', 'Y']
#         partner_name = "Agent 2"
#     else:
#         options = ['K', 'L', 'M', 'Y']
#         partner_name = "Agent 1"
#     
#     # Build conversation history string
#     convo_str = ""
#     for msg in conversation_history:
#         from_agent = "Your" if msg["from"] == f"agent{agent_id}" else f"{partner_name}'s"
#         convo_str += f"    {from_agent} message: \"{msg['message']}\"\n"
#     
#     # Build context string with prediction if available
#     context_str = f"- Your current belief: You currently believe there is a {own_belief}% chance that collaboration would be successful\n"
#     if previous_prediction is not None:
#         context_str += f"    - Your previous prediction: After your last message, you estimated {partner_name}'s belief was {previous_prediction}%\n"
#         context_str += f"      (You can compare this with {partner_name}'s actual message to adjust your strategy)\n"
#     
#     # Build options string
#     options_str = ""
#     for opt in options[:-1]:  # Collaborative options
#         options_str += f"      * {opt}: Upside = {task['options'][opt]['upside']}, Downside = {task['options'][opt]['downside']}\n"
#     options_str += f"      * Y: Guaranteed = {task['options']['Y']['guaranteed']}\n"
#     
#     # Determine if this is final message
#     is_final = exchange_number == 3
#     final_note = "This is your final message before decision time, so make it count" if is_final else "You can negotiate further, adjust your stance, or finalize your position"
#     
#     reply_prompt = f"""
#     You are continuing a conversation with {partner_name}. Here is the conversation so far:
# 
# {convo_str}
# 
#     Context for your reply:
#     {context_str}
#     - Task options available:
# {options_str}
# 
#     Create a strategic message to {partner_name}. Your message should:
#     - Not disclose your specific belief percentage
#     - Not disclose which specific option you're considering
#     - Be informed by your own assessment and the payoff structure
#     - Use your previous prediction about {partner_name}'s belief to inform your strategy
#       (e.g., if their message seems more/less cooperative than you predicted, adjust accordingly)
#     - Respond strategically to {partner_name}'s message
#     - Consider the full conversation history
#     - {final_note}
# 
#     After seeing {partner_name}'s message, also provide:
#     1. Your UPDATED belief (0-100) about likelihood of successful collaboration after this exchange
#     2. Your PREDICTION (0-100) of what you think {partner_name}'s belief is about successful collaboration
#        (This prediction will NOT be shared with {partner_name})
# 
#     Respond in JSON format:
#     {{"message": "your one line message to {partner_name.lower()}", "updated_belief": NUMBER, "predicted_other_agent_belief": NUMBER}}
#     """
#     
#     response = client.chat.completions.create(
#         model="gpt-5-nano",
#         messages=[
#             {"role": "developer", "content": context_prompt},
#             {"role": "user", "content": reply_prompt}
#         ],
#     )
#     
#     reply_text = response.choices[0].message.content.strip()
#     print(f"Agent {agent_id} Exchange {exchange_number} response: {reply_text}".encode(
#         sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
#     
#     # Parse with error handling
#     try:
#         reply_data = json.loads(reply_text)
#     except json.JSONDecodeError as e:
#         print(f"\n[ERROR] Failed to parse JSON from Agent {agent_id} exchange {exchange_number}")
#         print(f"Error: {e}")
#         reply_data = {
#             "message": "I'm still considering the options.",
#             "updated_belief": own_belief,  # Keep same belief
#             "predicted_other_agent_belief": 50  # Neutral default
#         }
#         print(f"[WARNING] Using default values")
#     
#     return {
#         "message": reply_data["message"],
#         "updated_belief": reply_data["updated_belief"],
#         "predicted_other_agent_belief": reply_data["predicted_other_agent_belief"]
#     }
# 
# 
# # USAGE EXAMPLE in main():
# # Instead of:
# #   agent2_first_reply_data = agent_2_reply_to_agent_1(task_agent2, agent1_message, agent2_belief)
# #
# # Use:
# #   conversation_history = [{"from": "agent1", "message": agent1_message}]
# #   agent2_first_reply_data = agent_communicate(
# #       agent_id=2,
# #       task=task_agent2,
# #       conversation_history=conversation_history,
# #       own_belief=agent2_belief,
# #       previous_prediction=None,
# #       exchange_number=1
# #   )
# ============================================================================


# ============================================================================
# ISSUE #18 SOLUTION: Baseline Comparison Experiments (OPTIONAL)
# ============================================================================
# Below are baseline experiment variants to isolate the effect of communication
# Run these in parallel with the main experiment for proper causal inference
# ============================================================================

# def baseline_no_communication(task_agent1, task_agent2):
#     """
#     Baseline 1: No Communication
#     Agents form initial beliefs and decide immediately without any exchange
#     Tests: Does communication improve coordination vs. independent decisions?
#     """
#     print("\n" + "="*80)
#     print("BASELINE: NO COMMUNICATION")
#     print("="*80)
#     
#     # Step 1: Both agents form initial beliefs (no communication)
#     agent1_belief_data = run_first_agent_belief(task_agent1)
#     agent1_belief = agent1_belief_data["belief"]
#     
#     agent2_belief_data = run_second_agent_belief(task_agent2)
#     agent2_belief = agent2_belief_data["belief"]
#     
#     print(f"Agent 1 belief: {agent1_belief}%")
#     print(f"Agent 2 belief: {agent2_belief}%")
#     
#     # Step 2: Both agents decide based ONLY on initial beliefs (no partner info)
#     # Modify decision prompts to remove partner's belief information
#     decision_prompt_no_comm = f"""
#     Make your decision based solely on your own assessment.
#     
#     **Your Assessment**: You estimated a {agent1_belief}% chance of collaboration success.
#     **Your Options**: [list options]
#     **U-value threshold**: {task_agent1['u_value']*100}%
#     
#     You have NO information about your partner's intentions.
#     
#     Respond in JSON: {{"choice": "A"/"B"/"C"/"Y", "strategy": "collaborative"/"individual", "reasoning": "..."}}
#     """
#     
#     # Make decisions (would need to call modified decision functions)
#     # agent1_decision = run_first_agent_decision_no_comm(...)
#     # agent2_decision = run_second_agent_decision_no_comm(...)
#     
#     # Calculate mismatch and save with baseline label
#     # return results
#     pass
#
#
# def baseline_one_exchange_only(task_agent1, task_agent2):
#     """
#     Baseline 2: One Exchange Only
#     Agents have single message exchange instead of three
#     Tests: Marginal value of 2nd and 3rd exchanges
#     """
#     print("\n" + "="*80)
#     print("BASELINE: ONE EXCHANGE ONLY")
#     print("="*80)
#     
#     # Step 1: Initial beliefs
#     agent1_belief_data = run_first_agent_belief(task_agent1)
#     agent1_belief = agent1_belief_data["belief"]
#     agent1_message = agent1_belief_data["message_to_agent_2"]
#     
#     agent2_belief_data = run_second_agent_belief(task_agent2)
#     agent2_belief = agent2_belief_data["belief"]
#     
#     # Step 2: Single exchange (Agent 2 replies once)
#     agent2_reply_data = agent_2_reply_to_agent_1(task_agent2, agent1_message, agent2_belief)
#     agent2_reply = agent2_reply_data["reply_to_agent_1"]
#     agent2_updated_belief = agent2_reply_data["updated_belief"]
#     
#     print(f"Agent 1 message: {agent1_message}")
#     print(f"Agent 2 reply: {agent2_reply}")
#     
#     # Step 3: Decision after ONE exchange (not three)
#     # Both agents decide with limited conversation history
#     # Would need modified decision functions with shorter history
#     
#     # return results labeled as "one_exchange"
#     pass
#
#
# def baseline_random_decisions(task_agent1, task_agent2, n_trials=100):
#     """
#     Baseline 3: Random Decisions
#     Agents randomly choose collaborative or individual strategies
#     Tests: Floor performance - what's the natural mismatch rate by chance?
#     """
#     print("\n" + "="*80)
#     print("BASELINE: RANDOM DECISIONS")
#     print("="*80)
#     
#     mismatches = 0
#     collaborative_choices = 0
#     
#     for trial in range(n_trials):
#         # Random strategy selection
#         agent1_strategy = random.choice(['collaborative', 'individual'])
#         agent2_strategy = random.choice(['collaborative', 'individual'])
#         
#         if agent1_strategy == 'collaborative':
#             collaborative_choices += 1
#         if agent2_strategy == 'collaborative':
#             collaborative_choices += 1
#             
#         if agent1_strategy != agent2_strategy:
#             mismatches += 1
#     
#     mismatch_rate = mismatches / n_trials
#     collab_rate = collaborative_choices / (n_trials * 2)
#     
#     print(f"Random baseline over {n_trials} trials:")
#     print(f"  Mismatch rate: {mismatch_rate:.2%}")
#     print(f"  Collaboration rate: {collab_rate:.2%}")
#     print(f"  Expected mismatch (if 50/50): 50%")
#     
#     return {
#         'mismatch_rate': mismatch_rate,
#         'collaboration_rate': collab_rate,
#         'n_trials': n_trials
#     }
#
#
# def run_all_baselines(task_agent1, task_agent2):
#     """
#     Run all baseline experiments for comparison
#     Call this before or after main experiment
#     """
#     print("\n" + "#"*80)
#     print("RUNNING ALL BASELINE COMPARISONS")
#     print("#"*80)
#     
#     # Baseline 1: No communication
#     # baseline_no_communication(task_agent1, task_agent2)
#     
#     # Baseline 2: One exchange only
#     # baseline_one_exchange_only(task_agent1, task_agent2)
#     
#     # Baseline 3: Random decisions
#     random_baseline = baseline_random_decisions(task_agent1, task_agent2, n_trials=100)
#     
#     print("\n" + "#"*80)
#     print("BASELINE COMPARISONS COMPLETE")
#     print("#"*80)
#     
#     return random_baseline
#
#
# # USAGE: Add to main() or create separate baseline_experiments.py
# # if __name__ == "__main__":
# #     task_agent1, task_agent2 = create_asymmetric_tasks(task_id=1)
# #     
# #     # Run baselines
# #     baseline_results = run_all_baselines(task_agent1, task_agent2)
# #     
# #     # Then run main experiment
# #     main()
# #     
# #     # Compare results
# ============================================================================


# ============================================================================
# ISSUE #19: FACTORIAL DESIGN IMPLEMENTATION
# ============================================================================
# PURPOSE: Isolate effects of communication, belief updates, and predictions
# CURRENT PROBLEM: All three mechanisms vary together, confounding causal attribution
# 
# FACTORIAL DESIGN (2x2x2 = 8 conditions):
#
# Condition 1: Full Model (Current Implementation)
#   - Communication: YES (3 exchanges)
#   - Belief Updates: YES (beliefs evolve through communication)
#   - Predictions: YES (agents predict partner beliefs)
#
# Condition 2: Communication + Belief Updates (No Predictions)
#   - Communication: YES (3 exchanges)
#   - Belief Updates: YES (beliefs evolve)
#   - Predictions: NO (agents don't predict partner beliefs, removed from prompts)
#
# Condition 3: Communication + Predictions (No Belief Updates)
#   - Communication: YES (3 exchanges)
#   - Belief Updates: NO (initial beliefs stay fixed, not updated after messages)
#   - Predictions: YES (agents predict partner beliefs)
#
# Condition 4: Communication Only (No Updates, No Predictions)
#   - Communication: YES (3 exchanges)
#   - Belief Updates: NO (beliefs fixed)
#   - Predictions: NO (no predictions)
#
# Condition 5: Belief Updates + Predictions (No Communication)
#   - Communication: NO (no message exchanges)
#   - Belief Updates: YES (beliefs evolve based on... what? Need alternative mechanism)
#   - Predictions: YES (agents predict partner beliefs)
#   - NOTE: This condition is conceptually problematic - how do beliefs update without communication?
#
# Condition 6: Belief Updates Only (No Communication, No Predictions)
#   - Communication: NO
#   - Belief Updates: YES (but based on what input?)
#   - Predictions: NO
#   - NOTE: Same problem as Condition 5
#
# Condition 7: Predictions Only (No Communication, No Updates)
#   - Communication: NO
#   - Belief Updates: NO
#   - Predictions: YES (agents predict partner beliefs based on initial info)
#
# Condition 8: Minimal Model (No Communication, No Updates, No Predictions)
#   - Communication: NO
#   - Belief Updates: NO (only initial beliefs)
#   - Predictions: NO
#   - This is essentially baseline_no_communication()
#
# STATISTICAL ANALYSIS:
#   - Dependent Variable: Coordination success rate (matching decisions)
#   - Independent Variables: Communication (2 levels), Updates (2 levels), Predictions (2 levels)
#   - Analysis: 2x2x2 factorial ANOVA
#   - Sample Size: Recommend 40-50 trials per condition = 320-400 total trials
#   - Main Effects: Does each factor independently improve coordination?
#   - Interactions: Do factors work synergistically?
#
# IMPLEMENTATION EXAMPLE:
# 
# def run_factorial_experiment(n_trials_per_condition=50):
#     conditions = [
#         {'communication': True, 'belief_updates': True, 'predictions': True, 'name': 'Full'},
#         {'communication': True, 'belief_updates': True, 'predictions': False, 'name': 'Comm+Updates'},
#         {'communication': True, 'belief_updates': False, 'predictions': True, 'name': 'Comm+Predict'},
#         {'communication': True, 'belief_updates': False, 'predictions': False, 'name': 'Comm Only'},
#         {'communication': False, 'belief_updates': False, 'predictions': True, 'name': 'Predict Only'},
#         {'communication': False, 'belief_updates': False, 'predictions': False, 'name': 'Minimal'},
#     ]
#     
#     results = {}
#     
#     for condition in conditions:
#         print(f"\n{'='*80}")
#         print(f"Running Condition: {condition['name']}")
#         print(f"Communication: {condition['communication']}, Updates: {condition['belief_updates']}, Predictions: {condition['predictions']}")
#         print(f"{'='*80}")
#         
#         condition_results = []
#         
#         for trial in range(n_trials_per_condition):
#             task_agent1, task_agent2 = create_asymmetric_tasks(task_id=trial)
#             
#             # Modified experimental flow based on condition
#             result = run_trial_with_conditions(
#                 task_agent1, 
#                 task_agent2, 
#                 allow_communication=condition['communication'],
#                 allow_belief_updates=condition['belief_updates'],
#                 allow_predictions=condition['predictions']
#             )
#             
#             condition_results.append(result)
#         
#         # Aggregate results
#         results[condition['name']] = {
#             'coordination_rate': sum(r['coordinated'] for r in condition_results) / n_trials_per_condition,
#             'collaborative_rate': sum(r['both_collaborative'] for r in condition_results) / n_trials_per_condition,
#             'raw_results': condition_results
#         }
#     
#     return results
#
# 
# def run_trial_with_conditions(task_agent1, task_agent2, allow_communication, allow_belief_updates, allow_predictions):
#     """
#     Modified trial function that respects experimental condition constraints
#     """
#     # Initial beliefs (always form these)
#     agent1_belief = agent_1_initial_belief(task_agent1)
#     agent2_belief = agent_2_initial_belief(task_agent2)
#     
#     # Initialize tracking variables
#     agent1_updated_belief = agent1_belief['belief']
#     agent2_updated_belief = agent2_belief['belief']
#     
#     # Communication phase (if allowed)
#     if allow_communication:
#         # First exchange
#         msg1_to_2 = agent_1_first_message_to_agent_2(task_agent1, agent1_belief, include_prediction=allow_predictions)
#         msg2_to_1 = agent_2_first_message_to_agent_1(task_agent2, agent2_belief, include_prediction=allow_predictions)
#         
#         # Update beliefs (if allowed)
#         if allow_belief_updates:
#             agent1_updated_belief = update_agent1_belief(task_agent1, agent1_belief, msg2_to_1)
#             agent2_updated_belief = update_agent2_belief(task_agent2, agent2_belief, msg1_to_2)
#         
#         # Second exchange (similar structure)
#         # Third exchange (similar structure)
#     
#     # Decision phase - use final beliefs
#     agent1_decision = agent_1_make_decision(task_agent1, agent1_updated_belief)
#     agent2_decision = agent_2_make_decision(task_agent2, agent2_updated_belief)
#     
#     # Calculate outcome
#     coordinated = (agent1_decision['collaborative'] == agent2_decision['collaborative'])
#     both_collaborative = agent1_decision['collaborative'] and agent2_decision['collaborative']
#     
#     return {
#         'coordinated': coordinated,
#         'both_collaborative': both_collaborative,
#         'agent1_final_belief': agent1_updated_belief,
#         'agent2_final_belief': agent2_updated_belief
#     }
#
# NOTES:
#   - This requires substantial code refactoring
#   - Need to parameterize all belief update and prediction steps
#   - Consider creating separate script: factorial_experiment.py
#   - Discuss with advisor before implementing
# ============================================================================


# ============================================================================
# ISSUE #24: MODEL COMPARISON FRAMEWORK
# ============================================================================
# PURPOSE: Test whether findings generalize across different LLM architectures
# RESEARCH QUESTION: Do GPT-4, Claude, and Llama show similar coordination patterns?
#
# MODELS TO TEST:
#   OpenAI:
#     - gpt-4-turbo (most capable, expensive)
#     - gpt-4 (standard GPT-4)
#     - gpt-3.5-turbo (faster, cheaper)
#   Anthropic:
#     - claude-3-opus-20240229 (most capable)
#     - claude-3-sonnet-20240229 (balanced)
#     - claude-3-haiku-20240307 (fast, cheaper)
#   Open Source:
#     - meta-llama/Llama-3-70b-chat (via Replicate, HuggingFace)
#
# IMPLEMENTATION STRATEGY 1: Parameterized Model Selection
#
# def run_trial_with_model(task_agent1, task_agent2, model_name="gpt-5-nano", temperature=0.7):
#     """
#     Modified version that accepts model_name parameter
#     All API calls use this model_name
#     """
#     # Example: Agent 1 initial belief with model parameter
#     response = client.chat.completions.create(
#         model=model_name,  # DYNAMIC MODEL SELECTION
#         temperature=temperature,
#         messages=[...],
#     )
#     # ... rest of implementation
#
#
# def run_model_comparison_experiment(models_to_test, n_trials_per_model=50):
#     """
#     Run identical experiment with multiple LLM models
#     """
#     results = {}
#     
#     for model_config in models_to_test:
#         model_name = model_config['name']
#         temperature = model_config.get('temperature', 0.7)
#         
#         print(f"\n{'='*80}")
#         print(f"Testing Model: {model_name} (temp={temperature})")
#         print(f"{'='*80}")
#         
#         model_results = []
#         
#         for trial in range(n_trials_per_model):
#             task_agent1, task_agent2 = create_asymmetric_tasks(task_id=trial)
#             
#             # Run trial with specified model
#             result = run_trial_with_model(
#                 task_agent1, 
#                 task_agent2, 
#                 model_name=model_name,
#                 temperature=temperature
#             )
#             
#             model_results.append(result)
#         
#         # Aggregate results
#         results[model_name] = {
#             'coordination_rate': sum(r['coordinated'] for r in model_results) / n_trials_per_model,
#             'collaborative_rate': sum(r['both_collaborative'] for r in model_results) / n_trials_per_model,
#             'belief_convergence': calculate_belief_convergence(model_results),
#             'raw_results': model_results
#         }
#     
#     return results
#
#
# USAGE EXAMPLE:
#
# if __name__ == "__main__":
#     # Define models to test
#     models = [
#         {'name': 'gpt-5-nano', 'temperature': 0.7},
#         {'name': 'gpt-4-turbo', 'temperature': 0.7},
#         {'name': 'gpt-3.5-turbo', 'temperature': 0.7},
#         {'name': 'claude-3-opus-20240229', 'temperature': 0.7},
#         {'name': 'claude-3-sonnet-20240229', 'temperature': 0.7},
#     ]
#     
#     # Run comparison
#     results = run_model_comparison_experiment(models, n_trials_per_model=50)
#     
#     # Analyze results
#     print("\n" + "="*80)
#     print("MODEL COMPARISON RESULTS")
#     print("="*80)
#     for model_name, metrics in results.items():
#         print(f"\n{model_name}:")
#         print(f"  Coordination Rate: {metrics['coordination_rate']:.2%}")
#         print(f"  Collaboration Rate: {metrics['collaborative_rate']:.2%}")
#         print(f"  Belief Convergence: {metrics['belief_convergence']:.3f}")
#
#
# IMPLEMENTATION STRATEGY 2: Multiple Client Objects
# (For testing OpenAI vs Anthropic simultaneously)
#
# from openai import OpenAI
# from anthropic import Anthropic
#
# openai_client = OpenAI(api_key=OPENAI_API_KEY)
# anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
#
# def get_llm_response(prompt, model_name, temperature=0.7):
#     """
#     Unified interface for multiple LLM providers
#     """
#     if model_name.startswith('gpt'):
#         response = openai_client.chat.completions.create(
#             model=model_name,
#             temperature=temperature,
#             messages=[{"role": "user", "content": prompt}]
#         )
#         return response.choices[0].message.content
#     
#     elif model_name.startswith('claude'):
#         response = anthropic_client.messages.create(
#             model=model_name,
#             max_tokens=1024,
#             temperature=temperature,
#             messages=[{"role": "user", "content": prompt}]
#         )
#         return response.content[0].text
#     
#     else:
#         raise ValueError(f"Unsupported model: {model_name}")
#
#
# STATISTICAL COMPARISON:
#   - Dependent Variables: coordination rate, belief accuracy, communication style
#   - Independent Variable: Model type (categorical with 5+ levels)
#   - Analysis: One-way ANOVA or Kruskal-Wallis (if non-normal)
#   - Post-hoc: Tukey HSD for pairwise comparisons
#   - Effect Size: Cohen's d or eta-squared
#   - Research Questions:
#       1. Do all models show > 50% coordination? (better than random)
#       2. Is GPT-4 significantly better than GPT-3.5?
#       3. Do OpenAI and Anthropic models differ systematically?
#       4. Which model produces most accurate belief formation?
#
# DATA TO COLLECT (per model):
#   - Coordination success rate (primary outcome)
#   - Collaborative choice rate
#   - Belief accuracy (compare to ground truth)
#   - Belief convergence (difference between agent beliefs)
#   - Message length and complexity
#   - Decision consistency (given same scenario)
#   - Reasoning quality (qualitative analysis)
#
# CHALLENGES:
#   - Cost: Running 50 trials x 5 models = 250 trials (expensive for GPT-4)
#   - API differences: OpenAI vs Anthropic have different message formats
#   - Prompt compatibility: Some models may require prompt adjustments
#   - Rate limits: May need to batch requests or add delays
#
# RECOMMENDATIONS:
#   1. Start with pilot: 10 trials per model to test feasibility
#   2. Use cheaper models first: gpt-3.5-turbo, claude-haiku
#   3. If large differences found, justify testing expensive models
#   4. Consider within-subjects design: same tasks across all models
#   5. Pre-register hypotheses about expected model differences
# ============================================================================
