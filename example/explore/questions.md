# Explore Agent Example Questions

**Data Files:**
- `data/architecture.json` - System architecture
- `data/code_analysis.csv` - Code file analysis

---

## Question 1: Repository Architecture
```
Explore the financial services monorepo structure.

Reference: data/architecture.json

From data/architecture.json:
- Pattern: Modular monorepo
- Layers: Presentation (React), Business Logic (Python/FastAPI), Data (PostgreSQL)
- Component Count: 145 React components, 23 services, 67 models

Key Files:
- pricing_service.py: 892 lines, high complexity
- portfolio_model.py: 445 lines, medium complexity
- order_api.py: 623 lines, high complexity

Please:
1) Map the architecture layers
2) Identify key entry points
3) Trace dependencies
4) Document integration points
```

---

## Question 2: Code Complexity Analysis
```
Analyze code complexity across the codebase.

Reference: data/code_analysis.csv

From data/code_analysis.csv:
- pricing_service.py: 892 lines, high complexity
- portfolio_model.py: 445 lines, medium complexity
- order_api.py: 623 lines, high complexity
- risk_calculator.py: 312 lines, medium complexity
- trade_executor.py: 567 lines, high complexity

Please:
1) Identify high-complexity files
2) Flag files needing refactoring
3) Map code ownership
4) Recommend test coverage priorities
```