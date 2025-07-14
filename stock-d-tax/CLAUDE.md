# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stock D-TAX is a Korean stock investment tax calculation and AI chatbot service with a monorepo structure containing separate frontend and backend applications.

## Architecture

- **Frontend**: Next.js React application (`apps/web/`)
- **Backend**: Node.js Express API server (`apps/api/`)
- **Communication**: WebSocket for real-time stock price updates
- **AI Integration**: OpenAI API for tax consultation chatbot with RAG implementation

## Development Commands

### Frontend (apps/web/)
```bash
cd apps/web
npm install          # Install dependencies
npm run dev          # Start development server (port 3000)
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

### Backend (apps/api/)
```bash
cd apps/api
npm install          # Install dependencies
npm run dev          # Start development server with nodemon (port 4000)
npm run start        # Start production server
```

## Environment Setup

Backend requires OpenAI API key configuration:
```bash
cd apps/api
cp config.env .env
# Edit .env to add: OPENAI_API_KEY=your_openai_api_key_here
```

## Key Architecture Components

### API Routes Structure
- `/api/tax/*` - Tax calculation endpoints
- `/api/chatbot/*` - AI chatbot message processing
- WebSocket connection for real-time price updates (Samsung Electronics: 005930)

### Frontend Page Structure
- `/` - Main dashboard with portfolio chart
- `/assets/` - Asset management dashboard
- `/tax` - Tax calculation interface
- `/chatbot` - AI tax consultation chat interface

### Data Flow
1. Real-time stock data via WebSocket (5-second intervals)
2. Tax calculations processed server-side
3. AI chatbot uses RAG with `taxKnowledgeBase` in `openaiService.js`
4. Chart.js for portfolio visualization

### Key Services
- `stockApi.js` - External stock price API integration
- `openaiService.js` - AI chatbot logic with tax knowledge base
- `taxController.js` - Tax calculation business logic

## Extension Points

### Adding Tax Knowledge
Extend the `taxKnowledgeBase` array in `apps/api/services/openaiService.js` to add new tax consultation topics.

### Stock Data Integration
Modify `apps/api/services/stockApi.js` to integrate with real stock market APIs.

### New Asset Types
Add components in `apps/web/components/assets/` for new investment account types.