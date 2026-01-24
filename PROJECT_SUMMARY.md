# QA-Driven Digital Twin - Project Summary

## What We Built

A **counterfactual decision intelligence engine** that analyzes customer support calls and simulates alternative agent decisions to quantify operational impact.

## Core Innovation

**Micro Digital Twin** for decision-level counterfactual simulation, not city-scale modeling.

## System Architecture

```
┌─────────────────┐
│ Call Transcript │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Auto-QA        │  ← Rule + Pattern-based detection
│  Analyzer       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Decision       │  ← Extracts actual decision
│  Extractor      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Micro Digital  │  ← Deterministic simulation
│  Twin           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Counterfactual │  ← Generates 2-3 alternatives
│  Comparator     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Insight        │  ← Human-readable output
│  Generator      │
└─────────────────┘
```

## Key Components

### 1. Auto-QA Analyzer (`modules/auto_qa.py`)
- **Rule-based detection** of suboptimal decisions
- Detects: SOP deviation, risky routing, late escalation, incomplete explanation
- Returns confidence scores

### 2. Decision Extractor (`modules/decision_extractor.py`)
- Extracts actual agent decision from transcript
- Supports: Station Routing, Escalation Timing, Response Structure

### 3. Micro Digital Twin (`modules/digital_twin.py`)
- **Deterministic simulation** (no ML)
- Models: Station capacity, load, service time, distance
- Calculates: Wait time (queue theory), congestion risk, repeat-call probability

### 4. Counterfactual Comparator (`modules/counterfactual.py`)
- Generates 2-3 alternative decisions
- Simulates each alternative
- Compares outcomes and ranks best option

### 5. Insight Generator (`modules/insight_generator.py`)
- Creates human-readable insights
- Quantifies impact (wait time reduction %, risk improvements)
- Demo-friendly formatted output

## Decision Types (Locked)

1. **Station Routing**: Which station to send driver
2. **Escalation Timing**: Escalate now vs later vs not at all
3. **Response Structure**: Direct instruction vs clarifying preference

## KPIs (Locked)

1. **Expected Wait Time**: Minutes (calculated from queue + travel)
2. **Congestion Risk**: Low / Medium / High (based on load/capacity ratio)
3. **Repeat-Call Probability**: Low / Medium / High (based on wait + mismatch)

## Technical Stack

- **Backend**: Python 3.8+, FastAPI, Pydantic
- **Frontend**: React 18, Axios
- **Simulation**: Deterministic (queue theory, Haversine distance)
- **Data**: Mock JSON (realistic but simplified)

## File Structure

```
BatterySmart/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── requirements.txt
│   ├── modules/
│   │   ├── auto_qa.py
│   │   ├── decision_extractor.py
│   │   ├── digital_twin.py
│   │   ├── counterfactual.py
│   │   └── insight_generator.py
│   ├── data/
│   │   └── mock_data.py        # Stations + transcripts
│   └── test_modules.py
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── App.css
│   │   └── index.js
│   └── package.json
├── README.md
├── DEMO_GUIDE.md
└── PROJECT_SUMMARY.md
```

## Key Design Decisions

1. **Deterministic over ML**: Explainable, fast, credible
2. **Micro-twin over city-twin**: Decision-level, not system-level
3. **Rule-based QA**: Fast detection, transparent logic
4. **Mock data**: Realistic but simplified for demo
5. **Modular architecture**: Each component is independent

## What Makes This Different

✅ **Counterfactual reasoning**: Not just detecting problems, but simulating alternatives
✅ **Quantified impact**: Wait time reduction %, risk improvements
✅ **Explainable**: Deterministic simulation, no black box
✅ **Operational focus**: KPIs that matter (wait time, congestion, repeat calls)
✅ **Demo-ready**: Clean UI, sample data, working prototype

## Business Impact

- **Reduces wait times**: Better routing decisions
- **Prevents congestion**: Load balancing across stations
- **Reduces repeat calls**: Better communication and escalation
- **Cost savings**: Fewer support escalations, better resource utilization

## Evaluation Criteria Met

✅ **Systems thinking**: Modular architecture, clear data flow
✅ **Counterfactual reasoning**: Simulates alternatives, compares outcomes
✅ **Ops awareness**: Real operational KPIs (wait time, congestion, repeat calls)
✅ **Safe AI design**: Deterministic, explainable, no autonomous decisions
✅ **Business impact clarity**: Quantified improvements, actionable recommendations

## Next Steps (If Extending)

1. Add more sophisticated queue models (M/M/c, priority queues)
2. Integrate real-time station data
3. Add historical decision learning
4. Expand to more decision types
5. Add agent training recommendations

## Constraints Respected

✅ Only 3 decision types (Station Routing, Escalation, Response)
✅ Only 3 KPIs (Wait Time, Congestion Risk, Repeat-Call Risk)
✅ Micro-twin (not city-scale)
✅ Deterministic simulation (no ML)
✅ Mock data (realistic but simplified)
✅ 48-hour MVP scope
