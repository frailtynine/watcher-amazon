# AI Consumer Module

This module handles AI-powered news processing using Amazon Bedrock (Nova).

## Overview

The AI consumer processes news items by:
1. Fetching unprocessed news items (published within the last 4 hours)
2. Running them through user-defined prompts via Amazon Nova on AWS Bedrock
3. Storing results (match/no-match) with AI reasoning

## Components

### `nova_client.py`

Wrapper around Amazon Bedrock's converse API:
- **Inference profile / model**: `global.amazon.nova-2-lite-v1:0` (recommended)
- **Input**: News title, content, and user prompt
- **Output**: Structured JSON with:
  - `result`: Boolean (matches criteria or not)
  - `thinking`: AI's explanation
  - `tokens_used`: Token count for the request

**Example usage:**
```python
client = NovaClient(
    aws_access_key_id="key",
    aws_secret_access_key="secret",
    region_name="us-east-1",
)
result = await client.process_news(
    title="Breaking News",
    content="Full article text...",
    prompt="Find news about technology"
)
# result.result -> True/False
# result.thinking -> "This article discusses..."
# result.tokens_used -> 150
```

### `consumer.py`

Main consumer logic:
- **Global AWS credentials**: Uses `BACKEND_AWS_*` settings for all users
- **Active tasks only**: Only processes tasks marked as `active=True`
- **Time window**: Only processes news published within last 4 hours
- **Deduplication**: Skips already-processed item-task combinations
- **Error isolation**: Errors for one item don't stop processing others

**Example usage:**
```python
consumer = AIConsumer()
stats = await consumer.process_user_news(user_id)
# stats -> {"processed": 10, "errors": 1}
```

## Database Schema

Results stored in `news_item_news_task` table:
- `news_item_id`, `news_task_id` - Composite primary key
- `processed` - Boolean flag
- `result` - True if news matches task prompt
- `ai_response` - Full JSON response from Amazon Nova:
  ```json
  {
    "thinking": "This article discusses AI advancements...",
    "tokens_used": 150,
    "processed_at": "2024-01-15T10:30:00"
  }
  ```

## Configuration

AWS credentials are configured via environment variables:
```
BACKEND_AWS_ACCESS_KEY=your-aws-access-key-id
BACKEND_AWS_SECRET_KEY=your-aws-secret-access-key
BACKEND_AWS_REGION=us-east-1
BACKEND_AWS_BEDROCK_MODEL_ID=global.amazon.nova-2-lite-v1:0
```

## Error Handling

- **API errors**: Logged but don't stop processing other items
- **Invalid responses**: Defaults to `result=False`, empty thinking

## Testing

Tests use mocked AWS Bedrock responses:
```bash
# Run all AI tests
make test-unit FILE=tests/test_nova_client.py
make test-unit FILE=tests/test_ai_consumer.py
```

## Future Integration

To integrate into the scheduler:
1. Import in `app/main.py`:
   ```python
   from app.ai.consumer import AIConsumer
   ```
2. Add scheduled job:
   ```python
   async def ai_consumer_job():
       async for db in get_async_session():
           users = await get_all_users(db)
           consumer = AIConsumer()
           for user in users:
               await consumer.process_user_news(user.id)
   ```
3. Schedule it:
   ```python
   scheduler.add_job(
       ai_consumer_job,
       'interval',
       minutes=10,
       id='ai_consumer',
       replace_existing=True
   )
   ```
