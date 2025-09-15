# MUN-Reso-Formatter

Docx-basd Python App for formatting MUN Resolutions. May be integrated into [website](biphmun.netlify.app) as backend.

## Build and run

Currently the project is only around 30~50% finished, but you can test the basic extraction functionality.

```bash
pip install -r requirements.txt
cd src
python main.py
```

## Help

```bash
/path/to/MUN-Reso-Formatter/src$ python main.py --help
usage: [-h] [-v] [-o OUTPUT] [filename]

Formats a resolution (.docx) and outputs file.

positional arguments:
  filename             input filename (optional)

options:
  -h, --help           show this help message and exit
  -v, --verbose        enable verbose mode
  -o, --output OUTPUT  output filename
```

### TODO:

1. Finish app logic
2. Fix alignment centering
3. Develop GUI (with input fields and upload file)
4. Integrate to website if appropriate
5. (Far future) allow amendment logic and apply amendments (though probably nobody cares)

# Resolution Format:

The resolution should have Times New Roman font family with font size 12 and double spacing.
--------------------------------------------------------------------------------------------

## Header

`<strong>`Committee: `</strong>`Capitalize With Spaces (Initials without '.')

`<strong>`Main Submitter: `</strong>`Capitalize With Spaces

`<strong>`Co-Submitters: `</strong>`Country Name, Another Country Name, Capitalize With Space and Commas

`<strong>`Topic: `</strong>` Capitalize With Spaces

---

## Body

The Committee Name,

### Preambs

`<em>`Adverb in italic`</em>` something,
`<em>`Capitalize first word`</em>` some other stuff,
`<em>`Capitalize first word`</em>` some other stuff,
`<em>`Keeping in mind that`</em>` "The Committee Name" be placed before the preambulatory clauses,

### Operational Clauses

<ol>
  <li>
    <u>Capitalized Operational Verb</u> that states the main idea of the clause, ending with a semi-colon or colon, where the subclauses are formatted like below:
    <ol style="list-style-type: lower-alpha">
      <li>Capitalized first word of subclause, ending with a comma,</li>
      <li>Another sub-clause, as a clause must have two subclauses, ending with a comma, </li>
      <li>Maybe other optional subclauses, or sub-sub-clauses:
        <ol style="list-style-type: lower-roman">
          <li>A first sub-sub-clause,</li>
          <li>A second sub-sub-clause, as the same rules apply for sub-sub-clauses as well as sub-clauses, ending with commas too,</li>
        </ol>
      </li>
    </ol>
  </li>
  <li>
    <u>Capitalized Operational Verb</u> another clause, the same rules apply; the user should input the minimum number of clauses as well, and the very last sub/sub-sub clause should end with a period.
  </li>
</ol>
---
