from core.preambs import *
from core.operationals import *
import document as doc

class Resolution:
    def __init__(self, 
                committee: str = "Test Committee",
                mainSubmitter: str = "Main Submitter Country Name",
                coSubmitters: list[str] | None = None,
                topic: str = "Test Topic",
                preambs: list[preamb] | None = None,
                clauses: list[clause] | None = None) -> None:
        self.committee = committee
        self.mainSubmitter = mainSubmitter
        self.coSubmitters = coSubmitters if coSubmitters is not None else []
        self.topic = topic
        self.preambs = preambs if preambs is not None else []
        self.clauses = clauses if clauses is not None else []
    
    def __str__(self) -> str:
        # Header section
        header = f"RESOLUTION: {self.topic.upper()}\n"
        header += "=" * 60 + "\n\n"
        
        # Committee and submitters
        header += f"Committee: {self.committee}\n"
        header += f"Main Submitter: {self.mainSubmitter}\n"
        
        if self.coSubmitters:
            co_submitters_str = ", ".join(self.coSubmitters)
            header += f"Co-Submitters: {co_submitters_str}\n"
        
        header += "\n" + "=" * 60 + "\n\n"
        
        # Preambs section
        preambs_section = "PREAMBULATORY CLAUSES:\n"
        preambs_section += "-" * 30 + "\n"
        
        for i, preamb in enumerate(self.preambs, 1):
            preambs_section += f"{i}. {preamb.adverb.upper()} {preamb.content}\n"
        
        preambs_section += "\n"
        
        # Operational clauses section
        clauses_section = "OPERATIONAL CLAUSES:\n"
        clauses_section += "-" * 25 + "\n"
        
        for i, clause in enumerate(self.clauses, 1):
            clauses_section += f"\n{i}. {clause.verb.upper()} {clause.text}\n"
            
            # Subclauses
            for j, subclause in enumerate(clause.listsubclauses, 1):
                letter = chr(96 + j)  # a, b, c, etc.
                clauses_section += f"   {letter}) {subclause.text}\n"
                
                # Sub-subclauses
                for k, subsubclause in enumerate(subclause.listsubsubclauses, 1):
                    roman = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"][k-1]
                    clauses_section += f"      {roman}. {subsubclause.text}\n"
        
        # Combine all sections
        return header + preambs_section + clauses_section
    
    def summary(self) -> str:
        """Return a brief summary of the resolution"""
        return (f"Resolution on '{self.topic}' by {self.mainSubmitter} "
                f"({len(self.preambs)} preambs, {len(self.clauses)} clauses, "
                f"{sum(len(clause.listsubclauses) for clause in self.clauses)} subclauses)")
