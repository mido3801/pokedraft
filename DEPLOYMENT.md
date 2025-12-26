# PokeDraft Deployment Guide

Deploy your PokeDraft application using Supabase (database), Fly.io (backend), and Netlify (frontend).

## Prerequisites

- [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/) installed
- [Netlify CLI](https://docs.netlify.com/cli/get-started/) installed (optional)
- A Supabase account
- A Fly.io account
- A Netlify account

## 1. Supabase Setup (Database)

### Create Project
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Choose organization, name your project, set a strong database password
4. Select a region close to your Fly.io region (e.g., `us-west-1` for `sjc`)

### Get Credentials
After project creation, go to **Settings > API**:
- **Project URL**: `https://[YOUR-PROJECT-REF].supabase.co`
- **anon/public key**: For frontend authentication
- **service_role key**: (Keep secret, for backend if needed)

Go to **Settings > Database**:
- **Connection string**: Copy the URI, replace `[YOUR-PASSWORD]` with your database password

### Run Migrations
From your local machine with the database URL:
```bash
cd backend
DATABASE_URL="postgres://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" alembic upgrade head
```

## 2. Fly.io Setup (Backend)

### Install Fly CLI
```bash
# macOS
brew install flyctl

# Or via curl
curl -L https://fly.io/install.sh | sh
```

### Login and Launch
```bash
cd backend

# Login to Fly.io
fly auth login

# Launch the app (first time only)
fly launch --no-deploy

# This will detect the fly.toml and Dockerfile
# Choose a unique app name or accept the generated one
# Select region: sjc (San Jose) or closest to your users
# Don't set up PostgreSQL through Fly (we're using Supabase)
```

### Set Secrets
```bash
# Required secrets
fly secrets set DATABASE_URL="postgres://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
fly secrets set SUPABASE_URL="https://[PROJECT-REF].supabase.co"
fly secrets set SUPABASE_KEY="your-supabase-anon-key"
fly secrets set SUPABASE_JWT_SECRET="your-jwt-secret"
fly secrets set SECRET_KEY="$(openssl rand -hex 32)"
fly secrets set DEV_MODE="false"

# CORS - your Netlify URL (update after deploying frontend)
fly secrets set CORS_ORIGINS="https://your-app.netlify.app"
```

### Deploy
```bash
fly deploy
```

### Verify Deployment
```bash
# Check status
fly status

# View logs
fly logs

# Test health endpoint
curl https://your-app.fly.dev/health
```

## 3. Netlify Setup (Frontend)

### Option A: Deploy via Git (Recommended)
1. Push your code to GitHub/GitLab
2. Go to [Netlify Dashboard](https://app.netlify.com)
3. Click "Add new site" > "Import an existing project"
4. Connect your Git provider and select your repository
5. Configure build settings:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`

### Option B: Deploy via CLI
```bash
cd frontend

# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Initialize (links to a site)
netlify init

# Deploy
npm run build
netlify deploy --prod
```

### Set Environment Variables
In Netlify Dashboard > Site Settings > Environment Variables:

```
VITE_API_URL = https://your-app.fly.dev
VITE_WS_URL = wss://your-app.fly.dev
VITE_SUPABASE_URL = https://[PROJECT-REF].supabase.co
VITE_SUPABASE_ANON_KEY = your-supabase-anon-key
```

**Important**: After setting variables, trigger a redeploy for changes to take effect.

### Update CORS on Fly.io
After getting your Netlify URL, update CORS:
```bash
cd backend
fly secrets set CORS_ORIGINS="https://your-app.netlify.app"
```

## 4. Configure Supabase Auth (Optional)

If using Supabase authentication with OAuth:

1. Go to Supabase Dashboard > Authentication > Providers
2. Enable Google (or other providers)
3. Add OAuth credentials from Google Cloud Console
4. Set redirect URLs:
   - `https://[PROJECT-REF].supabase.co/auth/v1/callback`
   - `https://your-app.netlify.app` (your frontend URL)

## Deployment Checklist

- [ ] Supabase project created
- [ ] Database migrations run on Supabase
- [ ] Fly.io app deployed with secrets set
- [ ] Netlify site deployed with environment variables
- [ ] CORS configured to allow Netlify domain
- [ ] Health check passing on Fly.io
- [ ] Frontend can connect to backend API
- [ ] WebSocket connections working (test draft room)
- [ ] Authentication flow working

## Troubleshooting

### Backend won't start
```bash
fly logs --app your-app
```
Common issues:
- Missing environment variables
- Database connection string format
- Port mismatch (should be 8000)

### CORS errors
Ensure `CORS_ORIGINS` on Fly.io includes your exact Netlify URL (with https://, no trailing slash).

### Database connection fails
- Verify the connection string format
- Ensure password doesn't contain special characters that need URL encoding
- Check if Supabase allows connections from external IPs (default: yes)

### WebSocket not connecting
- Ensure `VITE_WS_URL` uses `wss://` (not `ws://`)
- Check that Fly.io is properly forwarding WebSocket connections

## Updating Your Deployment

### Backend (Fly.io)
```bash
cd backend
fly deploy
```

### Frontend (Netlify)
Push to your connected Git branch, or:
```bash
cd frontend
npm run build
netlify deploy --prod
```

### Database Migrations
```bash
cd backend
DATABASE_URL="your-supabase-url" alembic upgrade head
```

## Cost Estimates

- **Supabase Free Tier**: 500MB database, 2GB bandwidth
- **Fly.io Free Tier**: 3 shared VMs, 160GB bandwidth
- **Netlify Free Tier**: 100GB bandwidth, 300 build minutes

For a hobby project, you can likely stay within free tiers.
