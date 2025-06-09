# Vercel Deployment for AI Checkout Automation

This document explains how to deploy the AI Checkout Automation backend to Vercel.

## Prerequisites

1. A Vercel account (sign up at [vercel.com](https://vercel.com))
2. Vercel CLI (optional but recommended)
3. Google AI API Key for Gemini

## Deployment Steps

### Option 1: Deploy with Vercel CLI (Recommended)

1. **Install Vercel CLI:**

```bash
npm install -g vercel
```

2. **Log in to Vercel:**

```bash
vercel login
```

3. **Navigate to the project directory:**

```bash
cd path/to/checkout_automation
```

4. **Deploy to Vercel:**

```bash
vercel
```

5. **Follow the CLI prompts:**
   - When asked about settings, choose to use the existing `vercel.json` configuration
   - Set the environment variables when prompted, especially `GOOGLE_API_KEY`

### Option 2: Deploy via Vercel Dashboard

1. **Push your code to a Git provider** (GitHub, GitLab, or Bitbucket)

2. **Import your repository in Vercel:**
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "Add New" → "Project"
   - Select your repository from the list

3. **Configure project:**
   - Keep the default framework preset (or select "Other")
   - Expand "Environment Variables" and add:
     - `GOOGLE_API_KEY`: Your Google AI API key for Gemini

4. **Deploy:**
   - Click "Deploy"

## Updating the Browser Extension

After deploying to Vercel, you'll need to update your browser extension to use the new API endpoint:

1. **Get your Vercel deployment URL** (e.g., `https://your-project-name.vercel.app`)

2. **Update the extension's API endpoint:**
   - Open `background.js` in your extension code
   - Find the API endpoint configuration (likely a variable like `BACKEND_URL` or similar)
   - Replace the local URL (`http://localhost:5000`) with your Vercel deployment URL

3. **Test the extension** with the new API endpoint

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google AI API Key for Gemini | Yes |

## Troubleshooting

If you encounter issues with your Vercel deployment:

1. **Check Vercel Logs:**
   - Go to your project in the Vercel dashboard
   - Click on the latest deployment
   - Select "Functions" and look for error messages

2. **API Key Issues:**
   - Verify that your Google AI API key is correctly set in the environment variables
   - Make sure the API key has access to Gemini AI

3. **Deployment Failures:**
   - Check the Python dependencies in `requirements.txt`
   - Ensure all necessary files are included in the deployment
