FROM node:latest
COPY ./ /app
WORKDIR /app
RUN npm install /app
EXPOSE 5173:5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]