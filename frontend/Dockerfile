# --- STAGE 1: Build ---
FROM node:20-alpine AS builder

WORKDIR /app

# Kopiere nur package-Dateien (für besseres Caching)
COPY package*.json ./

# Installiere ALLE Abhängigkeiten (auch devDependencies zum Bauen)
RUN npm ci

# Kopiere den Rest des Codes
COPY . .

# Baue die SvelteKit App
RUN npm run build

# Entferne devDependencies, um Platz zu sparen
RUN npm prune --production

# --- STAGE 2: Run ---
FROM node:20-alpine

WORKDIR /app

# Kopiere den fertigen Build aus Stage 1
COPY --from=builder /app/build build/
# Kopiere die production node_modules aus Stage 1
COPY --from=builder /app/node_modules node_modules/
COPY package.json .

# Google Cloud Run injiziert automatisch eine PORT Variable (meist 8080).
# SvelteKit's node-adapter hört automatisch auf process.env.PORT.
# Wir geben nur den Standard an:
ENV PORT=3000
EXPOSE 3000

# Starte den Server
CMD [ "node", "build" ]