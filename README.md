# Installation Guide

1. Install **Ollama**
2. Pull your desired LLM with multiple image uploads capability to Ollama
3. Install **Firefox**
4. Install **Geckodriver**  
    - Follow this guide: [Geckodriver Selenium Python - BrowserStack](https://www.browserstack.com/guide/geckodriver-selenium-python)  
5. Install **Python 3.11**  
6. Install dependencies from `requirements.txt`  

# Running Guide

1. Fill **task** and **task_link** with the name of the task and link to the task in taiga in `metabase_live.csv`
2. Fill your credentials in `creds.py`
3. Serve your model using **Ollama**
4. Run `main.py` along with the amount of test cases you want the LLM to generate from the list (Example: "python main.py 3" will generate 3 test cases from 3 task from `metabase_live.csv`).
