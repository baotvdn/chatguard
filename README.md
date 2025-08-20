# ChatGuard

A Django chatbot application with safety monitoring and compliance tracking, powered by LangGraph and Claude AI.

## Features

- **Interactive Web Chatbot**: Clean Django-based interface with real-time chat
- **Safety Monitoring**: Built-in compliance checking and safety event tracking
- **LangGraph Integration**: Advanced conversation flow management
- **User Authentication**: Secure registration and login system
- **Session Management**: Persistent conversation history

## Quick Start

### Prerequisites
- Python 3.13+
- uv package manager

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd chatguard
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up environment variables in `.env`:
   ```env
   DJANGO_SECRET_KEY=your-secret-key-here
   ANTHROPIC_API_KEY=your-anthropic-api-key-here
   ```

4. Run database migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

6. Visit http://127.0.0.1:8000/ to use the chatbot

## Development

### Code Quality
- `ruff check .` - Run linting checks
- `ruff format .` - Apply code formatting
- `ruff check --fix .` - Auto-fix linting issues

### Project Structure
- `config/` - Django project configuration
- `chatbot/` - Main chatbot application
- `main.py` - Legacy CLI chatbot (standalone)

## Security

**Important**: Always set environment variables in production:
- `DJANGO_SECRET_KEY` - Required for Django security
- `ANTHROPIC_API_KEY` - Required for Claude AI integration

## Technology Stack

- **Backend**: Django 5.2+
- **AI**: LangGraph + Anthropic Claude 3.5 Sonnet
- **Package Management**: uv
- **Code Quality**: Ruff (linting & formatting)
- **Database**: SQLite (development), configurable for production
