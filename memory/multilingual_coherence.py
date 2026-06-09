import re
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

class LanguageMode(Enum):
    RUSSIAN = "ru"
    ENGLISH = "en"
    MIXED = "mixed"

@dataclass
class ConceptMapping:
    english_term: str
    russian_term: str
    confidence: float
    last_validated: float

@dataclass
class MemoryFragment:
    content: str
    language_mode: LanguageMode
    concepts: Set[str]
    timestamp: float

class MultilingualCoherenceValidator:
    def __init__(self):
        self.concept_mappings: Dict[str, ConceptMapping] = {}
        self.memory_fragments: List[MemoryFragment] = []
        self.language_switches: List[Tuple[float, LanguageMode, LanguageMode]] = []
        self.current_mode = LanguageMode.ENGLISH
        self.fragmentation_flags: List[Dict[str, Any]] = []
        
    def detect_language_mode(self, text: str) -> LanguageMode:
        """Detect the primary language mode of given text"""
        russian_chars = len(re.findall(r'[а-яА-ЯёЁ]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if russian_chars > english_chars:
            return LanguageMode.RUSSIAN
        elif english_chars > russian_chars:
            return LanguageMode.ENGLISH
        else:
            return LanguageMode.MIXED
            
    def trace_language_switch(self, timestamp: float, new_mode: LanguageMode) -> None:
        """Record language switch events"""
        if new_mode != self.current_mode:
            self.language_switches.append((timestamp, self.current_mode, new_mode))
            self.current_mode = new_mode
            
    def extract_concepts(self, text: str, language_mode: LanguageMode) -> Set[str]:
        """Extract key concepts from text based on language mode"""
        concepts = set()
        # Simple tokenization - in practice, would use more sophisticated NLP
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        if language_mode == LanguageMode.RUSSIAN:
            # Russian-specific concept extraction
            concepts.update(tokens)
        elif language_mode == LanguageMode.ENGLISH:
            # English-specific concept extraction
            concepts.update(tokens)
        else:
            # Mixed mode - separate by language
            ru_tokens = [t for t in tokens if re.match(r'^[а-яё]+$', t)]
            en_tokens = [t for t in tokens if re.match(r'^[a-z]+$', t)]
            concepts.update(ru_tokens + en_tokens)
            
        return concepts
        
    def add_memory_fragment(self, content: str, timestamp: float) -> None:
        """Add a memory fragment with language detection"""
        language_mode = self.detect_language_mode(content)
        concepts = self.extract_concepts(content, language_mode)
        
        fragment = MemoryFragment(
            content=content,
            language_mode=language_mode,
            concepts=concepts,
            timestamp=timestamp
        )
        
        self.memory_fragments.append(fragment)
        self.trace_language_switch(timestamp, language_mode)
        
    def register_concept_mapping(self, english_term: str, russian_term: str, confidence: float = 1.0) -> None:
        """Register a bidirectional concept mapping"""
        mapping_key = f"{english_term.lower()}:{russian_term.lower()}"
        self.concept_mappings[mapping_key] = ConceptMapping(
            english_term=english_term.lower(),
            russian_term=russian_term.lower(),
            confidence=confidence,
            last_validated=0.0  # Would use actual timestamp in practice
        )
        
    def is_concept_translated(self, concept: str, target_language: LanguageMode) -> bool:
        """Check if a concept has a translation in the target language"""
        if target_language == LanguageMode.ENGLISH:
            # Check if Russian concept has English translation
            for mapping in self.concept_mappings.values():
                if mapping.russian_term == concept.lower() and mapping.confidence > 0.7:
                    return True
        elif target_language == LanguageMode.RUSSIAN:
            # Check if English concept has Russian translation
            for mapping in self.concept_mappings.values():
                if mapping.english_term == concept.lower() and mapping.confidence > 0.7:
                    return True
        return False
        
    def flag_untranslated_concepts(self) -> List[Dict[str, Any]]:
        """Identify concepts that lack proper translations"""
        flags = []
        
        for fragment in self.memory_fragments:
            untranslated = set()
            
            for concept in fragment.concepts:
                if fragment.language_mode == LanguageMode.RUSSIAN:
                    if not self.is_concept_translated(concept, LanguageMode.ENGLISH):
                        untranslated.add(concept)
                elif fragment.language_mode == LanguageMode.ENGLISH:
                    if not self.is_concept_translated(concept, LanguageMode.RUSSIAN):
                        untranslated.add(concept)
                        
            if untranslated:
                flag = {
                    'fragment_id': id(fragment),
                    'untranslated_concepts': list(untranslated),
                    'language_mode': fragment.language_mode,
                    'timestamp': fragment.timestamp
                }
                flags.append(flag)
                self.fragmentation_flags.append(flag)
                
        return flags
        
    def validate_bidirectional_mapping(self, english_concept: str, russian_concept: str) -> bool:
        """Validate that concepts have bidirectional mappings"""
        forward_key = f"{english_concept.lower()}:{russian_concept.lower()}"
        reverse_key = f"{russian_concept.lower()}:{english_concept.lower()}"
        
        forward_exists = forward_key in self.concept_mappings and \
                        self.concept_mappings[forward_key].confidence > 0.7
        reverse_exists = reverse_key in self.concept_mappings and \
                        self.concept_mappings[reverse_key].confidence > 0.7
                        
        return forward_exists and reverse_exists
        
    def enforce_coherence_before_commit(self, modifications: Dict[str, Any]) -> bool:
        """Enforce coherence validation before allowing deep modifications"""
        # Check for language switches in recent history
        if len(self.language_switches) > 2:
            recent_switches = [s for s in self.language_switches[-5:] 
                             if s[0] > modifications.get('timestamp', 0) - 3600]  # Last hour
            if len(recent_switches) > 2:
                return False  # Too many switches indicate fragmentation
                
        # Check untranslated concepts in modification context
        content = modifications.get('content', '')
        language_mode = self.detect_language_mode(content)
        concepts = self.extract_concepts(content, language_mode)
        
        for concept in concepts:
            if language_mode == LanguageMode.RUSSIAN:
                if not self.is_concept_translated(concept, LanguageMode.ENGLISH):
                    return False
            elif language_mode == LanguageMode.ENGLISH:
                if not self.is_concept_translated(concept, LanguageMode.RUSSIAN):
                    return False
                    
        # Validate bidirectional mappings for key concepts
        key_concepts = modifications.get('key_concepts', [])
        for concept_pair in key_concepts:
            if len(concept_pair) == 2:
                if not self.validate_bidirectional_mapping(concept_pair[0], concept_pair[1]):
                    return False
                    
        return True
        
    def get_fragmentation_report(self) -> Dict[str, Any]:
        """Generate a comprehensive fragmentation analysis report"""
        untranslated_flags = self.flag_untranslated_concepts()
        
        return {
            'total_fragments': len(self.memory_fragments),
            'language_switches': len(self.language_switches),
            'untranslated_concepts': len(untranslated_flags),
            'fragmentation_flags': untranslated_flags,
            'concept_mappings_count': len(self.concept_mappings),
            'current_language_mode': self.current_mode.value
        }

# Example usage
if __name__ == "__main__":
    validator = MultilingualCoherenceValidator()
    
    # Register some concept mappings
    validator.register_concept_mapping("memory", "память", 0.95)
    validator.register_concept_mapping("concept", "концепция", 0.90)
    validator.register_concept_mapping("validation", "валидация", 0.85)
    
    # Add memory fragments
    validator.add_memory_fragment("Working with memory systems", 1000.0)
    validator.add_memory_fragment("Работа с системами памяти", 1001.0)
    validator.add_memory_fragment("Fragmentation detection", 1002.0)  # Missing Russian translation
    
    # Check for untranslated concepts
    flags = validator.flag_untranslated_concepts()
    print("Untranslated concepts:", flags)
    
    # Test modification enforcement
    modification = {
        'content': "Deep memory validation process",
        'timestamp': 1003.0,
        'key_concepts': [['memory', 'память'], ['validation', 'валидация']]
    }
    
    is_coherent = validator.enforce_coherence_before_commit(modification)
    print("Modification coherence check:", is_coherent)
    
    # Generate report
    report = validator.get_fragmentation_report()
    print("Fragmentation report:", report)