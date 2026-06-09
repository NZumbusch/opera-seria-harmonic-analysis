# Opera Seria Harmonic Analysis

This repository contains the source code for the harmonic analysis of eighteenth-century opera seria arias, as presented in the paper "Discovering trends in historical aria data using loess smoothing, functional component analysis and generalized skipgrams" (working title, see `papers/overview.tex`).

## Project Overview

The project uses computational methods to analyze harmonic patterns, schemata usage, and stylistic developments in a large corpus of opera seria. It leverages statistical tools such as Functional Principal Component Analysis (FPCA) and LOESS smoothing to identify trends across time and different composers.

## Data Notice (NDA)

The primary dataset used in this study is the **DIDONE corpus**, an ERC-funded project at the Instituto Complutense de Ciencias Musicales (ICCM). Due to a Non-Disclosure Agreement (NDA), the raw musical scores (`.mscx`) and processed data (`.tsv`) from the DIDONE corpus **cannot be distributed in this repository**.

Researchers interested in replicating the results or using the corpus should contact the [DIDONE Project Team](https://didone.eu/) to request access to the dataset.

The code provided here can be used to process similar datasets if they follow the MuseScore format or can be converted to the intermediate TSV format used by the pipeline.

## Installation

This project uses `setuptools` and `pyproject.toml` for dependency management. It is recommended to use a virtual environment.

```bash
# Clone the repository
git clone https://github.com/NZumbusch/opera-seria-harmonic-analysis
cd opera-seria-harmonic-analysis

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`

# Install the package and its dependencies
pip install .
```

### Main Dependencies

- `ms3`: For parsing MuseScore files and extracting harmonic DCML labels.
- `pandas`, `numpy`: For data manipulation.
- `matplotlib`, `plotly`, `scienceplots`: For visualization.
- `scikit-fda` (`skfda`): For Functional Data Analysis.
- `scikit-learn`: For clustering (K-Means).
- `pydantic`: For data validation and modeling.

## Usage

### 1. Building the Aria Index

If you have access to the `.mscx` files, you can build the aria index:

```bash
python src/corpus/build_aria_index.py
```

### 2. Processing Scores

Extract harmonic labels and metadata in parallel using `ms3`:

```bash
python src/corpus/build_tsv_parallel.py
```

### 3. Harmonic Analysis

Run various analysis scripts located in `src/analysis/`:

- `src/analysis/chord_distribution/`: Analyze chord frequencies and trends.
- `src/analysis/schemata/`: Identify musical schemata.
- `src/analysis/tonal_journey/`: Analyze the tonal trajectory of arias.

### 4. Visualization

Generate plots and interactive figures:

- `src/visualization/chord_usage_timeline_loess.py`
- `src/visualization/fda_timeline.py`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this code or the findings in your research, please cite this repository or the accompaning paper.
