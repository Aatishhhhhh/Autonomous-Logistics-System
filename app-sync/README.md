# AutoDrop app sync

The intended app source is https://github.com/Aasim41/rocar-delivery.

The app is a React + TypeScript + Vite frontend packaged with Capacitor for Android. Its main areas include authentication/onboarding, dashboard, send package, fetch package, order tracking/history, profile, QR scanner, notifications, Supabase SQL/functions, PWA assets and Android wrapper.

The existing Python navigation/API code at the repository root must remain authoritative. Keep the app's bundled Python snapshot isolated under `app-sync/backend-snapshot/` unless and until its endpoint contracts are reconciled with the root backend.

Do not import the source repository's `.env` or `android/app/google-services.json`. Configure local values through `.env.local` or deployment secrets. Before using any SQL, inspect it for destructive DROP statements and test against a disposable Supabase project.

The GitHub connector available in this run can inspect source files, but bulk content/tree writes are currently failing due connector request limits. No claim is made that the full frontend application has been imported yet.