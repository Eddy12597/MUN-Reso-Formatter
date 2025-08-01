from preambs import *
from operationals import *
import document as doc

class Resolution:
    def __init__(self, committee: str = "Test Committee",
                    mainSubmitter: str = "Main Submitter Country Name",
                    coSubmitters: list[str] | None = None,
                    topic: str = "Test Topic",
                    preambs: list[preamb] | None = None) -> None:
        self.committee = committee;
        self.mainSubmitter = mainSubmitter;
        self.coSubmitters = coSubmitters if coSubmitters is not None else []
        self.topic = topic
        self.preambs = preambs if preambs is not None else []
    