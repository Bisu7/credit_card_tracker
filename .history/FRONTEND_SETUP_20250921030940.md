# Deep Researcher Frontend Setup Guide

This guide will help you set up and run the complete Deep Researcher system with both backend and frontend.

## 🎯 Overview

The Deep Researcher now includes a modern React frontend that provides a Perplexity-like interface for conducting AI-powered research. The system consists of:

- **Backend**: FastAPI server with AI research capabilities
- **Frontend**: React TypeScript application with modern UI
- **Integration**: Seamless communication between frontend and backend

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

1. **Start the complete system:**
   ```bash
   python start_full_system.py
   ```
   This will start both the backend API server and React frontend automatically.

### Option 2: Manual Setup

1. **Start the backend:**
   ```bash
   python api_server.py
   ```

2. **In a new terminal, start the frontend:**
   ```bash
   python start_frontend.py
   ```

## 📋 Prerequisites

### Backend Requirements
- Python 3.8+
- All dependencies from `requirements.txt` installed
- Backend should be running on `http://localhost:8000`

### Frontend Requirements
- Node.js 16+ ([Download here](https://nodejs.org/))
- npm (comes with Node.js)

## 🔧 Detailed Setup

### 1. Backend Setup

Ensure your backend is properly set up:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the backend server
python api_server.py
```

The backend should be running on `http://localhost:8000`.

### 2. Frontend Setup

Navigate to the frontend directory and install dependencies:

```bash
cd frontend
npm install
```

Start the development server:

```bash
npm start
```

The frontend will be available at `http://localhost:3000`.

## 🎨 Frontend Features

### Core Components

1. **Search Interface**
   - Perplexity-style search bar
   - Real-time query suggestions
   - Example queries for guidance

2. **Results Display**
   - Markdown rendering with syntax highlighting
   - Source citations with expandable content
   - Confidence scores and execution metrics
   - Copy, export, and share functionality

3. **Document Upload**
   - Drag-and-drop file upload
   - Support for multiple formats (PDF, DOC, TXT, etc.)
   - Progress tracking and error handling

4. **Session Management**
   - Session creation and management
   - Query history tracking
   - Session statistics
   - Re-run previous queries

### UI Features

- **Dark/Light Theme**: Toggle between themes
- **Responsive Design**: Works on all devices
- **Modern Animations**: Smooth transitions and loading states
- **Accessibility**: Keyboard navigation and screen reader support

## 🔗 API Integration

The frontend communicates with the backend through these endpoints:

- `POST /research` - Conduct research on a query
- `POST /suggest` - Get query suggestions
- `POST /ingest` - Upload documents
- `GET /status` - System status
- `GET /health` - Health check

## 🛠️ Development

### Project Structure

```
frontend/
├── public/                 # Static files
├── src/
│   ├── components/         # React components
│   │   ├── Header.tsx
│   │   ├── SearchInterface.tsx
│   │   ├── ResultsDisplay.tsx
│   │   ├── DocumentUpload.tsx
│   │   └── SessionHistory.tsx
│   ├── contexts/          # React contexts
│   │   ├── ThemeContext.tsx
│   │   ├── SessionContext.tsx
│   │   └── ApiContext.tsx
│   ├── App.tsx            # Main app
│   └── index.tsx          # Entry point
├── package.json           # Dependencies
├── tailwind.config.js     # Tailwind config
└── tsconfig.json          # TypeScript config
```

### Available Scripts

```bash
npm start          # Start development server
npm run build      # Build for production
npm test           # Run tests
npm run eject      # Eject from Create React App
```

### Customization

#### Styling
- Edit `src/index.css` for global styles
- Modify `tailwind.config.js` for theme customization
- Update component styles in individual `.tsx` files

#### API Configuration
- Change API URL in `src/contexts/ApiContext.tsx`
- Add new endpoints as needed

#### Adding New Features
1. Create new components in `src/components/`
2. Add new contexts in `src/contexts/` if needed
3. Update routing in `src/App.tsx`
4. Add new API methods in `src/contexts/ApiContext.tsx`

## 🚀 Deployment

### Frontend Deployment

1. **Build the project:**
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy the `build` folder** to your hosting service:
   - Vercel
   - Netlify
   - AWS S3
   - Any static hosting service

### Backend Deployment

Deploy the FastAPI backend to your preferred platform:
- Heroku
- AWS
- Google Cloud
- DigitalOcean

### Environment Configuration

Create environment variables for production:

**Frontend (.env):**
```env
REACT_APP_API_URL=https://your-backend-api.com
```

**Backend:**
Update CORS settings in `api_server.py` to allow your frontend domain.

## 🐛 Troubleshooting

### Common Issues

1. **Frontend won't start:**
   - Check Node.js version: `node --version`
   - Clear npm cache: `npm cache clean --force`
   - Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

2. **API connection failed:**
   - Ensure backend is running on port 8000
   - Check CORS settings in `api_server.py`
   - Verify API URL in frontend configuration

3. **Build errors:**
   - Check TypeScript errors: `npm run build`
   - Ensure all dependencies are installed
   - Clear build cache: `rm -rf build`

### Debug Mode

Enable debug mode by setting:
```env
REACT_APP_DEBUG=true
```

## 📚 Additional Resources

- [React Documentation](https://reactjs.org/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)

## 🤝 Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Test components thoroughly
4. Update documentation as needed

## 📄 License

This project is part of the Deep Researcher system.
