# Sentiment Analysis Example

Demonstrates structured output with schema enforcement for sentiment analysis.

## Files
- `input.json` - The prompt and messages
- `schema.json` - JSON schema for structured output
- `README.md` - This documentation

## Example:

When you use this example, here is what happens step by step:

**Input:**
```json
{
    "messages": [
        {
            "role": "system",
            "content": "You are an expert sentiment analysis tool. "
                       "Analyze the sentiment of the given text and provide structured analysis."
        },
        {
            "role": "user",
            "content": 
                "Analyze the sentiment of this text: "
                "'I absolutely love this new AI-first development approach!"
                "The productivity gains are incredible and the team is really excited about"
                "the possibilities. The only concern is the learning curve, but we're confident"
                "we can overcome it.'"
        }
    ],
    "context": {
        "session_id": "sentiment-analysis-001",
        "metadata": {
            "task_type": "sentiment_analysis",
            "domain": "text_analysis"
        }
    }
}
```

**Schema:** The system enforces a JSON schema that defines the output structure:
- `sentiment`: Must be one of ["positive", "negative", "neutral"]
- `confidence`: Number between 0 and 1
- `key_points`: Array of 1-5 strings
- `summary`: String with max 200 characters


## Usage
```bash
llm-ci-runner \
  --input-file examples/01-basic/sentiment-analysis/input.json \
  --schema-file examples/01-basic/sentiment-analysis/schema.json
```

**Output:**
```json
{
  "success": true,
  "response": {
    "sentiment": "positive",
    "confidence": 0.85,
    "key_points": [
      "AI-first development approach",
      "Productivity gains",
      "Team excitement",
      "Learning curve concern"
    ],
    "summary": "The text expresses enthusiasm for AI-focused development,"
               "highlighting productivity improvements and team excitement,"
               "with a minor concern about the learning curve."
  },
  "metadata": {
    "runner": "llm-ci-runner",
    "timestamp": "auto-generated"
  }
}
```


## What This Demonstrates
- Structured output with 100% schema enforcement
- Enum constraints (sentiment: positive/negative/neutral)
- Numeric constraints (confidence: 0-1 range)
- Array constraints (key_points: 1-5 items)
- String constraints (summary: max 200 characters)
