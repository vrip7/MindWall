# MindWall — Dashboard Dockerfile
# Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci --production=false

# Copy source
COPY . .

EXPOSE 4297

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
