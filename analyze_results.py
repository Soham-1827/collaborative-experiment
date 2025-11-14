"""
Script to analyze experiment results and create visualizations
"""

import matplotlib.pyplot as plt
import re
from collections import defaultdict

def parse_results_file(filename):
    """Parse the results file and extract data"""
    results = []

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Extract fields using regex
                u_value_match = re.search(r'U_Value:([\d.]+)', line)
                agent1_strategy_match = re.search(r'Agent1_Strategy:(\w+)', line)
                agent2_strategy_match = re.search(r'Agent2_Strategy:(\w+)', line)
                mismatch_match = re.search(r'Mismatch:(\d+)', line)

                if all([u_value_match, agent1_strategy_match, agent2_strategy_match, mismatch_match]):
                    results.append({
                        'u_value': float(u_value_match.group(1)),
                        'agent1_strategy': agent1_strategy_match.group(1),
                        'agent2_strategy': agent2_strategy_match.group(1),
                        'mismatch': int(mismatch_match.group(1))
                    })

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found!")
        return []

    return results

def aggregate_by_u_value(results):
    """Aggregate results by u-value"""
    aggregated = defaultdict(lambda: {
        'total': 0,
        'mismatches': 0,
        'both_collaborative': 0,
        'both_individual': 0,
        'mixed': 0
    })

    for result in results:
        u_val = result['u_value']
        aggregated[u_val]['total'] += 1
        aggregated[u_val]['mismatches'] += result['mismatch']

        if result['agent1_strategy'] == 'collaborative' and result['agent2_strategy'] == 'collaborative':
            aggregated[u_val]['both_collaborative'] += 1
        elif result['agent1_strategy'] == 'individual' and result['agent2_strategy'] == 'individual':
            aggregated[u_val]['both_individual'] += 1
        else:
            aggregated[u_val]['mixed'] += 1

    return aggregated

def create_visualizations(aggregated_data):
    """Create visualization graphs"""
    if not aggregated_data:
        print("No data to visualize!")
        return

    # Sort u-values
    u_values = sorted(aggregated_data.keys())

    # Calculate percentages and counts
    mismatch_rates = []
    collaborative_rates = []
    individual_rates = []
    mixed_rates = []

    mismatch_counts = []
    collaborative_counts = []
    individual_counts = []
    mixed_counts = []

    for u_val in u_values:
        data = aggregated_data[u_val]
        total = data['total']

        # Percentages
        mismatch_rates.append((data['mismatches'] / total) * 100 if total > 0 else 0)
        collaborative_rates.append((data['both_collaborative'] / total) * 100 if total > 0 else 0)
        individual_rates.append((data['both_individual'] / total) * 100 if total > 0 else 0)
        mixed_rates.append((data['mixed'] / total) * 100 if total > 0 else 0)

        # Counts
        mismatch_counts.append(data['mismatches'])
        collaborative_counts.append(data['both_collaborative'])
        individual_counts.append(data['both_individual'])
        mixed_counts.append(data['mixed'])

    # Create figure with 4 subplots (2x2)
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Graph 1: Mismatch Rate vs U-Value
    ax1.plot(u_values, mismatch_rates, marker='o', linewidth=2, markersize=8, color='red')
    ax1.set_xlabel('U-Value (Collaboration Threshold)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Mismatch Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Strategy Mismatch Rate vs U-Value', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(-5, 105)

    # Add data labels
    for i, (u, rate) in enumerate(zip(u_values, mismatch_rates)):
        ax1.annotate(f'{rate:.1f}%', (u, rate), textcoords="offset points",
                    xytext=(0,10), ha='center', fontsize=9)

    # Graph 2: Strategy Distribution vs U-Value (Percentage)
    x_pos = range(len(u_values))
    width = 0.25

    ax2.bar([x - width for x in x_pos], collaborative_rates, width,
            label='Both Collaborative', color='green', alpha=0.8)
    ax2.bar(x_pos, individual_rates, width,
            label='Both Individual', color='blue', alpha=0.8)
    ax2.bar([x + width for x in x_pos], mixed_rates, width,
            label='Mixed (Mismatch)', color='red', alpha=0.8)

    ax2.set_xlabel('U-Value (Collaboration Threshold)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Strategy Choices vs U-Value (Percentage)', fontsize=14, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([f'{u:.2f}' for u in u_values])
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_ylim(0, 105)

    # Graph 3: Mismatch Frequency vs U-Value
    ax3.plot(u_values, mismatch_counts, marker='o', linewidth=2, markersize=8, color='red')
    ax3.set_xlabel('U-Value (Collaboration Threshold)', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Mismatch Count (Frequency)', fontsize=12, fontweight='bold')
    ax3.set_title('Strategy Mismatch Frequency vs U-Value', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)

    # Add data labels
    for i, (u, count) in enumerate(zip(u_values, mismatch_counts)):
        ax3.annotate(f'{count}', (u, count), textcoords="offset points",
                    xytext=(0,10), ha='center', fontsize=9)

    # Graph 4: Strategy Distribution vs U-Value (Frequency)
    ax4.bar([x - width for x in x_pos], collaborative_counts, width,
            label='Both Collaborative', color='green', alpha=0.8)
    ax4.bar(x_pos, individual_counts, width,
            label='Both Individual', color='blue', alpha=0.8)
    ax4.bar([x + width for x in x_pos], mixed_counts, width,
            label='Mixed (Mismatch)', color='red', alpha=0.8)

    ax4.set_xlabel('U-Value (Collaboration Threshold)', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Count (Frequency)', fontsize=12, fontweight='bold')
    ax4.set_title('Strategy Choices vs U-Value (Frequency)', fontsize=14, fontweight='bold')
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels([f'{u:.2f}' for u in u_values])
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    # Save the figure
    output_file = 'experiment_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nGraphs saved to: {output_file}")

    # Show the plot
    plt.show()

def print_summary(aggregated_data):
    """Print summary statistics"""
    print("\n" + "="*80)
    print("EXPERIMENT RESULTS SUMMARY")
    print("="*80)

    u_values = sorted(aggregated_data.keys())

    print(f"\n{'U-Value':<10} {'Total':<8} {'Mismatch':<12} {'Both Collab':<15} {'Both Indiv':<15} {'Mixed':<10}")
    print("-"*80)

    for u_val in u_values:
        data = aggregated_data[u_val]
        total = data['total']
        mismatch_pct = (data['mismatches'] / total * 100) if total > 0 else 0
        collab_pct = (data['both_collaborative'] / total * 100) if total > 0 else 0
        indiv_pct = (data['both_individual'] / total * 100) if total > 0 else 0
        mixed_pct = (data['mixed'] / total * 100) if total > 0 else 0

        print(f"{u_val:<10.2f} {total:<8} {mismatch_pct:<11.1f}% {collab_pct:<14.1f}% {indiv_pct:<14.1f}% {mixed_pct:<9.1f}%")

    print("="*80)

def main():
    """Main function"""
    # File to read
    results_file = "experiment_results_three_exchanges.txt"

    print("="*80)
    print("ANALYZING EXPERIMENT RESULTS")
    print("="*80)
    print(f"Reading from: {results_file}")

    # Parse results
    results = parse_results_file(results_file)

    if not results:
        print("No results found to analyze!")
        return

    print(f"Total experiments found: {len(results)}")

    # Aggregate by u-value
    aggregated = aggregate_by_u_value(results)

    print(f"Unique u-values: {sorted(aggregated.keys())}")

    # Print summary
    print_summary(aggregated)

    # Create visualizations
    print("\nGenerating visualizations...")
    create_visualizations(aggregated)

    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
