# EQS Reconciliation SmoLAgent

A specialized agent for reconciling equity breaks using trade activity, positions, and total equity data.

## Description

This repository contains a SmoLAgent implementation designed for asset management reconciliation tasks. The agent analyzes three datasets—Trade Activity, Positions, and Total Equity—to identify and explain differences between calculated and reported closing equity. It provides tools for security valuation, trade analysis, and equity breakdown.

## Features

- Automated equity break analysis
- Security-level valuation and discrepancy detection
- Trade activity review for root cause analysis
- Step-by-step reconciliation workflow

## Installation

```bash
pip install -r requirements.txt
```

## Usage

- Clone the repo.
- Add a `.env` file in the `eqs-smolagent` folder with your API key (for OpenRouter or other LLM backend)
- Ensure the CSV files are present in the `data/` folder:
    - `trade_activity.csv`
    - `positions.csv`
    - `total_equity.csv`
- Run the following command to launch the Streamlit UI:
```bash
streamlit run eqs-agent.py
```

## Dependencies

- smolagents
- streamlit
- pandas
