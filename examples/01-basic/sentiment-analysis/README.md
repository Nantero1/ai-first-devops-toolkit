# Sentiment Analysis Example

Demonstrates structured output with schema enforcement for sentiment analysis.

## Files
- `input.json` - The prompt and messages
- `schema.json` - JSON schema for structured output
- `README.md` - This documentation

## Usage
```bash
uv run llm_runner.py \
  --input-file examples/01-basic/sentiment-analysis/input.json \
  --output-file result.json \
  --schema-file examples/01-basic/sentiment-analysis/schema.json \
  --log-level INFO
```

## What This Demonstrates
- Structured output with 100% schema enforcement
- Enum constraints (sentiment: positive/negative/neutral)
- Numeric constraints (confidence: 0-1 range)
- Array constraints (key_points: 1-5 items)
- String constraints (summary: max 200 characters)

## Schema Features
- **Enum Validation**: Sentiment must be one of the predefined values
- **Range Validation**: Confidence score must be between 0 and 1
- **Array Limits**: Key points must have 1-5 items
- **String Length**: Summary must be under 200 characters 