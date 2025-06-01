# AIRev
AIRev – Auto Reverse IP using Gemini AI for automatic keyword generation and Google Search to fetch IPs. This script is used to get a bulk domain list. To use this tool, you need to set up the **Google Custom Search API** and **Gemini AI** and obtain an **API Key** and **Custom Search Engine ID (CSE ID)**.
### Tools and components required
- VPS or RDP (OPTIONAL), Get free $200 credit [DigitalOcean](https://m.do.co/c/3f132e0f7e13) for 60 days here: [Register](https://m.do.co/c/3f132e0f7e13)
- Rotating Proxies for bypass Rate Limit. You can buy at [here](https://proxyscrape.com/?ref=odk1mmj) or [here](https://app.proxy-cheap.com/r/JysUiH)
- Python version 3.10 or Latest
## Setup Tutorial
#### 1. Create a Google Cloud Project
- Visit the [Google Cloud Console](https://console.cloud.google.com/).
- Click **"New Project"**, give it a name (e.g., `My Project`), and create the project.
#### 2. Enable Custom Search API
- In the Cloud Console, navigate to: `APIs & Services > Library`.
- Search for **"Custom Search API"** and click **Enable**.
- Search for **"Gemini API"** and click **Enable**.
#### 3. Generate an API Key
- Go to: `APIs & Services > Credentials`.
- Click **"Create Credentials" > "API Key"**.
- Copy and save the generated **API Key**.
#### 4. Create a Custom Search Engine (CSE)
- Visit [Google Programmable Search Engine](https://programmablesearchengine.google.com/).
- Click **"New Search Engine"**, set it to search the **Entire Web**, and create it.
- Go to `Edit search engine > Setup`, and copy the **Search engine ID (CSE ID)**.
## Installation 
#### 1. Install Python
- Install Python For Windows: [Python](https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe)
- For Unix:
```bash
apt install python3 python3-pip git -y
```
#### 2. Download tool
- Download tool [Manually](https://github.com/im-hanzou/AIRev/archive/refs/heads/main.zip) or use git:
```bash
git clone https://github.com/im-hanzou/AIRev
```
#### 3. Install requirements
- Make sure you already in tool folder:
```bash
cd AIRev
```
- Install requirements
```bash
python -m pip install -r requirements.txt
```
#### 4. Run the tool
- Open and edit `.env` file with your **YOUR_GOOGLE_CONSOLE_API_KEY**, **YOUR_CSE_ID** and your **Proxy**, example :
```bash
API_KEY=AIzaSyBbQjuKw57XXXXXXX
CSE_ID=e19764fxxxxxxx
PROXY_URL=http://your:proxy@ip:port
```
- Run the tool :
```bash
python main.py
```
## 📌 Notes
- You can just run this tool at **your own risk**, **I'm not responsible for any loss or damage caused by this tool**.
- This tool is for **educational** purposes only.
- The API has a **free quota of 100 queries per day**. If exceeded, billing needs to be enabled.
- Keep your **API Key** and **CSE ID** secure – **do not share them publicly**.
