from typing import Dict, List, Tuple
from researchmind.agent.models import StructuredAnswer, CanonicalEvidence

class GroundingValidator:
    """Validates citations and enforces a conservative grounding heuristic."""

    def __init__(self, evidence_cache: Dict[str, CanonicalEvidence]):
        self.evidence_cache = evidence_cache

    def validate(self, answer: StructuredAnswer) -> StructuredAnswer:
        """
        Validate the StructuredAnswer against the retrieved evidence.
        Updates the grounding_status and confidence based on validation.
        """
        if not answer.citations and answer.grounding_status == "grounded":
            # If they claim it's grounded but provide no citations
            answer.grounding_status = "insufficient_evidence"
            answer.confidence = "low"
            answer.limitations.append("No citations provided for the answer.")
            return answer

        valid_citations = []
        has_invalid = False
        
        for cit in answer.citations:
            if cit.evidence_id not in self.evidence_cache:
                has_invalid = True
                answer.limitations.append(f"Citation validation failed: evidence_id '{cit.evidence_id}' does not exist.")
                continue
            
            ev = self.evidence_cache[cit.evidence_id]
            
            # Check clause number match
            if cit.clause_number and ev.clause_number and cit.clause_number != ev.clause_number:
                has_invalid = True
                answer.limitations.append(f"Citation mismatch: cited clause '{cit.clause_number}' does not match evidence '{ev.clause_number}'.")
                continue
                
            # Check page number match
            if cit.page_number and ev.page_number and cit.page_number != ev.page_number:
                has_invalid = True
                answer.limitations.append(f"Citation mismatch: cited page '{cit.page_number}' does not match evidence '{ev.page_number}'.")
                continue
                
            valid_citations.append(cit)
            
        answer.citations = valid_citations

        if has_invalid:
            answer.grounding_status = "validation_failed"
            answer.confidence = "low"
        
        # If the LLM declared insufficient evidence, preserve that state
        if answer.grounding_status == "insufficient_evidence":
            answer.confidence = "low"
            
        # Ensure confidence constraints
        if answer.grounding_status != "grounded":
            answer.confidence = "low"
            
        return answer
