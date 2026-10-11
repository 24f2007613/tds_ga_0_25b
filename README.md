# eShopCo latency endpoint (Vercel)

## Deploy
1. Put this folder in a GitHub repository.
2. Import the repository at https://vercel.com/new.
3. Deploy with the default settings (Python serverless function).
4. Your endpoint will be `https://YOUR-DEPLOYMENT.vercel.app/api`.

## Test (Windows CMD)
```cmd
curl.exe -i -X POST https://YOUR-DEPLOYMENT.vercel.app/api ^
  -H "Content-Type: application/json" ^
  -d "{\"regions\":[\"apac\",\"amer\"],\"threshold_ms\":186}"
```

The JSON response has a `results` array. Each result includes `region`,
`avg_latency`, `p95_latency`, `avg_uptime`, and `breaches`.

The handler supports POST and CORS preflight OPTIONS requests. It uses the
provided `data/telemetry.json` sample bundle.
