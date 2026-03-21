# Tax Review App

AI-powered macOS application for reviewing tax returns and work papers using Claude.

## Architecture

```
┌─────────────────────┐       ┌─────────────────────┐       ┌──────────────┐
│  SwiftUI macOS App  │──────▶│  FastAPI Backend     │──────▶│  Claude API  │
│  (Frontend)         │◀──────│  (Python)            │◀──────│  (Anthropic) │
└─────────────────────┘       └─────────────────────┘       └──────────────┘
                                       │
                              ┌────────┴────────┐
                              │ Document        │
                              │ Processing      │
                              │ (PDF/Excel/IMG) │
                              └─────────────────┘
```

## Features

- **Document Upload**: Drag-and-drop PDF, Excel, CSV, and image files
- **AI Review**: Claude analyzes tax documents for errors, omissions, and compliance issues
- **Issue Tracking**: Categorized issues with severity levels (High/Medium/Low/Info)
- **Document Comparison**: Compare multiple documents for discrepancies
- **Report Generation**: Generate comprehensive review reports
- **Scanned Document Support**: Vision-based analysis for scanned/image documents

## Quick Start

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

Open `frontend/TaxReviewApp.swiftpm` in Xcode (requires macOS 14+ and Xcode 15+).

Build and run the app. It connects to `http://localhost:8000` by default (configurable in Settings).

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload a tax document |
| GET | `/api/documents/` | List all documents |
| GET | `/api/documents/{id}` | Get document details |
| DELETE | `/api/documents/{id}` | Delete a document |
| POST | `/api/reviews/review` | Review a document with Claude |
| GET | `/api/reviews/` | List all reviews |
| GET | `/api/reviews/{id}` | Get review details |
| PATCH | `/api/reviews/{id}/issues/{issue_id}/resolve` | Mark issue resolved |
| POST | `/api/reviews/compare` | Compare multiple documents |
| POST | `/api/reviews/report` | Generate a review report |

## Supported Document Types

- **PDF** — Digital and scanned tax returns, schedules, work papers
- **Excel (.xlsx)** — Work papers, trial balances, reconciliations
- **CSV** — Data exports, transaction lists
- **Images (PNG, JPG, TIFF)** — Scanned documents, receipts
