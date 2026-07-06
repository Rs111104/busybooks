# BusyBooks

BusyBooks is a modular desktop bookkeeping and accounting application built in Python. It helps users record and manage financial transactions, maintain accurate books, and generate clean reports — with a strong focus on data validation, integrity, and reliability.

## Overview

BusyBooks provides a simple, standalone way to handle everyday bookkeeping without spreadsheets or web dependencies. It stores records in a local database, offers an easy desktop interface, and produces formatted reports for review and sharing. Built-in audit and self-check routines continuously validate the data so your books stay consistent and trustworthy.

## Features

- 📒 Bookkeeping & records management — record, edit, and manage financial transactions and accounts
- 🗄️ Local database storage — persistent, reliable storage for all entries and records
- 📊 Automated reports — generate formatted HTML/PDF report output for review and sharing
- ✅ Data validation & integrity — audit, self-check, and feature-verification routines keep data clean and consistent
- 🖥️ Desktop interface — standalone UI, no browser required
- 🧪 Tested — automated test suite using pytest
- 📦 Distributable — packaged into a standalone executable with PyInstaller

## Tech Stack

- Language: Python 3.x
- Database: SQLite
- Testing: pytest
- Packaging: PyInstaller
- Reporting: HTML / TeX (PDF)

## Project Structure

    busybooks/
    ├── core/            # Core business logic
    ├── services/        # Application services
    ├── db/              # Database layer and models
    ├── ui/              # User interface
    ├── utils/           # Helper utilities
    ├── output/          # Generated reports and exports
    ├── tests/           # Automated test suite
    ├── main.py          # Application entry point
    ├── audit_run.py     # Data audit routine
    ├── selfcheck.py     # Self-check / integrity validation
    ├── featurecheck.py  # Feature verification
    ├── probe.py         # Diagnostics
    ├── conftest.py      # pytest configuration
    └── BusyBooks.spec   # PyInstaller build spec

## Getting Started

### Prerequisites

- Python 3.x installed on your system

### Installation

    # Clone the repository
    git clone https://github.com/Rs111104/busybooks.git
    cd busybooks

    # (Recommended) create and activate a virtual environment
    python -m venv .venv
    source .venv/bin/activate        # On Windows: .venv\Scripts\activate

    # Install dependencies
    pip install -r requirements.txt

### Running the App

    python main.py

## Testing

Run the full test suite:

    pytest

Run the additional validation utilities:

    python audit_run.py       # Run data audit
    python selfcheck.py       # Run integrity self-check
    python featurecheck.py    # Verify features

## Building an Executable

Package the app into a standalone executable:

    pyinstaller BusyBooks.spec

The built application will be available in the dist/ folder.

## Contributing

Contributions are welcome. Fork the repository, create a feature branch, commit your changes, and open a pull request.

## License

This project is licensed under the MIT License — see the LICENSE file for details.

## Author

Rahul Singhi
GitHub: https://github.com/Rs111104
