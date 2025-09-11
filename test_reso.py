# test_clause_export.py
import src.document as doc
from core.operationals import clause, subclause, subsubclause

def test_toDocParagraph():
    # Clause 1
    c1 = clause(
        index=1,
        verb="Urges",
        text="all member states to implement climate action plans",
        listsubclauses=[
            subclause(
                index=1,
                text="Nationally Determined Contributions that exceed current pledges",
                listsubsubclauses=[
                    subsubclause(1, "Carbon pricing mechanisms"),
                    subsubclause(2, "Renewable energy investments")
                ]
            ),
            subclause(
                index=2,
                text="Regular public reporting of emissions"
            )
        ]
    )

    # Clause 2
    c2 = clause(
        index=2,
        verb="Calls upon",
        text="developed nations to provide financing",
        listsubclauses=[
            subclause(
                index=1,
                text="At least $100 billion annually to the Green Climate Fund",
                listsubsubclauses=[
                    subsubclause(1, "50% for adaptation"),
                    subsubclause(2, "50% for mitigation")
                ]
            )
        ]
    )

    doc_out = doc.document(
        inputfile="tests/inputs/test1.docx",
        outputfile="tests/outputs/test_reso.docx",
        line_spacing = 2,
    )

    for cl in [c1, c2]:
        for para in cl.toDocParagraphs():
            # para.line_spacing = 2
            doc_out.append(para)

    doc_out.save()

if __name__ == "__main__":
    test_toDocParagraph()
