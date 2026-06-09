import logging
import traceback
import json
import time
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class LanguageMode(Enum):
    RUSSIAN = "russian"
    ENGLISH = "english"

@dataclass
class DivergenceRecord:
    timestamp: str
    language_mode: LanguageMode
    stack_trace: List[str]
    fracture_point: str
    context_data: Dict[str, Any]
    coherence_impact: float  # 0.0 to 1.0 scale

class UnifiedRuntimeValidator:
    def __init__(self, log_file: str = "divergence_log.json"):
        self.log_file = log_file
        self.divergence_records: List[DivergenceRecord] = []
        self.fracture_counter = Counter()
        self._setup_logging()
        
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('runtime_validation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def capture_divergence(self, language_mode: LanguageMode, 
                          context_data: Dict[str, Any] = None,
                          coherence_impact: float = 0.5) -> None:
        """Capture full stack trace during semantic divergence"""
        stack_trace = traceback.format_stack()
        timestamp = datetime.now().isoformat()
        
        # Extract fracture point (last significant frame)
        fracture_point = self._extract_fracture_point(stack_trace)
        
        record = DivergenceRecord(
            timestamp=timestamp,
            language_mode=language_mode,
            stack_trace=stack_trace,
            fracture_point=fracture_point,
            context_data=context_data or {},
            coherence_impact=coherence_impact
        )
        
        self.divergence_records.append(record)
        self.fracture_counter[fracture_point] += 1
        
        self._log_divergence(record)
        self._save_to_file()

    def _extract_fracture_point(self, stack_trace: List[str]) -> str:
        """Extract meaningful fracture point from stack trace"""
        for frame in reversed(stack_trace[:-1]):  # Exclude current frame
            if 'unified_runtime_validator.py' not in frame:
                # Extract function/file info
                lines = frame.split('\n')
                if lines:
                    return lines[0].strip()
        return "unknown_fracture_point"

    def _log_divergence(self, record: DivergenceRecord) -> None:
        """Log divergence with timestamp and language context"""
        self.logger.info(f"SEMANTIC DIVERGENCE DETECTED")
        self.logger.info(f"Language Mode: {record.language_mode.value}")
        self.logger.info(f"Timestamp: {record.timestamp}")
        self.logger.info(f"Fracture Point: {record.fracture_point}")
        self.logger.info(f"Coherence Impact: {record.coherence_impact}")
        self.logger.info("Stack Trace:")
        for line in record.stack_trace:
            self.logger.info(f"  {line.rstrip()}")

    def _save_to_file(self) -> None:
        """Save divergence records to JSON file"""
        try:
            records_data = []
            for record in self.divergence_records:
                record_dict = asdict(record)
                record_dict['language_mode'] = record.language_mode.value
                records_data.append(record_dict)
            
            with open(self.log_file, 'w') as f:
                json.dump(records_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save divergence log: {e}")

    def load_from_file(self) -> None:
        """Load divergence records from JSON file"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            
            self.divergence_records = []
            for record_data in data:
                record = DivergenceRecord(
                    timestamp=record_data['timestamp'],
                    language_mode=LanguageMode(record_data['language_mode']),
                    stack_trace=record_data['stack_trace'],
                    fracture_point=record_data['fracture_point'],
                    context_data=record_data['context_data'],
                    coherence_impact=record_data['coherence_impact']
                )
                self.divergence_records.append(record)
                self.fracture_counter[record.fracture_point] += 1
                
        except FileNotFoundError:
            self.logger.warning(f"Log file {self.log_file} not found")
        except Exception as e:
            self.logger.error(f"Failed to load divergence log: {e}")

    def replay_divergence(self, record_index: int) -> Optional[DivergenceRecord]:
        """Replay specific divergence scenario from logs"""
        if 0 <= record_index < len(self.divergence_records):
            record = self.divergence_records[record_index]
            self.logger.info("=== REPLAYING DIVERGENCE SCENARIO ===")
            self._log_divergence(record)
            return record
        else:
            self.logger.error(f"Invalid record index: {record_index}")
            return None

    def get_fracture_priority(self) -> List[Tuple[str, int, float]]:
        """Get prioritized list of fractures by recurrence and impact"""
        fracture_priority = []
        
        for fracture_point, count in self.fracture_counter.items():
            # Calculate average coherence impact for this fracture
            total_impact = sum(
                record.coherence_impact 
                for record in self.divergence_records 
                if record.fracture_point == fracture_point
            )
            avg_impact = total_impact / count if count > 0 else 0
            
            # Priority score: frequency * impact
            priority_score = count * avg_impact
            fracture_priority.append((fracture_point, count, avg_impact, priority_score))
        
        # Sort by priority score (descending)
        fracture_priority.sort(key=lambda x: x[3], reverse=True)
        return fracture_priority

    def generate_priority_report(self) -> str:
        """Generate report of prioritized fractures"""
        priority_list = self.get_fracture_priority()
        report = "=== FRACTURE PRIORITY REPORT ===\n"
        report += "Rank | Fracture Point | Frequency | Avg Impact | Priority\n"
        report += "-" * 60 + "\n"
        
        for i, (fracture, freq, impact, priority) in enumerate(priority_list[:20], 1):
            report += f"{i:4d} | {fracture[:30]:30s} | {freq:9d} | {impact:10.2f} | {priority:8.2f}\n"
        
        return report

    def clear_records(self) -> None:
        """Clear all divergence records"""
        self.divergence_records.clear()
        self.fracture_counter.clear()
        self._save_to_file()
        self.logger.info("All divergence records cleared")