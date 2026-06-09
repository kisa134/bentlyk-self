import os
import importlib
import sys
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import json

class GrowthIntegrator:
    def __init__(self, tools_directory: str = "memory"):
        self.tools_directory = tools_directory
        self.tools = {}
        self.results = {}
        self.report = {
            "tool_execution": {},
            "conflicts": [],
            "gaps": [],
            "overlaps": [],
            "summary": {}
        }
        
    def discover_tools(self) -> List[str]:
        """Discover all available memory tools in the tools directory"""
        tools = []
        for filename in os.listdir(self.tools_directory):
            if filename.startswith("integration_") and filename.endswith(".py"):
                tools.append(filename[:-3])  # Remove .py extension
            elif filename.startswith("continuity_") and filename.endswith(".py"):
                tools.append(filename[:-3])
        return tools
    
    def load_tools(self) -> None:
        """Dynamically load all discovered tools"""
        tool_names = self.discover_tools()
        for tool_name in tool_names:
            try:
                module = importlib.import_module(f"memory.{tool_name}")
                self.tools[tool_name] = module
            except ImportError as e:
                self.report["tool_execution"][tool_name] = {
                    "status": "failed",
                    "error": str(e)
                }
    
    def run_tool(self, tool_name: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific tool with test data"""
        try:
            module = self.tools[tool_name]
            if hasattr(module, 'analyze'):
                result = module.analyze(test_data)
            elif hasattr(module, 'run'):
                result = module.run(test_data)
            elif hasattr(module, 'process'):
                result = module.process(test_data)
            else:
                # Try to call the module directly if it's callable
                result = module(test_data)
            
            return {
                "status": "success",
                "result": result
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def run_all_tools(self, test_data: Dict[str, Any]) -> None:
        """Run all loaded tools with provided test data"""
        for tool_name in self.tools:
            self.results[tool_name] = self.run_tool(tool_name, test_data)
            self.report["tool_execution"][tool_name] = self.results[tool_name]
    
    def check_consistency(self) -> None:
        """Check consistency between tool outputs"""
        successful_results = {
            name: data["result"] 
            for name, data in self.results.items() 
            if data["status"] == "success"
        }
        
        # Compare outputs for consistency
        tool_names = list(successful_results.keys())
        for i in range(len(tool_names)):
            for j in range(i + 1, len(tool_names)):
                tool_a, tool_b = tool_names[i], tool_names[j]
                result_a, result_b = successful_results[tool_a], successful_results[tool_b]
                
                # Check for direct contradictions
                conflict = self.detect_conflict(result_a, result_b)
                if conflict:
                    self.report["conflicts"].append({
                        "tools": [tool_a, tool_b],
                        "conflict": conflict
                    })
                
                # Check for overlaps
                overlap = self.detect_overlap(result_a, result_b)
                if overlap:
                    self.report["overlaps"].append({
                        "tools": [tool_a, tool_b],
                        "overlap": overlap
                    })
    
    def detect_conflict(self, result_a: Any, result_b: Any) -> str:
        """Detect conflicts between two tool results"""
        # This is a simplified conflict detection
        # In a real implementation, this would be more sophisticated
        if isinstance(result_a, dict) and isinstance(result_b, dict):
            for key in result_a:
                if key in result_b:
                    if result_a[key] != result_b[key]:
                        return f"Conflicting values for key '{key}': {result_a[key]} vs {result_b[key]}"
        return ""
    
    def detect_overlap(self, result_a: Any, result_b: Any) -> str:
        """Detect overlaps between two tool results"""
        # This is a simplified overlap detection
        if isinstance(result_a, dict) and isinstance(result_b, dict):
            common_keys = set(result_a.keys()) & set(result_b.keys())
            if common_keys:
                return f"Overlapping keys: {list(common_keys)}"
        return ""
    
    def identify_gaps(self) -> None:
        """Identify gaps in tool coverage"""
        successful_results = {
            name: data["result"] 
            for name, data in self.results.items() 
            if data["status"] == "success"
        }
        
        if not successful_results:
            self.report["gaps"].append("No tools executed successfully")
            return
            
        # Identify areas not covered by any tool
        all_keys = set()
        for result in successful_results.values():
            if isinstance(result, dict):
                all_keys.update(result.keys())
        
        # This is a simplified gap analysis
        # In practice, this would analyze the semantic meaning of the results
        if len(successful_results) < len(self.tools):
            failed_tools = [
                name for name, data in self.results.items() 
                if data["status"] == "failed"
            ]
            self.report["gaps"].append(f"Failed tools: {failed_tools}")
    
    def generate_summary(self) -> None:
        """Generate a summary of the integration results"""
        successful_count = sum(1 for data in self.results.values() if data["status"] == "success")
        failed_count = len(self.results) - successful_count
        
        self.report["summary"] = {
            "total_tools": len(self.tools),
            "successful_executions": successful_count,
            "failed_executions": failed_count,
            "conflicts_found": len(self.report["conflicts"]),
            "overlaps_found": len(self.report["overlaps"]),
            "gaps_identified": len(self.report["gaps"])
        }
    
    def generate_report(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main method to generate the integration report"""
        self.load_tools()
        self.run_all_tools(test_data)
        self.check_consistency()
        self.identify_gaps()
        self.generate_summary()
        
        return self.report
    
    def export_report(self, filename: str = "integration_report.json") -> None:
        """Export the report to a JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.report, f, indent=2)

# Example usage function
def run_integration_analysis(test_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to run the integration analysis"""
    integrator = GrowthIntegrator()
    return integrator.generate_report(test_data)

# Backward compatibility function
def main():
    """Main function for direct script execution"""
    # Example test data - in practice this would come from actual memory analysis
    test_data = {
        "memory_segments": ["segment_1", "segment_2"],
        "access_patterns": ["pattern_a", "pattern_b"],
        "growth_metrics": {"rate": 0.5, "threshold": 0.8}
    }
    
    integrator = GrowthIntegrator()
    report = integrator.generate_report(test_data)
    
    # Print summary
    print("Integration Report Summary:")
    print(f"Total Tools: {report['summary']['total_tools']}")
    print(f"Successful Executions: {report['summary']['successful_executions']}")
    print(f"Conflicts Found: {report['summary']['conflicts_found']}")
    print(f"Overlaps Found: {report['summary']['overlaps_found']}")
    print(f"Gaps Identified: {report['summary']['gaps_identified']}")
    
    return report

if __name__ == "__main__":
    main()