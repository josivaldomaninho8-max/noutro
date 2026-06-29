#!/bin/bash
apt-get update -y
apt-get install -y wget unzip xvfb libxi6 libgconf-2-4 jq

# Instalar Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
apt-get update -y
apt-get install -y google-chrome-stable

# Instalar ChromeDriver compatível
CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
CHROME_MAJOR=$(echo $CHROME_VERSION | cut -d. -f1)
wget -O chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip"
unzip chromedriver.zip
mv chromedriver-linux64/chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

pip install -r requirements.txt
