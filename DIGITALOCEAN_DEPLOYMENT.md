# DigitalOcean Deployment Guide for GeckoJump

## Prerequisites

1. **DigitalOcean Account** - Sign up at [digitalocean.com](https://digitalocean.com)
2. **GitHub Repository** - Push your code to GitHub
3. **Domain (Optional)** - You can use the default DigitalOcean domain or connect your own

## Step-by-Step Deployment

### 1. Prepare Your Repository

Make sure your code is pushed to GitHub with these files:
- `app_new.py` (main application)
- `requirements.txt`
- `Procfile`
- `runtime.txt`
- `.do/app.yaml` (optional, for advanced config)
- All your game files and templates

### 2. Create DigitalOcean App

1. **Login to DigitalOcean**
   - Go to [cloud.digitalocean.com](https://cloud.digitalocean.com)
   - Navigate to "Apps" in the sidebar

2. **Create New App**
   - Click "Create App"
   - Choose "GitHub" as source
   - Connect your GitHub account if not already connected
   - Select your repository
   - Choose the branch (usually `main`)

3. **Configure App Settings**
   - **App Name**: `geckojump` (or your preferred name)
   - **Source Directory**: `/` (root directory)
   - **Build Command**: Leave empty (not needed for Python)
   - **Run Command**: `python app_new.py`

### 3. Environment Variables

In the DigitalOcean App settings, add these environment variables:

```
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=False
HOST=0.0.0.0
PORT=5000
ALLOWED_ORIGINS=https://your-app-name.ondigitalocean.app
```

**Important**: 
- Generate a secure `SECRET_KEY` (you can use: `python -c "import secrets; print(secrets.token_hex(32))"`)
- Replace `your-app-name` with your actual DigitalOcean app name

### 4. Instance Configuration

- **Instance Size**: `Basic XXS` (cheapest option, good for testing)
- **Instance Count**: `1` (can scale up later)
- **HTTP Port**: `5000`

### 5. Deploy

1. Click "Create Resources"
2. DigitalOcean will build and deploy your app
3. This process takes 5-10 minutes
4. You'll get a URL like: `https://your-app-name.ondigitalocean.app`

### 6. Custom Domain (Optional)

If you have a custom domain:

1. **Add Domain in DigitalOcean**
   - Go to your app settings
   - Add your domain (e.g., `geckojump.com`)

2. **Update DNS Records**
   - Point your domain's A record to DigitalOcean's IP
   - Or use CNAME to point to your app's DigitalOcean URL

3. **Update Environment Variables**
   - Update `ALLOWED_ORIGINS` to include your custom domain

## Configuration Files Explained

### `Procfile`
```
web: python app_new.py
```
Tells DigitalOcean how to run your app.

### `runtime.txt`
```
python-3.10.12
```
Specifies the Python version to use.

### `requirements.txt`
Lists all Python dependencies. Already configured with:
- Flask and Flask-SocketIO for the web framework
- Eventlet for WebSocket support
- Other dependencies for your games

### `.do/app.yaml` (Optional)
Advanced configuration file for more control over deployment settings.

## Post-Deployment Checklist

- [ ] App loads successfully at the DigitalOcean URL
- [ ] Homepage shows the typewriter effect
- [ ] Games page displays MysticGrid card
- [ ] MysticGrid game is playable
- [ ] WebSocket connections work (test multiplayer)
- [ ] Custom domain works (if configured)
- [ ] HTTPS is enabled (automatic with DigitalOcean)

## Troubleshooting

### Common Issues

1. **App Won't Start**
   - Check the logs in DigitalOcean dashboard
   - Verify `app_new.py` is the correct entry point
   - Ensure all dependencies are in `requirements.txt`

2. **WebSocket Issues**
   - Verify `ALLOWED_ORIGINS` includes your domain
   - Check that `eventlet` is in requirements.txt

3. **Static Files Not Loading**
   - Ensure static files are in the correct directories
   - Check file paths in templates

4. **Games Not Loading**
   - Verify the games directory structure is correct
   - Check that all game files are committed to Git

### Monitoring

- **Logs**: Available in DigitalOcean dashboard under "Runtime Logs"
- **Metrics**: Monitor CPU, memory, and request metrics
- **Alerts**: Set up alerts for downtime or high resource usage

## Scaling

Once your app is successful:

1. **Increase Instance Size**: Upgrade from Basic XXS to larger sizes
2. **Add More Instances**: Scale horizontally for more traffic
3. **Add Database**: Consider adding a managed database for persistent data
4. **CDN**: Use DigitalOcean Spaces for static file delivery

## Cost Estimation

- **Basic XXS**: ~$5/month
- **Basic XS**: ~$12/month
- **Basic S**: ~$24/month

Start with Basic XXS and scale up as needed.

## Security Notes

- ✅ Secret key is properly configured
- ✅ Debug mode is disabled in production
- ✅ CORS is properly configured
- ⚠️ Consider adding rate limiting for production
- ⚠️ Add input validation for user inputs
- ⚠️ Consider adding authentication if needed

Your app is now ready for production deployment! 🚀
