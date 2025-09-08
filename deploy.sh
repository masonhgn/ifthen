#!/bin/bash

# GeckoJump DigitalOcean Deployment Script

echo "🦎 GeckoJump Deployment Script"
echo "================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Please initialize git first:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    exit 1
fi

# Check if remote origin is set
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "❌ No GitHub remote found. Please add your GitHub repository:"
    echo "   git remote add origin https://github.com/yourusername/geckojump.git"
    exit 1
fi

# Generate a secure secret key
echo "🔑 Generating secure secret key..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
echo "Generated SECRET_KEY: $SECRET_KEY"
echo ""

# Create .env file for local development
echo "📝 Creating .env file for local development..."
cat > .env << EOF
SECRET_KEY=$SECRET_KEY
DEBUG=True
HOST=0.0.0.0
PORT=5000
ALLOWED_ORIGINS=http://localhost:5000,http://127.0.0.1:5000
EOF

echo "✅ Created .env file"
echo ""

# Check if all required files exist
echo "🔍 Checking required files..."
REQUIRED_FILES=("app_new.py" "requirements.txt" "Procfile" "runtime.txt")
MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    echo "❌ Missing required files:"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    exit 1
fi

echo "✅ All required files present"
echo ""

# Show deployment checklist
echo "📋 Deployment Checklist:"
echo "1. Push code to GitHub:"
echo "   git add ."
echo "   git commit -m 'Ready for deployment'"
echo "   git push origin main"
echo ""
echo "2. Go to DigitalOcean App Platform:"
echo "   https://cloud.digitalocean.com/apps"
echo ""
echo "3. Create new app from GitHub repository"
echo ""
echo "4. Set environment variables:"
echo "   SECRET_KEY=$SECRET_KEY"
echo "   DEBUG=False"
echo "   HOST=0.0.0.0"
echo "   PORT=5000"
echo "   ALLOWED_ORIGINS=https://your-app-name.ondigitalocean.app"
echo ""
echo "5. Deploy and test!"
echo ""
echo "🎉 Ready for deployment!"
