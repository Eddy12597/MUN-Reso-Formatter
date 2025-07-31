# MUN-Reso-Formatter
Docx-basd Python App for formatting MUN Resolutions. May be integrated into [website](biphmun.netlify.app) as backend.

### TODO:
1. Finish app logic
2. Develop GUI (with input fields and upload file)
3. Integrate to website if appropriate
4. (Far future) allow amendment logic and apply amendments (though probably nobody cares)


# Resolution Format:
The resolution should have Times New Roman font family with font size 12 and double spacing.
---
## Header

<strong>Committee: </strong>Capitalize With Spaces (Initials without '.')

<strong>Main Submitter: </strong>Capitalize With Spaces

<strong>Co-Submitters: </strong>Country Name, Another Country Name, Capitalize With Space and Commas

<strong>Topic: </strong> Capitalize With Spaces



---

## Body
The Committee Name,

### Preambs

<em>Adverb in italic</em> something,
<em>Capitalize first word</em> some other stuff,
<em>Capitalize first word</em> some other stuff,
<em>Keeping in mind that</em> "The Committee Name" be placed before the preambulatory clauses,

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

