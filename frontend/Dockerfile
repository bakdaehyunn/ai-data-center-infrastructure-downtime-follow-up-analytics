FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_SEMANTIC_API_BASE_URL=http://127.0.0.1:18080
ENV VITE_SEMANTIC_API_BASE_URL=$VITE_SEMANTIC_API_BASE_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
