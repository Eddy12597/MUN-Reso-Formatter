# MUN-Reso-Formatter

Python App for formatting MUN Resolutions made with python-docx. May be integrated into [website](https://mun-chair.netlify.app) or [conference website](https://biphmun.netlify.app) as backend.

## Build and run

Currently the project is around 60~70% finished, but it can:
- pop up GUI window
- extract resolution structure to a [`Resolution`](./src/core/resolution.py) object
- automatically correct errors
- show where the format of the resolution document is incorrect.

```bash
pip install -r requirements.txt
cd src
python main.py ../tests/inputs/test_problematic.docx -o ../tests/outputs/test_problematic.docx -l ../tests/outputs/formatter.log
```

## Usage / Help

```bash
usage: [-h] [-v] [-o [OUTPUT]] [-l [LOG]] [filename]

Formats a resolution (.docx) and outputs file.

positional arguments:
  filename              input filename (optional)

options:
  -h, --help            show this help message and exit
  -v, --verbose         enable verbose mode
  -o, --output [OUTPUT]
                        output filename
  -l, --log [LOG]       log file name
```

### Resolution Format

Sample resolutions are available in [`tests/`](./tests/)

## Contributing

Contributions (issues, PRs) are welcome. You can also add preambulatory/operational phrases by changing [`./src/config/preambs/config.json`](./src/config/preambs/config.json) or [`./src/config/operationals/config.json`](./src/config/operationals/config.json). You can contribute to app logic development in [`./src`](./src), or develop/refine workflow. Raise an issue or submit a PR.

## TODO / Roadmap:

1. Refine Error handling and showing
2. Enable adding to config (for phrases and adverbs)
3. Upgrade GUI:
    - Preview (tree view of clauses)
    - Verbose mode
    - Drag and drop
4. Integrate to website if appropriate
5. (Far future) allow amendment logic and apply amendments (though probably nobody cares)

