# Cloud Hosting Guide

## Option 1: Streamlit Community Cloud (FREE - Recommended)

**Best for:** Quick deployment, no server management

### Steps:
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Select `app.py` as the main file
5. Click "Deploy" → Live in ~2 minutes!

**Limitations:** Public repos only (free tier), 1GB RAM

---

## Option 2: Railway (FREE Tier)

### Steps:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Or connect GitHub repo at [railway.app](https://railway.app)

**Free tier:** 500 hours/month, 512MB RAM

---

## Option 3: Render (FREE Tier)

### Steps:
1. Push to GitHub
2. Go to [render.com](https://render.com)
3. New → Web Service → Connect repo
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

**Free tier:** 750 hours/month, auto-sleep after 15 min inactivity

---

## Option 4: Fly.io (FREE Tier)

### Steps:
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Deploy
fly auth login
fly launch
fly deploy
```

**Free tier:** 3 shared VMs, 256MB RAM each

---

## Option 5: Azure App Service

### Steps:
```bash
# Install Azure CLI
az login

# Create and deploy
az webapp up --name messenger-app --runtime "PYTHON:3.11" --sku F1
```

**Free tier (F1):** 60 min CPU/day, 1GB storage

---

## Option 6: Google Cloud Run

### Steps:
1. Create `Dockerfile` (see below)
2. Deploy:
```bash
gcloud run deploy messenger --source . --allow-unauthenticated
```

**Free tier:** 2 million requests/month

---

## Option 7: AWS (Elastic Beanstalk or Lightsail)

### Lightsail (Simplest):
- $3.50/month for smallest instance
- Go to [lightsail.aws.amazon.com](https://lightsail.aws.amazon.com)
- Create instance → Choose OS → Upload files → Run

---

## Docker Deployment (Works Anywhere)

Use this Dockerfile for any container platform:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
```

Build and run:
```bash
docker build -t messenger .
docker run -p 8501:8501 messenger
```

---

## Quick Comparison

| Platform | Setup Time | Free Tier | Custom Domain | Auto-Deploy |
|----------|------------|-----------|---------------|-------------|
| Streamlit Cloud | 2 min | ✅ Yes | ✅ Yes | ✅ Yes |
| Railway | 5 min | ✅ 500h/mo | ✅ Yes | ✅ Yes |
| Render | 5 min | ✅ 750h/mo | ✅ Yes | ✅ Yes |
| Fly.io | 10 min | ✅ 3 VMs | ✅ Yes | ✅ Yes |
| Azure | 10 min | ✅ 60 min/day | ✅ Yes | ✅ Yes |
| Google Cloud Run | 15 min | ✅ 2M req/mo | ✅ Yes | ✅ Yes |
| AWS Lightsail | 15 min | ❌ $3.50/mo | ✅ Yes | ❌ Manual |

---

## My Recommendation

**For testing/personal use:** Streamlit Cloud (free, 2-minute setup)

**For production:** Railway or Render (free tier, more control)

**For enterprise:** Azure App Service or AWS
