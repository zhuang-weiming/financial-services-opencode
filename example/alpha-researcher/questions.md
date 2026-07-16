# Alpha-Researcher Agent — Example Questions

> **Routing trigger keywords:** alpha, alpha zoo, alpha family, factor bench, factor benchmark, IC/IR, alpha research, factor research

**Data Files:**
- `data/alpha101_bench.csv` — Alpha101 factor benchmark results
- `data/qlib158_summary.json` — Qlib158 alpha family summary

---

## Question 1: List all alpha families
```
List all alpha families available in the alpha zoo, with a brief description of each.

Reference: data/alpha101_bench.csv, data/qlib158_summary.json

From data/alpha101_bench.csv:
- 101 alphas across multiple families
- Performance metrics per alpha

From data/qlib158_summary.json:
- Qlib158: 158 quantitative research alphas
- Coverage: cross-sectional factor libraries

Please:
1) List all 5 alpha families with name and count
2) Describe the origin of each family
3) Note which markets each family is designed for
4) Suggest which family to start with for A-share vs US research
```

## Question 2: Bench the alpha101 family against CSI 300
```
Run a factor bench on the alpha101 family against the CSI 300 universe.

Reference: data/alpha101_bench.csv

Please:
1) Compute IC and IR for each of the 101 alphas
2) Rank top 20 by IC
3) Rank top 20 by IR
4) Show the distribution of IC values across the family
5) Flag alphas with unstable or negative IC
```

## Question 3: Compare IC/IR between alpha families
```
Compare IC/IR between the gtja191 and fundamental factor families to identify which has stronger predictive power.

Reference: data/alpha101_bench.csv, data/qlib158_summary.json

Please:
1) Compute mean IC and IR for each family
2) Show IC time-series stability comparison
3) Identify the top 5 alphas across all families by IR
4) Recommend which family is best suited for the current market regime
```
