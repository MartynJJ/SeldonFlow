# Market Maker for Prediction Markets

A systematic market making platform for prediction markets, starting with Kalshi and expandable to PolyMarket.

## Setup
1. Install Poetry: `pip install poetry`
2. Install dependencies: `poetry install`
3. Configure API keys in `config/api_keys.yaml`
4. Run the platform: `poetry run python src/seldonflow/scripts/run.py`

## Structure
- `src/`: Core code (API clients, strategies, execution, etc.)
- `tests/`: Unit tests
- `config/`: Configuration files
- `scripts/`: Entry points