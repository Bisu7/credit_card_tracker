# Frontend Deployment Guide

## 🚀 Deploy Your Deep Researcher Frontend

Your backend is now live at: **https://deepresearch-2fou.onrender.com**

### Option 1: Vercel (Recommended)

1. **Go to [vercel.com](https://vercel.com)**
2. **Sign up/Login** with GitHub
3. **Import Project**:
   - Click "New Project"
   - Import from GitHub: `praveen70444/DeepResearch`
   - **Root Directory**: Select `frontend`
4. **Configure**:
   - Framework Preset: `Create React App`
   - Build Command: `npm run build`
   - Output Directory: `build`
   - Environment Variables:
     - `REACT_APP_API_URL` = `https://deepresearch-2fou.onrender.com`
5. **Deploy!**

### Option 2: Netlify

1. **Go to [netlify.com](https://netlify.com)**
2. **Sign up/Login** with GitHub
3. **New Site from Git**:
   - Connect to GitHub
   - Select repository: `praveen70444/DeepResearch`
   - **Base directory**: `frontend`
4. **Build Settings**:
   - Build command: `npm run build`
   - Publish directory: `frontend/build`
   - Environment Variables:
     - `REACT_APP_API_URL` = `https://deepresearch-2fou.onrender.com`
5. **Deploy!**

### Option 3: GitHub Pages

1. **Install gh-pages**:
   ```bash
   cd frontend
   npm install --save-dev gh-pages
   ```

2. **Update package.json**:
   ```json
   {
     "homepage": "https://praveen70444.github.io/DeepResearch",
     "scripts": {
       "predeploy": "npm run build",
       "deploy": "gh-pages -d build"
     }
   }
   ```

3. **Deploy**:
   ```bash
   npm run deploy
   ```

### Option 4: Render (Static Site)

1. **Go to [render.com](https://render.com)**
2. **New Static Site**
3. **Connect GitHub**: `praveen70444/DeepResearch`
4. **Configure**:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `build`
   - **Environment Variables**:
     - `REACT_APP_API_URL` = `https://deepresearch-2fou.onrender.com`

## 🔧 Manual Deployment Commands

### Build the Frontend Locally:
```bash
cd frontend
npm install
npm run build
```

### Test Locally:
```bash
cd frontend
npm start
```

## ✅ What's Updated:

- ✅ Frontend now points to your deployed backend
- ✅ API calls will go to `https://deepresearch-2fou.onrender.com`
- ✅ All research functionality will work
- ✅ Mock responses will be displayed

## 🎯 Expected Result:

Once deployed, your frontend will:
- ✅ Connect to your live backend
- ✅ Display research results
- ✅ Show suggestions
- ✅ Handle all API interactions

## 🚨 Important Notes:

1. **CORS**: Your backend already has CORS enabled for all origins
2. **Environment**: The frontend will use the deployed backend automatically
3. **HTTPS**: Both frontend and backend will use HTTPS in production
4. **Performance**: The lite backend responds quickly with mock data

Choose your preferred deployment platform and follow the steps above!
