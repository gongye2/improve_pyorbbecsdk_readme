# Type Stubs for pyorbbecsdk

This directory contains Python type stub files (`.pyi`) for the pyorbbecsdk package.

## What are .pyi files?

`.pyi` files are type stub files that provide type information for Python packages. They enable:
- **IDE Autocomplete**: Smart code completion in VS Code, PyCharm, etc.
- **Type Checking**: Static type analysis with tools like mypy or pyright
- **Better Documentation**: Inline documentation for classes and functions

## Usage

### For IDE Autocomplete (Recommended)

Simply install the pyorbbecsdk package, and the stubs will be automatically available:

```bash
pip install pyorbbecsdk2
```

In VS Code with Pylance extension:
```python
from pyorbbecsdk import Context, Pipeline, Config

# Now you'll get autocomplete suggestions for all methods
pipeline = Pipeline()
pipeline.start()  # Autocomplete shows available methods
```

### Manual Installation

If your IDE doesn't automatically detect the stubs, you can copy them:

```bash
# Find the package installation path
pip show pyorbbecsdk2

# Copy stubs to the package directory (optional)
cp stubs/*.pyi $(python -c "import pyorbbecsdk, os; print(os.path.dirname(pyorbbecsdk.__file__))")/
```

## Generating Stubs

To regenerate stubs from the compiled module:

```bash
# Install pybind11-stubgen
pip install pybind11-stubgen

# Generate stubs
pybind11-stubgen pyorbbecsdk -o .

# Fix the generated stubs (if needed)
python scripts/fix_pyi.py pyorbbecsdk.pyi
```

## Files

- `__init__.pyi`: Module exports and type definitions
- `pyorbbecsdk.pyi`: Main type definitions for all classes and functions
