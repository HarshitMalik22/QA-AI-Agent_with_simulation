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

    def get_agent_coaching_themes(self, agent_id: str = None) -> List[Dict[str, Any]]:
        """
        Returns coaching themes per agent based on recurring issues.
        If agent_id is provided, returns themes for that agent only.
        """
        df = self._load_data()
        if df.empty:
            return []

        # Ensure column exists
        if "QA Reason" not in df.columns or "Agent ID" not in df.columns:
            return []
        
        # Filter by agent if specified
        if agent_id:
            df = df[df["Agent ID"] == agent_id]
        
        # Group by agent and find most common issues
        results = []
        agent_groups = df.groupby("Agent ID")
        for agent, group in agent_groups:
            # Get top 3 recurring issues
            issues = group["QA Reason"].value_counts().head(3)
            if not issues.empty:
                results.append({
                    "agent_id": agent,
                    "total_calls": len(group),
                    "top_issues": [
                        {"issue": issue, "count": int(count), "pct": round(count/len(group)*100, 1)}
                        for issue, count in issues.items()
                    ],
                    "avg_score": round(group["Adherence Score"].mean(), 1) if "Adherence Score" in group.columns else 0,
                    "coaching_priority": "High" if group["Adherence Score"].mean() < 70 else "Medium" if group["Adherence Score"].mean() < 85 else "Low"
                })
        
        # Sort by coaching priority (High first)
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        results.sort(key=lambda x: priority_order.get(x["coaching_priority"], 3))
        
        return results

    def get_city_root_causes(self, city: str = None) -> List[Dict[str, Any]]:
        """
        Returns root causes and patterns per city.
        If city is provided, returns data for that city only.
        """
        df = self._load_data()
        if df.empty:
            return []

        # Ensure columns exist
        if "City" not in df.columns or "QA Reason" not in df.columns:
            return []
        
        # Filter by city if specified
        if city:
            df = df[df["City"] == city]
        
        results = []
        city_groups = df.groupby("City")
        for city_name, group in city_groups:
            # Get top issues for this city
            issues = group["QA Reason"].value_counts().head(5)
            risk_calls = len(group[group["Issue Detected"] == True])
            
            results.append({
                "city": city_name,
                "total_calls": len(group),
                "risk_calls": risk_calls,
                "risk_rate": round(risk_calls / len(group) * 100, 1) if len(group) > 0 else 0,
                "root_causes": [
                    {"cause": cause, "count": int(count)}
                    for cause, count in issues.items()
                ],
                "avg_score": round(group["Adherence Score"].mean(), 1) if "Adherence Score" in group.columns else 0,
                "attention_needed": risk_calls / len(group) > 0.2 if len(group) > 0 else False
            })
        
        # Sort by risk rate (highest first)
        results.sort(key=lambda x: x["risk_rate"], reverse=True)
        
        return results

