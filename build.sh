#!/bin/bash
apt-get update -y
apt-get install -y wget unzip xvfb libxi6 libgconf-2-4

# Instalar Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
apt-get update -y
apt-get install -y google-chrome-stable

# Instalar ChromeDriver
CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
wget -O chromedriver.zip "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$(curl -s https://googlechromelabs.github.io/chrome-for-testing/known-good-versions.json | jq -r '.versions[] | select(.version | startswith("'$CHROME_VERSION'")) | .downloads.chrome[0].url' | head -1 | cut -d'/' -f5)/linux64/chromedriver-linux64.zip"
unzip chromedriver.zip
mv chromedriver-linux64/chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

pip install -r requirements.txt
