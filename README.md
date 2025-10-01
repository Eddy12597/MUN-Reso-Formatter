# MUN-Reso-Formatter

Docx-basd Python App for formatting MUN Resolutions. May be integrated into [website](https://biphmun.netlify.app) as backend.

## Build and run

Currently the project is only around 50~60% finished, but you can test the basic extraction functionality.

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

Sample resolutions are available in `tests/`


### TODO:

1. Refine Error handling and showing
2. Enable adding to config (for phrases and adverbs)
3. Develop GUI (with input fields and upload file)
4. Integrate to website if appropriate
5. (Far future) allow amendment logic and apply amendments (though probably nobody cares)

