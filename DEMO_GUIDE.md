# Demo Guide: QA-Driven Digital Twin

## Quick Start

### 1. Start Backend
```bash
cd backend
pip3 install -r requirements.txt
python3 -m uvicorn main:app --reload
```
Backend runs on `http://localhost:8000`

### 2. Start Frontend
```bash
cd frontend
npm install
npm start
```
Frontend runs on `http://localhost:3000`

## Demo Flow

### Scenario 1: Risky Station Routing (Call #1024)
**What to show:**
1. Click "Load Call #1024" - loads a transcript where agent routes to a busy station
2. Click "Analyze Call"
3. **Key Points:**
   - ✅ Auto-QA detects: "Agent routed driver to station with high load"
   - ✅ Shows original decision: Route to Station A (8.2 min wait, High congestion)
   - ✅ Shows alternative: Route to Station B (2.9 min wait, Low congestion)
   - ✅ Recommendation: Route to Station B - reduces wait time by 65%

**Why this matters:**
- Demonstrates counterfactual reasoning
- Quantifies operational impact (wait time reduction)
- Shows congestion risk mitigation

### Scenario 2: Delayed Escalation (Call #1025)
**What to show:**
1. Click "Load Call #1025"
2. Click "Analyze Call"
3. **Key Points:**
   - ✅ Auto-QA detects: "Agent delayed escalation"
   - ✅ Shows impact: Immediate escalation reduces wait time significantly
   - ✅ Demonstrates escalation timing decision intelligence

### Scenario 3: Vague Response (Call #1026)
**What to show:**
1. Click "Load Call #1026"
2. Click "Analyze Call"
3. **Key Points:**
   - ✅ Auto-QA detects: "Vague or incomplete instructions"
   - ✅ Shows alternative: Ask driver preference (clarifying approach)
   - ✅ Demonstrates response structure impact on repeat-call risk

### Scenario 4: Good Decision (Call #1027)
**What to show:**
1. Click "Load Call #1027"
2. Click "Analyze Call"
3. **Key Points:**
   - ✅ No issues detected
   - ✅ Shows system can identify good decisions too

## Key Talking Points

### 1. **Counterfactual Decision Intelligence**
- Not just detecting problems, but simulating alternatives
- Quantifying "what if" scenarios
- Operational impact measurement

### 2. **Micro Digital Twin**
- Simple, deterministic simulation
- Explainable results (no black box)
- Fast and credible

### 3. **Rule + Pattern-Based QA**
- Not pure LLM - uses deterministic rules first
- Confidence scores for transparency
- Fast detection without heavy compute

### 4. **Three Decision Types**
- **Station Routing**: Which station to send driver
- **Escalation Timing**: When to escalate
- **Response Structure**: How to communicate

### 5. **Three KPIs**
- **Expected Wait Time**: Minutes
- **Congestion Risk**: Low/Medium/High
- **Repeat-Call Probability**: Low/Medium/High

## Architecture Highlights

```
Call Transcript
   ↓
Auto-QA Analyzer (Rule-based + Pattern matching)
   ↓
Decision Extractor (Extracts actual decision)
   ↓
Micro Digital Twin (Deterministic simulation)
   ↓
Counterfactual Comparator (Generates 2-3 alternatives)
   ↓
Insight Generator (Human-readable output)
```

## Technical Decisions

1. **Deterministic Simulation**: No ML, fully explainable
2. **Mock Data**: Realistic but simplified for demo
3. **FastAPI Backend**: Fast, async, type-safe
4. **React Frontend**: Clean, demo-friendly UI
5. **Modular Design**: Each component is independent

## What Makes This Different

❌ **NOT** a generic Auto-QA system
✅ **IS** a counterfactual decision intelligence engine

❌ **NOT** a city-scale digital twin
✅ **IS** a micro-twin for decision-level simulation

❌ **NOT** autonomous decision-making
✅ **IS** decision support with quantified alternatives

## Questions Judges Might Ask

**Q: Is this realistic?**
A: Yes - uses real queue theory (M/M/1 approximation), Haversine distance, and operational KPIs that matter (wait time, congestion, repeat calls).

**Q: Why not use ML?**
A: Deterministic simulation is explainable, fast, and credible. For decision support, explainability > accuracy.

**Q: How does this scale?**
A: Micro-twin approach means each decision is simulated independently. Can parallelize across calls.

**Q: What's the business impact?**
A: Reduces wait times (customer satisfaction), prevents congestion (operational efficiency), reduces repeat calls (cost savings).

## Demo Tips

1. **Start with Call #1024** - clearest example of counterfactual reasoning
2. **Show the comparison table** - visual impact of alternatives
3. **Explain the simulation logic** - shows systems thinking
4. **Highlight the recommendation** - actionable insights
5. **Mention the 48-hour constraint** - shows prioritization

## Troubleshooting

**Backend won't start:**
- Check Python version: `python3 --version` (need 3.8+)
- Install dependencies: `pip3 install -r requirements.txt`

**Frontend won't start:**
- Check Node version: `node --version` (need 14+)
- Install dependencies: `npm install`

**API connection error:**
- Ensure backend is running on port 8000
- Check CORS settings in `main.py`
