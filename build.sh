#!/bin/bash
set -e
apt-get install -y wkhtmltopdf fonts-noto-core
pip install -r requirements.txt
# Download NotoSansBengali
python3 -c "
import urllib.request
url = 'https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansBengali/NotoSansBengali-Regular.ttf'
urllib.request.urlretrieve(url, 'NotoSansBengali-Regular.ttf')
print('Font downloaded')
"
