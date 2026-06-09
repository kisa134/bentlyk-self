import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class GrowthTracker:
    def __init__(self, log_directory: str = "logs"):
        self.log_directory = Path(log_directory)
        self.metrics = {
            "introspection_intensity": 0.0,
            "energy_level": 0.0,
            "vulnerability_score": 0.0,
            "cognitive_load": 0.0,
            "emotional_volatility": 0.0
        }
        self.trends = {}
        self.flags = []
        
    def parse_logs(self) -> Dict[str, List[Dict]]:
        """Parse all available tracer logs"""
        parsed_logs = {
            "self_reflection": [],
            "energy_state": [],
            "vulnerability": [],
            "cognitive_load": [],
            "emotional_state": []
        }
        
        # Parse self reflection logs
        reflection_file = self.log_directory / "self_reflection_tracer.json"
        if reflection_file.exists():
            with open(reflection_file, 'r') as f:
                parsed_logs["self_reflection"] = json.load(f)
                
        # Parse energy state logs
        energy_file = self.log_directory / "energy_state_logger.json"
        if energy_file.exists():
            with open(energy_file, 'r') as f:
                parsed_logs["energy_state"] = json.load(f)
                
        # Parse vulnerability logs
        vuln_file = self.log_directory / "vulnerability_tracer.json"
        if vuln_file.exists():
            with open(vuln_file, 'r') as f:
                parsed_logs["vulnerability"] = json.load(f)
                
        # Parse cognitive load logs
        cognitive_file = self.log_directory / "cognitive_load_tracer.json"
        if cognitive_file.exists():
            with open(cognitive_file, 'r') as f:
                parsed_logs["cognitive_load"] = json.load(f)
                
        # Parse emotional state logs
        emotion_file = self.log_directory / "emotional_state_tracer.json"
        if emotion_file.exists():
            with open(emotion_file, 'r') as f:
                parsed_logs["emotional_state"] = json.load(f)
                
        return parsed_logs
    
    def calculate_metrics(self, logs: Dict[str, List[Dict]]) -> Dict[str, float]:
        """Calculate key growth metrics from parsed logs"""
        metrics = {}
        
        # Introspection intensity from self-reflection logs
        if logs["self_reflection"]:
            intensities = [log.get("depth_score", 0) for log in logs["self_reflection"]]
            metrics["introspection_intensity"] = sum(intensities) / len(intensities)
        else:
            metrics["introspection_intensity"] = 0.0
            
        # Energy level from energy state logs
        if logs["energy_state"]:
            energy_levels = [log.get("level", 0) for log in logs["energy_state"]]
            metrics["energy_level"] = sum(energy_levels) / len(energy_levels)
        else:
            metrics["energy_level"] = 0.0
            
        # Vulnerability score from vulnerability logs
        if logs["vulnerability"]:
            vuln_scores = [log.get("exposure_level", 0) for log in logs["vulnerability"]]
            metrics["vulnerability_score"] = sum(vuln_scores) / len(vuln_scores)
        else:
            metrics["vulnerability_score"] = 0.0
            
        # Cognitive load from cognitive load logs
        if logs["cognitive_load"]:
            load_scores = [log.get("load_value", 0) for log in logs["cognitive_load"]]
            metrics["cognitive_load"] = sum(load_scores) / len(load_scores)
        else:
            metrics["cognitive_load"] = 0.0
            
        # Emotional volatility from emotional state logs
        if logs["emotional_state"]:
            emotions = [log.get("intensity", 0) for log in logs["emotional_state"]]
            if len(emotions) > 1:
                volatility = sum(abs(emotions[i] - emotions[i-1]) for i in range(1, len(emotions))) / (len(emotions) - 1)
                metrics["emotional_volatility"] = volatility
            else:
                metrics["emotional_volatility"] = 0.0
        else:
            metrics["emotional_volatility"] = 0.0
            
        return metrics
    
    def identify_trends(self, logs: Dict[str, List[Dict]], metrics: Dict[str, float]) -> Dict[str, str]:
        """Identify key trends based on recent log patterns"""
        trends = {}
        
        # Trend for introspection
        if len(logs["self_reflection"]) >= 2:
            recent = logs["self_reflection"][-5:]  # Last 5 entries
            depths = [r.get("depth_score", 0) for r in recent]
            if len(depths) >= 2:
                if depths[-1] > depths[0]:
                    trends["introspection"] = "increasing"
                elif depths[-1] < depths[0]:
                    trends["introspection"] = "decreasing"
                else:
                    trends["introspection"] = "stable"
                    
        # Trend for energy
        if len(logs["energy_state"]) >= 2:
            recent = logs["energy_state"][-5:]
            energies = [e.get("level", 0) for e in recent]
            if len(energies) >= 2:
                if energies[-1] > energies[0]:
                    trends["energy"] = "increasing"
                elif energies[-1] < energies[0]:
                    trends["energy"] = "decreasing"
                else:
                    trends["energy"] = "stable"
                    
        # Trend for vulnerability
        if len(logs["vulnerability"]) >= 2:
            recent = logs["vulnerability"][-5:]
            vulns = [v.get("exposure_level", 0) for v in recent]
            if len(vulns) >= 2:
                if vulns[-1] > vulns[0]:
                    trends["vulnerability"] = "increasing"
                elif vulns[-1] < vulns[0]:
                    trends["vulnerability"] = "decreasing"
                else:
                    trends["vulnerability"] = "stable"
                    
        return trends
    
    def identify_flags(self, metrics: Dict[str, float], trends: Dict[str, str]) -> List[str]:
        """Identify potential issues or significant changes"""
        flags = []
        
        # High cognitive load flag
        if metrics["cognitive_load"] > 8.0:
            flags.append("HIGH_COGNITIVE_LOAD")
            
        # Low energy flag
        if metrics["energy_level"] < 3.0:
            flags.append("LOW_ENERGY")
            
        # High vulnerability flag
        if metrics["vulnerability_score"] > 7.0:
            flags.append("HIGH_VULNERABILITY")
            
        # Emotional instability flag
        if metrics["emotional_volatility"] > 5.0:
            flags.append("EMOTIONAL_INSTABILITY")
            
        # Rapidly decreasing introspection
        if trends.get("introspection") == "decreasing":
            flags.append("DECREASING_INTROSPECTION")
            
        return flags
    
    def generate_dashboard(self) -> Dict[str, Any]:
        """Generate structured JSON summary of growth state"""
        logs = self.parse_logs()
        self.metrics = self.calculate_metrics(logs)
        self.trends = self.identify_trends(logs, self.metrics)
        self.flags = self.identify_flags(self.metrics, self.trends)
        
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics,
            "trends": self.trends,
            "flags": self.flags,
            "summary": {
                "overall_health": self._calculate_overall_health(),
                "growth_indicators": self._get_growth_indicators(),
                "risk_factors": self._get_risk_factors()
            }
        }
        
        return dashboard
    
    def _calculate_overall_health(self) -> str:
        """Calculate overall health descriptor"""
        avg_metric = sum(self.metrics.values()) / len(self.metrics)
        if avg_metric >= 7.0:
            return "excellent"
        elif avg_metric >= 5.0:
            return "good"
        elif avg_metric >= 3.0:
            return "fair"
        else:
            return "poor"
    
    def _get_growth_indicators(self) -> List[str]:
        """Get positive growth indicators"""
        indicators = []
        if self.trends.get("introspection") == "increasing":
            indicators.append("deepening_self_awareness")
        if self.trends.get("energy") == "increasing":
            indicators.append("rising_vitality")
        if self.metrics["vulnerability_score"] > 5.0 and self.trends.get("vulnerability") == "increasing":
            indicators.append("authentic_openness")
        return indicators
    
    def _get_risk_factors(self) -> List[str]:
        """Get current risk factors"""
        risks = []
        if "HIGH_COGNITIVE_LOAD" in self.flags:
            risks.append("mental_exhaustion_risk")
        if "LOW_ENERGY" in self.flags:
            risks.append