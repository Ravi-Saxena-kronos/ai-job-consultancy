# How to check Vercel build and runtime logs

## Build failed

1. Open [vercel.com](https://vercel.com) → your project **ai-job-consultancy**.
2. Click **Deployments**.
3. Click the **failed** deployment (red dot).
4. Open the **Building** tab — scroll to the **bottom** for the red `Error:` line.
5. Copy that block when asking for help.

## CLI (optional)

```bash
npm i -g vercel
cd ai-job-consultancy
vercel login
vercel link
vercel logs https://ai-job-consultancy.vercel.app --follow
```

Runtime errors (register, sheet, email):

1. **Deployments** → latest **Ready** deployment.
2. **Functions** → select **api/index** (or legacy path name).
3. **Logs** tab — reproduce the error, refresh logs.

## Project settings that must match this repo

| Setting | Value |
|---------|--------|
| Framework | **Other** |
| Install Command | **empty** |
| Build Command | **empty** |
| Root Directory | `.` (repo root) |
