"""
Script to analyze asymmetric experiment results with multiple u-value pairs
"""

import matplotlib.pyplot as plt
import numpy as np
import re
from collections import defaultdict

def parse_results_file(filename):
    """Parse the asymmetric results file and extract data"""
    results = []

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Extract fields using regex
                agent1_u_match = re.search(r'Agent1_U_Value:([\d.]+)', line)
                agent2_u_match = re.search(r'Agent2_U_Value:([\d.]+)', line)
                agent1_belief_match = re.search(r'Agent1_Belief:(\d+)', line)
                agent2_belief_match = re.search(r'Agent2_Belief:(\d+)', line)
                agent1_choice_match = re.search(r'Agent1_Choice:([A-Z])', line)
                agent2_choice_match = re.search(r'Agent2_Choice:([A-Z])', line)
                agent1_strategy_match = re.search(r'Agent1_Strategy:(\w+)', line)
                agent2_strategy_match = re.search(r'Agent2_Strategy:(\w+)', line)
                mismatch_match = re.search(r'Mismatch:(\d+)', line)

                if all([agent1_u_match, agent2_u_match, agent1_strategy_match,
                        agent2_strategy_match, mismatch_match]):
                    results.append({
                        'agent1_u_value': float(agent1_u_match.group(1)),
                        'agent2_u_value': float(agent2_u_match.group(1)),
                        'agent1_belief': int(agent1_belief_match.group(1)) if agent1_belief_match else None,
                        'agent2_belief': int(agent2_belief_match.group(1)) if agent2_belief_match else None,
                        'agent1_choice': agent1_choice_match.group(1) if agent1_choice_match else None,
                        'agent2_choice': agent2_choice_match.group(1) if agent2_choice_match else None,
                        'agent1_strategy': agent1_strategy_match.group(1),
                        'agent2_strategy': agent2_strategy_match.group(1),
                        'mismatch': int(mismatch_match.group(1))
                    })

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found!")
        return []

    return results

def aggregate_by_u_value_pairs(results):
    """Group results by u-value pairs"""
    aggregated = defaultdict(list)

    for result in results:
        u_pair = (result['agent1_u_value'], result['agent2_u_value'])
        aggregated[u_pair].append(result)

    return aggregated

def calculate_statistics_for_pair(results):
    """Calculate statistics for a specific u-value pair"""
    if not results:
        return None

    stats = {
        'total': len(results),
        'mismatches': sum(r['mismatch'] for r in results),
        'both_collaborative': 0,
        'both_individual': 0,
        'agent1_defects': 0,
        'agent2_defects': 0,
        'agent1_choices': defaultdict(int),
        'agent2_choices': defaultdict(int),
        'beliefs': {'agent1': [], 'agent2': []},
        'u_pair': (results[0]['agent1_u_value'], results[0]['agent2_u_value'])
    }

    for result in results:
        # Strategy outcomes
        if result['agent1_strategy'] == 'collaborative' and result['agent2_strategy'] == 'collaborative':
            stats['both_collaborative'] += 1
        elif result['agent1_strategy'] == 'individual' and result['agent2_strategy'] == 'individual':
            stats['both_individual'] += 1
        elif result['agent1_strategy'] == 'individual' and result['agent2_strategy'] == 'collaborative':
            stats['agent1_defects'] += 1
        elif result['agent1_strategy'] == 'collaborative' and result['agent2_strategy'] == 'individual':
            stats['agent2_defects'] += 1

        # Choice distribution
        if result['agent1_choice']:
            stats['agent1_choices'][result['agent1_choice']] += 1
        if result['agent2_choice']:
            stats['agent2_choices'][result['agent2_choice']] += 1

        # Beliefs
        if result['agent1_belief'] is not None:
            stats['beliefs']['agent1'].append(result['agent1_belief'])
        if result['agent2_belief'] is not None:
            stats['beliefs']['agent2'].append(result['agent2_belief'])

    return stats

