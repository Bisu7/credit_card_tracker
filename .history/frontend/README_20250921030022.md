# Deep Researcher Frontend

A modern React-based frontend for the Deep Researcher AI system, featuring a Perplexity-like interface for conducting AI-powered research.

## Features

- 🔍 **Intelligent Search Interface** - Perplexity-style search with real-time suggestions
- 📄 **Document Upload** - Support for multiple file formats (PDF, DOC, TXT, etc.)
- 🧠 **AI-Powered Research** - Deep analysis with reasoning explanations
- 📊 **Rich Results Display** - Markdown rendering, syntax highlighting, and source citations
- 🌙 **Dark/Light Theme** - Modern UI with theme switching
- 📚 **Session Management** - Track research sessions and query history
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

## Tech Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **React Router** for navigation
- **Axios** for API communication
- **React Hot Toast** for notifications
- **React Markdown** for content rendering
- **React Syntax Highlighter** for code blocks
- **React Dropzone** for file uploads

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Deep Researcher backend running on port 8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

### Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── components/          # React components
│   ├── Header.tsx      # Navigation header
│   ├── SearchInterface.tsx  # Main search component
│   ├── ResultsDisplay.tsx   # Research results display
│   ├── DocumentUpload.tsx   # File upload component
│   └── SessionHistory.tsx   # Session management
├── contexts/           # React contexts
│   ├── ThemeContext.tsx     # Theme management
│   ├── SessionContext.tsx   # Session state
│   └── ApiContext.tsx       # API integration
├── App.tsx             # Main app component
└── index.tsx          # App entry point
```

## Key Components

### SearchInterface
- Perplexity-style search bar with suggestions
- Real-time query refinement
- Example queries for guidance

### ResultsDisplay
- Markdown rendering with syntax highlighting
- Source citations with expandable content
- Confidence scores and execution metrics
- Copy, export, and share functionality

### DocumentUpload
- Drag-and-drop file upload
- Support for multiple file formats
- Progress tracking and error handling
- File management interface

### SessionHistory
- Session creation and management
- Query history tracking
- Session statistics
- Re-run previous queries

## API Integration

The frontend communicates with the FastAPI backend through the following endpoints:

- `POST /research` - Conduct research on a query
- `POST /suggest` - Get query suggestions
- `POST /ingest` - Upload documents
- `GET /status` - System status
- `GET /health` - Health check

## Styling

The UI uses Tailwind CSS with custom components and a design system inspired by Perplexity:

- **Colors**: Primary blue theme with gray neutrals
- **Typography**: Inter font family
- **Components**: Custom button, input, and card styles
- **Animations**: Smooth transitions and loading states
- **Responsive**: Mobile-first design approach

## Development

### Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App

### Code Style

- TypeScript for type safety
- Functional components with hooks
- Context API for state management
- Custom hooks for reusable logic

## Deployment

1. Build the project:
```bash
npm run build
```

2. Deploy the `build` folder to your hosting service.

3. Ensure the backend API is accessible from your frontend domain.

## Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Test components thoroughly
4. Update documentation as needed

## License

This project is part of the Deep Researcher system.
