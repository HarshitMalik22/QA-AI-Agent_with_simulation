import pandas as pd
import os
from typing import Dict, Any, List
from .excel_logger import LOG_FILE_PATH

class InsightAggregator:
    """
    Aggregates insights from the interaction_logs.xlsx file.
    Provides stats per Agent and per City.
    """
    
    def __init__(self):
        self.log_file = LOG_FILE_PATH

    def _load_data(self) -> pd.DataFrame:
        if not os.path.exists(self.log_file):
            return pd.DataFrame()
        try:
            return pd.read_excel(self.log_file)
        except Exception as e:
            print(f"Error loading logs: {e}")
            return pd.DataFrame()

    def get_aggregated_stats(self) -> Dict[str, Any]:
        """
        Returns aggregated stats for dashboard.
        """
        df = self._load_data()
        if df.empty:
            return {
                "total_calls": 0,
                "risk_calls": 0,
                "avg_scores": {},
                "agent_performance": [],
                "city_trends": []
            }

        # Ensure required columns exist (fill if missing for backward compatibility)
        required_cols = ["Agent ID", "City", "Adherence Score", "Correctness Score", "Issue Detected", "Supervisor Flag"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = None 

        # 1. Overall Stats
        total_calls = len(df)
        risk_calls = len(df[df["Issue Detected"] == True])
        
        # 2. Agent Performance
        agent_stats = []
        if "Agent ID" in df.columns:
            agent_groups = df.groupby("Agent ID")
            for agent, group in agent_groups:
                agent_stats.append({
                    "agent_id": agent,
                    "calls": len(group),
                    "avg_adherence": round(group["Adherence Score"].mean(), 1) if not group["Adherence Score"].isnull().all() else 0,
                    "avg_correctness": round(group["Correctness Score"].mean(), 1) if not group["Correctness Score"].isnull().all() else 0,
                    "risk_rate": round((group["Issue Detected"] == True).mean() * 100, 1)
                })

        # 3. City Trends
        city_stats = []
        if "City" in df.columns:
            city_groups = df.groupby("City")
            for city, group in city_groups:
                city_stats.append({
                    "city": city,
                    "calls": len(group),
                    "top_issue": group["QA Reason"].mode()[0] if not group["QA Reason"].empty else "None",
                    "risk_rate": round((group["Issue Detected"] == True).mean() * 100, 1)
                })

        return {
            "total_calls": total_calls,
            "risk_calls": risk_calls,
            "agent_performance": agent_stats,
            "city_trends": city_stats
        }

    def get_supervisor_flags(self) -> List[Dict[str, Any]]:
        """
        Returns list of calls flagged for supervisor review.
        """
        df = self._load_data()
        if df.empty or "Supervisor Flag" not in df.columns:
            return []

        # Filter where Supervisor Flag is YES
        flagged_df = df[df["Supervisor Flag"] == "YES"].copy()
        
        # Replace NaN with safe defaults for JSON serialization
        flagged_df.fillna("", inplace=True)
        
        return flagged_df.to_dict(orient="records")
