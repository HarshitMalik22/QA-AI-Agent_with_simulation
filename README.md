# SmartDispatch AI - Network Optimization Engine
**From Reactive Support to Decision-Support Network Optimization**

A **Closed-Loop Decision Intelligence System** built for the Battery Smart Hackathon. It converts customer support from a cost center into a network balancing tool.

---

## 🚨 The "Invisible Queue" Problem

1.  **Driver Behavior:** E-rickshaw drivers often rush to the nearest well-known station (e.g., Tilak Nagar) when battery is low.
2.  **The Result:** A 30-minute queue at one station, while a station just 2km away (Rajouri Garden) sits empty.
3.  **The Gap:** Support agents often advise the nearest station based on distance, unintentionally worsening traffic jams.

**This leads to:**
*   📉 **Lost Driver Earnings:** (Time spent waiting = Money lost)
*   📉 **Inefficient Assets:** (Empty stations = Wasted CAPEX)

---

## 🎯 Our Solution: Counterfactual Decision Intelligence

We built a decision-intelligence system that evaluates and improves support decisions using counterfactual simulation.

1.  **Decide:** A voice agent captures driver intent and emits an initial routing decision.
2.  **Evaluate:** A deterministic micro-digital twin estimates downstream wait-time impact using queue theory.
3.  **Improve:** The system recommends a better alternative when the original decision increases congestion.

---

## 🏗 System Architecture

### 1. Frontend (The Interface)
*   **Voice AI:** Built with **Vapi.ai**, designed to speak natural Hinglish.
*   **Live Dashboard:** React-based UI showing call transcript and simulated station load visualization (Red/Green).

### 2. Backend (The Brain)
*   **Decision Emitter (`modules/decision_emitter.py`):** The "Source of Truth" that captures intent and proposes an initial decision.
*   **Auto-QA (`modules/auto_qa.py`):** A guardrail that flags risky decisions (e.g., routing to a >80% loaded station).
*   **Micro Digital Twin (`modules/digital_twin.py`):** A deterministic simulation engine (Physics + Queue Theory) that calculates exact wait times.
*   **Counterfactual Comparator (`modules/counterfactual.py`):** Runs parallel simulations ("What if?") to find the optimal station.

---

## 🚀 Key Features

*   ✅ **Closed-Loop Intelligence:** It generates recommended improvements to routing decisions after evaluation.
*   ✅ **Deterministic Simulation:** Deterministic simulation avoids LLM-based estimation.
*   ✅ **Operational KPIs:** Focuses on what matters: **Wait Time (mins)**, **Congestion Risk**, and **Repeat Calls**.
*   ✅ **Hinglish Support:** Optimized context prompts for Indian e-rickshaw drivers.

---

## ℹ️ Data Disclaimer

Station locations are sourced from Google Places (location metadata only). All operational signals such as load, wait time, and congestion are simulated for decision-logic demonstration.

---

## 🛠 Setup & Installation

### Prerequisites
*   Python 3.8+
*   Node.js 14+
*   Vapi Public Key (for Voice AI)

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
*API running at: `http://localhost:8000`*

### Frontend Setup
```bash
cd frontend
npm install
npm start
```
*App running at: `http://localhost:3000`*

---

## 🎮 How to Demo

1.  Open the Dashboard at `http://localhost:3000`.
2.  Click **"Start Voice Agent"**.
3.  **Scenario:** Act as a driver near "Dwarka Mor" asking for "Tilak Nagar".
4.  **Observe the Decision Improvement:**
    *   The Agent will hear you.
    *   The **Analysis Table** will pop up showing "Original Decision: 20 min wait".
    *   The system recommends a better option, which the agent can communicate.
    *   The Dashboard will quantify the impact: *"Saved 13 mins"*.

---

## 🏆 Business Impact

*   **For Drivers:** More time on the road = More daily earnings.
*   **For Battery Smart:** Higher asset utilization without marketing spend.
*   **For Operations:** Decision-support driven load balancing at scale.

---

*"Turning Customer Support into Operational Strategy."*
