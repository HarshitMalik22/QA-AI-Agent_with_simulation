"""
Insight Generator Module

Generates human-readable insights from analysis results.
"""

from typing import Dict, Any, List
class InsightGenerator:
    """
    Generates demo-friendly, human-readable insights.
    """
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service

    def generate(self, qa_result: Dict[str, Any], 
                actual_decision: Dict[str, Any],
                alternatives: List[Dict[str, Any]],
                call_id: str,
                transcript: str = "") -> Dict[str, Any]:
        """
        Generate insights from the analysis.
        
        Returns:
            {
                "issue_summary": str,
                "recommendation": str,
                "impact_summary": str,
                "formatted_output": str
            }
        """
        if not qa_result.get("issue_detected"):
            return {
                "issue_summary": "No issues detected in this call",
                "call_summary": qa_result.get("call_summary", "Agent handled the call professionally and resolved the driver's query."),
                "improvement_explanation": qa_result.get("improvement_explanation", "No specific improvements needed. Keep up the good work!"),
                "simulation_narrative": "No alternative simulation required. The original decision was already optimal.",
                "recommendation": "Current decision appears optimal",
                "impact_summary": "No significant improvements identified",
                "formatted_output": self._format_no_issue(call_id, qa_result)
            }
        
        # Find actual and best alternative
        actual = next((alt for alt in alternatives if alt.get("is_actual")), None)
        best = next((alt for alt in alternatives if not alt.get("is_actual")), None)
        
        if not actual or not best:
            return {
                "issue_summary": qa_result.get("reason", "Issue detected"),
                "call_summary": qa_result.get("call_summary", "Call details could not be fully analyzed."),
                "improvement_explanation": qa_result.get("improvement_explanation", "Review the transcript for context."),
                "simulation_narrative": "Simulation data unavailable for this scenario.",
                "recommendation": "Review decision",
                "impact_summary": "Unable to quantify impact",
                "formatted_output": self._format_basic(call_id, qa_result)
            }
        
        # Generate insights
        issue_summary = qa_result.get("reason", "Suboptimal decision detected")
        decision_type = qa_result.get("decision_type", "unknown")
        
        # New Narrative Fields from LLM
        call_summary = qa_result.get("call_summary", "Detailed call summary not available.")
        improvement_explanation = qa_result.get("improvement_explanation", "No specific improvement feedback generated.")
        
        # Recommendation
        recommendation = self._generate_recommendation(best, decision_type)
        
        # Impact summary
        improvement = best.get("improvement", {})
        impact_summary = self._generate_impact_summary(actual, best, improvement)
        
        # Simulation Narrative (Why is the alternative better?)
        simulation_narrative = self._generate_simulation_narrative(actual, best, improvement)
        
        # LLM Coaching (Override static impact summary if LLM available)
        if self.llm_service and self.llm_service.client:
             impact_summary = self.llm_service.generate_coaching(
                 transcript, actual, best
             )
        
        # Formatted output
        formatted_output = self._format_insights(
            call_id,
            issue_summary,
            decision_type,
            actual,
            alternatives,
            best,
            improvement,
            qa_result
        )
        
        return {
            "issue_summary": issue_summary,
            "call_summary": call_summary,
            "improvement_explanation": improvement_explanation,
            "simulation_narrative": simulation_narrative,
            "recommendation": recommendation,
            "impact_summary": impact_summary,
            "formatted_output": formatted_output
        }
    
    def _generate_simulation_narrative(self, actual: Dict[str, Any], best: Dict[str, Any], improvement: Dict[str, Any]) -> str:
        """Generate a narrative explaining the simulation result"""
        wait_reduction = improvement.get("wait_time_reduction", 0)
        
        if actual.get("decision_type") == "station_routing":
             return f"The Digital Twin simulation reveals that {best.get('option')} was a better choice because it currently has {best.get('expected_wait_time', 0)} mins wait time compared to {actual.get('expected_wait_time', 0)} mins at the original choice. This would have saved the driver approx {wait_reduction} minutes."
        
        elif actual.get("decision_type") == "information_providing":
             return "Simulated scenario shows that strictly following the authentication protocol (checking ID first) prevents potential fraud and aligns with SOPs, even if it adds a few seconds to the call."
             
        return f"Simulation indicates that '{best.get('option')}' yields better outcomes, specifically improving {', '.join([k for k, v in improvement.items() if v])}."
    
    def _generate_recommendation(self, best_option: Dict[str, Any], 
                                decision_type: str) -> str:
        """Generate recommendation text"""
        option_name = best_option.get("option", "Alternative option")
        
        if decision_type == "station_routing":
            station_id = best_option.get("station_id", "")
            return f"Route to Station {station_id}"
        elif decision_type == "escalation_timing":
            return "Escalate immediately to supervisor"
        elif decision_type == "response_structure":
            return "Ask driver preference before routing"
        elif decision_type == "information_providing":
            return "Provide clear, concise information (No routing needed)"
        else:
            return option_name
    
    def _generate_impact_summary(self, actual: Dict[str, Any], 
                                best: Dict[str, Any],
                                improvement: Dict[str, Any]) -> str:
        """Generate impact summary"""
        parts = []
        
        wait_reduction = improvement.get("wait_time_reduction_pct", 0)
        if wait_reduction > 0:
            parts.append(f"reduce wait time by {wait_reduction:.0f}%")
        
        if improvement.get("congestion_improved"):
            parts.append("lower congestion risk")
        
        if improvement.get("repeat_call_improved"):
            parts.append("lower repeat-call risk")
        
        if parts:
            return f"This would likely {', '.join(parts)}."
        else:
            return "This would likely improve overall outcomes."
    
    def _format_insights(self, call_id: str, issue_summary: str, 
                        decision_type: str, actual: Dict[str, Any],
                        alternatives: List[Dict[str, Any]],
                        best: Dict[str, Any],
                        improvement: Dict[str, Any],
                        qa_result: Dict[str, Any]) -> str:
        """Format insights as demo-friendly text"""
        output = []
        output.append("🚨 QA Insight Detected\n")
        
        # Add Supervisor Flag if present
        if qa_result.get("supervisor_flag"):
            output.append("🚩 **SUPERVISOR REVIEW REQUIRED**\n")
            
        output.append(f"Issue: {issue_summary}")
        
        # Add Scorecard
        scorecard = qa_result.get("scorecard", {})
        if scorecard:
            output.append(f"\n📊 Scorecard:")
            output.append(f"• Adherence: {scorecard.get('adherence_score', 'N/A')}/100")
            output.append(f"• Correctness: {scorecard.get('correctness_score', 'N/A')}/100")
            output.append(f"• Sentiment: {scorecard.get('sentiment_label', 'N/A')}")
            output.append(f"• Coaching Theme: {qa_result.get('coaching_theme', 'N/A')}\n")
            
        output.append(f"Call ID: #{call_id}\n")
        output.append("🔁 Simulated Alternatives\n")
        output.append("Option\tWait Time\tCongestion\tRepeat Call")
        output.append("-" * 60)
        
        for alt in alternatives:
            is_actual = alt.get("is_actual", False)
            prefix = "Original" if is_actual else "Alternative"
            option = alt.get("option", "Unknown")
            wait = alt.get("expected_wait_time", 0)
            congestion = alt.get("congestion_risk", "Low")
            repeat = alt.get("repeat_call_risk", "Low")
            
            output.append(f"{prefix} ({option})\t{wait} min\t{congestion}\t{repeat}")
        
        output.append("\n✅ Recommended Action\n")
        output.append(self._generate_recommendation(best, decision_type))
        output.append("\n" + self._generate_impact_summary(actual, best, improvement))
        
        return "\n".join(output)
    
    def _format_no_issue(self, call_id: str, qa_result: Dict[str, Any]) -> str:
        """Format output when no issue detected"""
        output = []
        output.append("✅ No Issues Detected - Optimal Execution\n")
        output.append(f"Call ID: #{call_id}\n")
        
        # Add Scorecard
        scorecard = qa_result.get("scorecard", {})
        if scorecard:
            output.append(f"📊 Scorecard details:")
            output.append(f"• Total Score: {scorecard.get('total_score', 'N/A')}/100")
            output.append(f"• Authentication: {scorecard.get('authentication_score', 'N/A')}/30")
            output.append(f"• Solution: {scorecard.get('solution_score', 'N/A')}/40")
            output.append(f"• Greeting: {scorecard.get('greeting_score', 'N/A')}/10")
            output.append(f"• Closing: {scorecard.get('closing_score', 'N/A')}/20")
            output.append(f"• Sentiment: {scorecard.get('sentiment_label', 'N/A')}\n")
            
        output.append("No suboptimal decisions detected in this call.")
        return "\n".join(output)    
    def _format_basic(self, call_id: str, qa_result: Dict[str, Any]) -> str:
        """Format basic output"""
        return f"🚨 QA Insight Detected\n\nIssue: {qa_result.get('reason', 'Issue detected')}\nCall ID: #{call_id}"
