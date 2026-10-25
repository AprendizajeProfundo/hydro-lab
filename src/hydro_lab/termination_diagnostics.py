"""Read-only episode termination statistics; denominator is all evaluated episodes."""
from collections import Counter


def summarize_terminations(rows):
    """Accept dict rows with terminated, termination_reason and steps."""
    rows = list(rows)
    total = len(rows)
    terminated = [r for r in rows if bool(r['terminated'])]
    counts = Counter(r.get('termination_reason') or 'UNSPECIFIED' for r in terminated)
    return {
        'n_episodes': total,
        'n_terminated': len(terminated),
        'termination_rate': len(terminated) / total if total else None,
        'termination_reason_counts': dict(sorted(counts.items())),
        'termination_reason_rates': {k: v / total for k, v in sorted(counts.items())} if total else {},
        'termination_reason_shares': {k: v / len(terminated) for k, v in sorted(counts.items())} if terminated else {},
        'mean_steps_to_termination': sum(int(r['steps']) for r in terminated) / len(terminated) if terminated else None,
    }
