# CadQuery HSW Generator

Parametric **Honeycomb Storage Wall** generator written in **CadQuery**.

This project generates printable HSW-compatible parts (baseplates, bins, hooks, and adapters) from Python parameters, inspired by the OpenSCAD concept shown here:  
<https://www.printables.com/model/163200-openscad-parameterized-honeycomb-storage-wall>

> This repository is an independent CadQuery implementation.

## Features

- Fully parametric geometry (cell size, wall thickness, depth, tolerances)
- Scriptable part generation in Python
- Easy variant creation for different printers and materials
- Export to `STEP`, `STL`, and `3MF` (if supported by your toolchain)

## Requirements

- Python 3.10+
- CadQuery 2.3+  
- Optional: CQ-editor for interactive preview

## Installation

```bash
git clone https://github.com/macdems/hsw-generator.git
cd hsw-generator
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

## Usage

Run the generator script with desired parameters. For example, to create a baseplate with 10 rows and 9 columns of holes:

```bash
./hsw-base --rows 10 --cols 9
```

To add M3.5 screw holes and alternate the hole pattern:

```bash
./hsw-base --rows 10 --cols 9 --screws M3.5 --alternate
```

To save the output to a specific file:

```bash
./hsw-base --rows 10 --cols 9 output.step
```

### Available options

- `-h`, `--help`        Show help message and exit
- `--rows`, `-r`   Number of rows of holes (default: `9`)
- `--cols`, `-c`   Number of columns of holes (default: `9`)
- `--screws`, `-s`   Screw size for mounting holes
- `--alternate`, `-a`   Alternate the hole pattern along the columns (start with a short column)
- `--frame`, `-f`   Include edges in the frame. Available options: `top`, `bottom`, `left`, `right`, `vertical`, `horizontal`, `all` (you can shortcut with the first letter).
- `--no-save`   Don’t save the STEP file

## Development Notes

- Keep all dimensions in millimeters.
- Prefer `STEP` for CAD exchange and `STL` for slicing.

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.  

You can find the full license text in the [`LICENSE.md`](LICENSE.md) file or at:  
<https://www.gnu.org/licenses/gpl-3.0.en.html>
  

## Credits

- Inspired by the OpenSCAD parameterized HSW idea on Printables:  
    <https://www.printables.com/model/163200-openscad-parameterized-honeycomb-storage-wall>
- Built with CadQuery: <https://cadquery.readthedocs.io/>