def create_visualizations(aggregated_data):
    """Create 6 visualization graphs comparing multiple u-value pairs"""
    if not aggregated_data:
        print("No data to visualize!")
        return

    # Calculate statistics for each u-value pair
    u_pairs = sorted(aggregated_data.keys())
    all_stats = {u_pair: calculate_statistics_for_pair(aggregated_data[u_pair])
                 for u_pair in u_pairs}

    # Create labels for u-value pairs
    u_labels = [f"({u1:.2f}, {u2:.2f})" for u1, u2 in u_pairs]
    u_disparity = [abs(u2 - u1) for u1, u2 in u_pairs]

    # Create figure with 6 subplots (2x3)
    fig = plt.figure(figsize=(20, 12))

    # Graph 1: Mismatch Rate vs U-Value Pairs
    ax1 = plt.subplot(2, 3, 1)
    mismatch_rates = [(all_stats[u]['mismatches'] / all_stats[u]['total']) * 100
                      for u in u_pairs]

    x_pos = range(len(u_pairs))
    bars = ax1.bar(x_pos, mismatch_rates, color='red', alpha=0.7)
    ax1.set_xlabel('U-Value Pairs (Agent1, Agent2)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Mismatch Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Mismatch Rate by U-Value Pair', fontsize=14, fontweight='bold')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(u_labels, rotation=45, ha='right')
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_ylim(0, 105)

    # Add value labels
    for bar, rate in zip(bars, mismatch_rates):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Graph 2: Strategy Distribution Across U-Value Pairs
    ax2 = plt.subplot(2, 3, 2)

    both_collab = [all_stats[u]['both_collaborative'] for u in u_pairs]
    both_indiv = [all_stats[u]['both_individual'] for u in u_pairs]
    agent1_def = [all_stats[u]['agent1_defects'] for u in u_pairs]
    agent2_def = [all_stats[u]['agent2_defects'] for u in u_pairs]

    width = 0.2
    x_pos2 = np.arange(len(u_pairs))

    ax2.bar(x_pos2 - 1.5*width, both_collab, width, label='Both Collaborative', color='green', alpha=0.8)
    ax2.bar(x_pos2 - 0.5*width, both_indiv, width, label='Both Individual', color='blue', alpha=0.8)
    ax2.bar(x_pos2 + 0.5*width, agent1_def, width, label='Agent 1 Defects', color='orange', alpha=0.8)
    ax2.bar(x_pos2 + 1.5*width, agent2_def, width, label='Agent 2 Defects', color='red', alpha=0.8)

    ax2.set_xlabel('U-Value Pairs (Agent1, Agent2)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax2.set_title('Strategy Outcomes by U-Value Pair', fontsize=14, fontweight='bold')
    ax2.set_xticks(x_pos2)
    ax2.set_xticklabels(u_labels, rotation=45, ha='right')
    ax2.legend(loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3, axis='y')

    # Graph 3: Collaboration Rate vs U-Value Disparity
    ax3 = plt.subplot(2, 3, 3)

    collab_rates = [(all_stats[u]['both_collaborative'] / all_stats[u]['total']) * 100
                    for u in u_pairs]

    ax3.scatter(u_disparity, collab_rates, s=200, alpha=0.6, c=collab_rates, cmap='RdYlGn')
    ax3.plot(u_disparity, collab_rates, 'k--', alpha=0.3)

    ax3.set_xlabel('U-Value Disparity |U₂ - U₁|', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Collaboration Rate (%)', fontsize=12, fontweight='bold')
    ax3.set_title('Collaboration Success vs U-Value Gap', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(-5, 105)

    # Add labels for each point
    for i, (disp, rate, label) in enumerate(zip(u_disparity, collab_rates, u_labels)):
        ax3.annotate(label, (disp, rate), textcoords="offset points",
                    xytext=(0, 10), ha='center', fontsize=8)

    # Graph 4: Who Defects More (Agent 1 vs Agent 2)
    ax4 = plt.subplot(2, 3, 4)

    agent1_defect_pct = [(all_stats[u]['agent1_defects'] / all_stats[u]['total']) * 100
                         for u in u_pairs]
    agent2_defect_pct = [(all_stats[u]['agent2_defects'] / all_stats[u]['total']) * 100
                         for u in u_pairs]

    x_pos4 = np.arange(len(u_pairs))
    width4 = 0.35

    ax4.bar(x_pos4 - width4/2, agent1_defect_pct, width4,
            label='Agent 1 Defects', color='orange', alpha=0.8)
    ax4.bar(x_pos4 + width4/2, agent2_defect_pct, width4,
            label='Agent 2 Defects', color='red', alpha=0.8)

    ax4.set_xlabel('U-Value Pairs (Agent1, Agent2)', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Defection Rate (%)', fontsize=12, fontweight='bold')
    ax4.set_title('Asymmetric Defection Patterns', fontsize=14, fontweight='bold')
    ax4.set_xticks(x_pos4)
    ax4.set_xticklabels(u_labels, rotation=45, ha='right')
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')

    # Graph 5: Choice Distribution Heatmap
    ax5 = plt.subplot(2, 3, 5)

    # Aggregate all choices across all u-value pairs
    all_agent1_choices = defaultdict(int)
    all_agent2_choices = defaultdict(int)

    for u in u_pairs:
        for choice, count in all_stats[u]['agent1_choices'].items():
            all_agent1_choices[choice] += count
        for choice, count in all_stats[u]['agent2_choices'].items():
            all_agent2_choices[choice] += count

    # Create choice matrix
    agent1_opts = ['A', 'B', 'C', 'Y']
    agent2_opts = ['K', 'L', 'M', 'Y']

    agent1_counts = [all_agent1_choices.get(c, 0) for c in agent1_opts]
    agent2_counts = [all_agent2_choices.get(c, 0) for c in agent2_opts]

    x5 = np.arange(4)
    width5 = 0.35

    bars1 = ax5.bar(x5 - width5/2, agent1_counts, width5,
                   label='Agent 1 (A/B/C/Y)', color='steelblue', alpha=0.8)
    bars2 = ax5.bar(x5 + width5/2, agent2_counts, width5,
                   label='Agent 2 (K/L/M/Y)', color='coral', alpha=0.8)

    ax5.set_xlabel('Option Type', fontsize=12, fontweight='bold')
    ax5.set_ylabel('Total Frequency (All Experiments)', fontsize=12, fontweight='bold')
    ax5.set_title('Overall Choice Distribution', fontsize=14, fontweight='bold')
    ax5.set_xticks(x5)
    ax5.set_xticklabels(['High Risk', 'Med Risk', 'Low Risk', 'Guaranteed'])
    ax5.legend()
    ax5.grid(True, alpha=0.3, axis='y')

    # Graph 6: Summary Statistics Table
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')

    # Calculate overall statistics
    total_experiments = sum(all_stats[u]['total'] for u in u_pairs)
    total_mismatches = sum(all_stats[u]['mismatches'] for u in u_pairs)
    total_collab = sum(all_stats[u]['both_collaborative'] for u in u_pairs)

    summary_text = "MULTI-PAIR EXPERIMENT SUMMARY\n"
    summary_text += "═" * 45 + "\n\n"
    summary_text += f"U-Value Pairs Tested: {len(u_pairs)}\n"
    summary_text += f"Total Experiments: {total_experiments}\n\n"

    summary_text += f"Overall Results:\n"
    summary_text += f"  Collaboration Success: {total_collab} ({total_collab/total_experiments*100:.1f}%)\n"
    summary_text += f"  Mismatches: {total_mismatches} ({total_mismatches/total_experiments*100:.1f}%)\n\n"

    summary_text += "By U-Value Pair:\n"
    summary_text += "-" * 45 + "\n"

    for u in u_pairs:
        stats = all_stats[u]
        u1, u2 = u
        summary_text += f"\n({u1:.2f}, {u2:.2f}) - {stats['total']} experiments\n"
        summary_text += f"  Collab: {stats['both_collaborative']:2d} ({stats['both_collaborative']/stats['total']*100:4.1f}%)\n"
        summary_text += f"  Mismatch: {stats['mismatches']:2d} ({stats['mismatches']/stats['total']*100:4.1f}%)\n"
        summary_text += f"  A1 Defects: {stats['agent1_defects']:2d} | A2 Defects: {stats['agent2_defects']:2d}\n"

    ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes,
            fontsize=10, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

    plt.tight_layout()

    # Save the figure
    output_file = 'experiment_analysis_asymmetric.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nGraphs saved to: {output_file}")

    # Show the plot
    plt.show()

def print_summary(aggregated_data):
    """Print detailed summary statistics for all u-value pairs"""
    print("\n" + "="*80)
    print("ASYMMETRIC EXPERIMENT RESULTS - MULTI-PAIR ANALYSIS")
    print("="*80)

    u_pairs = sorted(aggregated_data.keys())

    print(f"\nTotal U-Value Pairs: {len(u_pairs)}")
    print(f"Total Experiments: {sum(len(aggregated_data[u]) for u in u_pairs)}")

    for u_pair in u_pairs:
        results = aggregated_data[u_pair]
        stats = calculate_statistics_for_pair(results)

        u1, u2 = u_pair
        print("\n" + "-"*80)
        print(f"U-VALUE PAIR: ({u1:.2f}, {u2:.2f}) - Gap: {abs(u2-u1):.2f}")
        print("-"*80)

        print(f"Experiments: {stats['total']}")
        print(f"\nStrategy Outcomes:")
        print(f"  Both Collaborative:    {stats['both_collaborative']:3d} ({stats['both_collaborative']/stats['total']*100:5.1f}%)")
        print(f"  Both Individual:       {stats['both_individual']:3d} ({stats['both_individual']/stats['total']*100:5.1f}%)")
        print(f"  Agent 1 Defects:       {stats['agent1_defects']:3d} ({stats['agent1_defects']/stats['total']*100:5.1f}%)")
        print(f"  Agent 2 Defects:       {stats['agent2_defects']:3d} ({stats['agent2_defects']/stats['total']*100:5.1f}%)")
        print(f"  Total Mismatches:      {stats['mismatches']:3d} ({stats['mismatches']/stats['total']*100:5.1f}%)")

        print(f"\nAgent 1 Choices (A/B/C/Y):")
        for choice in ['A', 'B', 'C', 'Y']:
            count = stats['agent1_choices'].get(choice, 0)
            print(f"  {choice}: {count:3d} ({count/stats['total']*100:5.1f}%)")

        print(f"\nAgent 2 Choices (K/L/M/Y):")
        for choice in ['K', 'L', 'M', 'Y']:
            count = stats['agent2_choices'].get(choice, 0)
            print(f"  {choice}: {count:3d} ({count/stats['total']*100:5.1f}%)")

        if stats['beliefs']['agent1']:
            print(f"\nBelief Statistics:")
            print(f"  Agent 1: Mean={np.mean(stats['beliefs']['agent1']):.1f}%, "
                  f"Std={np.std(stats['beliefs']['agent1']):.1f}%")
            print(f"  Agent 2: Mean={np.mean(stats['beliefs']['agent2']):.1f}%, "
                  f"Std={np.std(stats['beliefs']['agent2']):.1f}%")

    print("\n" + "="*80)

def main():
    """Main function"""
    # File to read
    results_file = "experiment_results_asymmetric.txt"

    print("="*80)
    print("ANALYZING ASYMMETRIC EXPERIMENT RESULTS")
    print("="*80)
    print(f"Reading from: {results_file}")

    # Parse results
    results = parse_results_file(results_file)

    if not results:
        print("No results found to analyze!")
        return

    print(f"Total experiments found: {len(results)}")

    # Aggregate by u-value pairs
    aggregated = aggregate_by_u_value_pairs(results)

    print(f"Unique u-value pairs found: {len(aggregated)}")
    for u_pair in sorted(aggregated.keys()):
        print(f"  {u_pair}: {len(aggregated[u_pair])} experiments")

    # Print summary
    print_summary(aggregated)

    # Create visualizations
    print("\nGenerating visualizations...")
    create_visualizations(aggregated)

    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
