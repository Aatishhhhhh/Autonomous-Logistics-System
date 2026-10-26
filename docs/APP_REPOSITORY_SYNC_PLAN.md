# AutoDrop App Integration Plan

Source app: https://github.com/Aasim41/rocar-delivery

The React/Vite/TypeScript app, Capacitor wrapper, Supabase schema/functions, branding assets and embedded backend snapshot are to be integrated into this repository while preserving the existing Python robot backend at the repository root.

## Required handling
- Do not copy the source repository's `.env` or the Android `google-services.json`.
- The app frontend uses `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`; populate these from your own project in a local environment file.
- The app's current `src/lib/backendApi.ts` targets the hosted cart API. Keep this endpoint configurable and verify compatibility with the Python API already in this repository before assuming end-to-end integration.
- `backend/autonomous-cart-main` is an additional backend snapshot from the app repository; it is kept separate from the root backend to prevent import/path collisions while the two implementations are reviewed.
- Supabase schema scripts include destructive DROP statements. Review schema changes and back up any existing project before applying SQL.
- Capacitor / Android build and deployment need local environment configuration and build verification.

## Next validation
1. Install frontend packages with npm ci.
2. Run npm run build.
3. Configure the Python service dependencies separately.
4. Verify login, QR scanning, package creation, fetch, live tracking, notifications and backend control endpoints against a development Supabase project and a development robot API before deployment.
