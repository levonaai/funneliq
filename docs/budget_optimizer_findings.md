# Work Package 6: Budget Optimization Simulator Findings

Simulated monthly budget: 50,000, split across between 3 and 100 equal-sized campaigns - the range that keeps each campaign's budget within 500-20,000, the span actually observed in the historical data.

## Historical profit by budget level (why this isn't a smooth curve)

| Ad budget | Avg. cumulative profit |
|---|---|
| 500 | 1,130 |
| 800 | 1,338 |
| 1,000 | 2,261 |
| 1,500 | 3,298 |
| 2,000 | 21,749 |
| 2,500 | 22,013 |
| 3,000 | 21,980 |
| 4,000 | 21,477 |
| 5,000 | 21,725 |
| 6,000 | 5,171 |
| 7,000 | 5,309 |
| 8,000 | 5,492 |
| 10,000 | 5,107 |
| 12,000 | 5,018 |
| 15,000 | 5,247 |
| 20,000 | 4,762 |

Profit is not monotonic in budget: campaigns in the 2,000-5,000 range average roughly 4-10x the profit of campaigns budgeted either lower or higher. This lines up with Work Package 1's finding that conversion rate also peaks at the Medium budget tier - it's a real sweet spot, not noise.

## Strategy comparison

- **Most concentrated** (3 campaign(s) of 16,667 each): predicted total profit 15,257
- **Most spread** (100 campaigns of 500 each): predicted total profit 113,042
- **Optimal** (25 campaigns of 2,000 each): predicted total profit 543,719

## Bottom line

**Neither extreme wins.** Full concentration into a handful of large campaigns and maximal spread into many tiny campaigns both push the per-campaign budget outside the 2,000-5,000 sweet spot. The best strategy found here is a **moderate number of medium-sized campaigns** (2,000 each) - 430,677 more predicted profit than the better of the two extremes.
