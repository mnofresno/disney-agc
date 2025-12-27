# Testing

## Run Tests

```bash
pytest
pytest --cov=chromecast_agc --cov-report=html
pytest tests/test_audio/test_analyzer.py
```

## CI

Tests run automatically on push/PR via GitHub Actions (Python 3.9-3.12, Linux).
