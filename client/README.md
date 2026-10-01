# NeuroScribe Client

The active NeuroScribe web application is a React + TypeScript single-page application built with Vite.

## Commands

~~~bash
npm ci
npm run dev
npm run build
npm run lint
npm run preview
~~~

Copy .env.example to .env for local configuration.

The frontend communicates with the FastAPI backend through VITE_API_URL and uses bearer-token authentication for protected clinical routes.

See the repository docs/development.md and docs/architecture.md.
