FROM node:18 AS build

WORKDIR /jsapp

# Install app dependencies
# A wildcard is used to ensure both package.json AND package-lock.json are copied
# where available (npm@5+)
COPY jsapp/package*.json ./

COPY jsapp/package.json ./
COPY jsapp/package-lock.json ./
RUN npm ci --omit=dev

COPY jsapp/public ./public
COPY jsapp/src ./src
RUN npm run build


FROM python:3.11-slim

WORKDIR /usr/src/app
ENV TZ="Europe/Stockholm"

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=build /jsapp/build ./jsapp/build
COPY pyapp/* ./

EXPOSE 8000
EXPOSE 8008

CMD [ "python", "./main.py" ]
