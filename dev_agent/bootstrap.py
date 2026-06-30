"""
Bootstrap — create minimal Next.js + Sequelize scaffold when package.json is missing.
"""

from pathlib import Path
from utils import log

PACKAGE_JSON = """{
  "name": "ngo-donation-app",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "sequelize": "^6.37.0",
    "pg": "^8.11.3",
    "pg-hstore": "^2.3.4",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.2",
    "zod": "^3.22.4",
    "nodemailer": "^6.9.7"
  },
  "devDependencies": {
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.35",
    "autoprefixer": "^10.4.17",
    "eslint": "^8.57.0",
    "eslint-config-next": "^14.2.0"
  }
}
"""

NEXT_CONFIG = """/** @type {import('next').NextConfig} */
const nextConfig = {};

module.exports = nextConfig;
"""

TAILWIND_CONFIG = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,jsx}',
    './components/**/*.{js,jsx}',
  ],
  theme: { extend: {} },
  plugins: [],
};
"""

POSTCSS_CONFIG = """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""

GLOBALS_CSS = """@tailwind base;
@tailwind components;
@tailwind utilities;
"""

LAYOUT_JS = """import './globals.css';

export const metadata = {
  title: 'NGO Donation Management',
  description: 'Donation management system for NGOs',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">{children}</body>
    </html>
  );
}
"""

PAGE_JS = """export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-3xl font-bold">NGO Donation Management</h1>
      <p className="mt-4 text-gray-600">DevAgent scaffold — building features from FEATURES.md</p>
    </main>
  );
}
"""

DB_JS = """import { Sequelize } from 'sequelize';

const globalForDb = globalThis;

function createSequelize() {
  const url = process.env.DATABASE_URL;
  if (!url) {
    return null;
  }
  return new Sequelize(url, {
    dialect: 'postgres',
    logging: false,
    dialectOptions: process.env.NODE_ENV === 'production'
      ? { ssl: { require: true, rejectUnauthorized: false } }
      : {},
  });
}

const sequelize = globalForDb.sequelize ?? createSequelize();

if (process.env.NODE_ENV !== 'production' && sequelize) {
  globalForDb.sequelize = sequelize;
}

export default sequelize;
"""

ENV_EXAMPLE = """DATABASE_URL=postgresql://user:pass@localhost:5432/ngo
JWT_SECRET=replace-with-long-random-string
JWT_EXPIRES_IN=7d
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USER=ngo@gmail.com
EMAIL_PASS=gmail-app-password
"""

JSConfig = """{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]
    }
  }
}
"""


def ensure_scaffold(repo_root: Path) -> bool:
    """Create minimal Next.js app if package.json does not exist. Returns True if created."""
    if (repo_root / "package.json").exists():
        return False

    log("Bootstrap: creating Next.js + Sequelize scaffold...")
    files = {
        "package.json":       PACKAGE_JSON,
        "next.config.js":     NEXT_CONFIG,
        "tailwind.config.js": TAILWIND_CONFIG,
        "postcss.config.js":  POSTCSS_CONFIG,
        "jsconfig.json":      JSConfig,
        ".env.example":       ENV_EXAMPLE,
        "app/globals.css":    GLOBALS_CSS,
        "app/layout.js":      LAYOUT_JS,
        "app/page.js":        PAGE_JS,
        "lib/db.js":          DB_JS,
    }

    for rel, content in files.items():
        path = repo_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    for d in ("models", "services", "components", "hooks"):
        (repo_root / d).mkdir(exist_ok=True)
        gitkeep = repo_root / d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("")

    log("Bootstrap: scaffold created")
    return True
