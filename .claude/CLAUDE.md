# Project: LuxuryTravel.AI Agent System

## Overview
Five-agent system for luxury travel booking with GDS/NDC integrations. This system provides a comprehensive solution for searching, comparing, and booking premium travel experiences including flights, hotels, and complete vacation packages.

## Architecture
- **Maestro**: Main orchestrator and conversation handler
- **Margaux**: Luxury hotel specialist (boutique hotels, resorts, amenities)
- **Atlas**: Flight/airline specialist (GDS, NDC, fare rules)
- **Isla**: Destination expert (local insights, experiences, recommendations)
- **Felix**: Booking/payment handler (reservations, confirmations, payments)

## Key Integrations
- **Downtown Travel**: Primary consolidator for GDS access
- **Kiwi.com API**: Flight connector and aggregator
- **GDS Terminals**: Amadeus, Sabre, Travelport via API
- **NDC Channels**: Direct airline booking capabilities
- **Payment Gateways**: Stripe, PayPal integration

## Development Conventions
- Use Python 3.10+
- Follow PEP 8 style guide
- Type hints required for all functions
- Async/await for I/O operations
- Error handling with custom exceptions
- Comprehensive logging with structured output

## Testing Requirements
- Minimum 80% code coverage
- Unit tests for all tools and utilities
- Integration tests for API connectors
- E2E tests for complete booking workflows
- Mock external APIs in tests

## Directory Structure
- `src/agents/` - Agent implementations (Maestro, Margaux, Atlas, Isla, Felix)
- `src/tools/` - Custom MCP tools for travel APIs
- `src/utils/` - Utility functions and helpers
- `src/config/` - Configuration management
- `tests/` - All test suites
- `.claude/agents/` - Agent definitions and prompts
- `.claude/skills/` - Reusable skills and patterns
- `data/` - Runtime data, cache, and session storage

## Common Commands
```bash
# Run tests
pytest tests/ -v --cov=src

# Start development server
python src/main.py --dev

# Deploy to staging
./scripts/deployment/deploy_staging.sh

# Run linting
ruff check src/
black src/ --check

# Format code
black src/
```

## API Endpoints (Once FastAPI backend is built)
- `POST /api/flights/search` - Search for flights
- `POST /api/hotels/search` - Search for hotels
- `POST /api/packages/search` - Search for vacation packages
- `POST /api/bookings/create` - Create new booking
- `GET /api/bookings/{id}` - Retrieve booking details
- `POST /api/chat` - Chat with travel agent

## Important Notes
- **Never commit API keys to git** - Use environment variables
- **Always test in staging before production** - No exceptions
- **Keep CLAUDE.md updated** - Document architectural changes
- **Rate limit awareness** - Respect API limits (100 req/min for Downtown Travel)
- **Error handling** - Always implement proper retry logic with exponential backoff
- **Data privacy** - PII must be encrypted at rest and in transit

## Current Development Phase
POC Development - Building core agent framework and API integrations

## Future Roadmap
1. Complete POC with all 5 agents
2. Build FastAPI backend
3. Deploy backend to cloud (AWS/GCP)
4. Develop iOS app (SwiftUI)
5. Production launch

## Team Contacts
- Product Lead: TBD
- Technical Lead: TBD
- API Integration: TBD
