import re
from dataclasses import dataclass


@dataclass
class ParsedClauseNumber:
    """Result of parsing a clause number from text."""
    raw: str              # "8.2.1" or "(a)" or "(iii)"
    parts: list[str]      # ["8", "2", "1"] or ["a"] or ["iii"]
    numbering_depth: int  # 2 for "8.2.1", 0 for "(a)" within its parent
    normalized: str       # "8.2.1" or "a" or "iii"
    numbering_type: str   # "decimal" | "letter" | "roman" | "label"


class ClauseNumberParser:
    """Parses and normalises Indian regulatory clause numbering schemes.
    
    Supports:
    - Decimal:      8, 8.1, 8.2, 8.2.1, 8.2.1.1
    - Lettered:     (a), (b), ..., (z)
    - Roman:        (i), (ii), ..., (xv)
    - Labels:       Table 8-B, Schedule I, Note, Proviso
    """
    
    DECIMAL = re.compile(r"^\s*(\d+(?:\.\d+)*)\b")
    LETTER  = re.compile(r"^\s*\(([a-z])\)")
    ROMAN   = re.compile(r"^\s*\(([ivxlc]+)\)", re.IGNORECASE)
    LABEL   = re.compile(
        r"^\s*(Table\s+\d+-?[A-Z]?|Schedule\s+[IVX]+|Note|Proviso|Provided\s+that|Explanation)",
        re.IGNORECASE,
    )

    def parse(self, text: str) -> ParsedClauseNumber | None:
        if not text:
            return None
            
        # Try decimal
        match = self.DECIMAL.match(text)
        if match:
            raw = match.group(1)
            parts = raw.split(".")
            return ParsedClauseNumber(
                raw=raw,
                parts=parts,
                numbering_depth=len(parts) - 1,
                normalized=raw,
                numbering_type="decimal"
            )
            
        # Try letter
        match = self.LETTER.match(text)
        # Try roman (check before letter to catch 'i', 'v', 'x' as roman if needed)
        # Actually, if we just swap them, (i) will be roman.
        match = self.ROMAN.match(text)
        if match:
            raw = match.group(0).strip()
            letter = match.group(1)
            roman = match.group(1).lower()
            return ParsedClauseNumber(
                raw=raw,
                parts=[letter],
                parts=[roman],
                numbering_depth=0,
                normalized=letter,
                numbering_type="letter"
                normalized=roman,
                numbering_type="roman"
            )
            
        # Try roman
        match = self.ROMAN.match(text)
        # Try letter
        match = self.LETTER.match(text)
        if match:
            raw = match.group(0).strip()
            roman = match.group(1).lower()
            letter = match.group(1).lower()
            return ParsedClauseNumber(
                raw=raw,
                parts=[roman],
                parts=[letter],
                numbering_depth=0,
                normalized=roman,
                numbering_type="roman"
                normalized=letter,
                numbering_type="letter"
            )
            
        # Try label
        match = self.LABEL.match(text)
        if match:
            raw = match.group(1).strip()
            # Normalize title case for standard labels
            normalized = raw.title() if " " not in raw else raw.capitalize()
            # Handle special case: Table 8-B
            if normalized.lower().startswith("table"):
                normalized = "Table " + raw.split(maxsplit=1)[1].upper()
            return ParsedClauseNumber(
                raw=raw,
                parts=[normalized],
                numbering_depth=0,
                normalized=normalized,
                numbering_type="label"
            )
            
        return None

    def depth(self, clause_number: str) -> int:
        parsed = self.parse(clause_number)
        if parsed:
            return parsed.numbering_depth
        return 0

    def is_child_of(self, child: str, parent: str) -> bool:
        """Determines if 'child' is a direct or deep descendant of 'parent' using strict decimal hierarchy rules."""
        parsed_child = self.parse(child)
        parsed_parent = self.parse(parent)
        
        if not parsed_child or not parsed_parent:
            return False
            
        # Only decimal numbers have true nested parent/child relationships that we can compute from the number alone
        if parsed_child.numbering_type == "decimal" and parsed_parent.numbering_type == "decimal":
            if parsed_child.numbering_depth <= parsed_parent.numbering_depth:
                return False
            # Check prefix
            parent_prefix = parsed_parent.normalized + "."
            return parsed_child.normalized.startswith(parent_prefix)
            
        return False

    def common_ancestor(self, a: str, b: str) -> str | None:
        """Finds the lowest common ancestor of two decimal clause numbers."""
        parsed_a = self.parse(a)
        parsed_b = self.parse(b)
        
        if not parsed_a or not parsed_b:
            return None
            
        if parsed_a.numbering_type != "decimal" or parsed_b.numbering_type != "decimal":
            return None
            
        parts_a = parsed_a.parts
        parts_b = parsed_b.parts
        
        common = []
        for pa, pb in zip(parts_a, parts_b):
            if pa == pb:
                common.append(pa)
            else:
                break
                
        if not common:
            return None
            
        return ".".join(common)
