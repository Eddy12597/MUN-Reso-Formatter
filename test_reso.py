import src.main as formatter
import src.document as mydoc

reso, _, _ = formatter.parseToResolution(doc = mydoc.document("tests/inputs/test_reso.docx", "tests/outputs/test_reso.docx"))

from server import getCommitteeShortened

print(getCommitteeShortened(reso.committee))

formatter.writeToFile(reso, "tests/outputs/test_reso.docx")

