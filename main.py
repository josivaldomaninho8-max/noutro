import time
import logging
import schedule
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from telegram import Bot

# --- CONFIGURACOES ---
TELEGRAM_TOKEN = "8730616898:AAFo4A7ooNt1mjmAduemWWDLez38uumltzo"
CHAT_ID = "@Lukevan_bot"
USERNAME = "925959236"
PASSWORD = "Senhas.925"

# --- SETUP TELEGRAM ---
bot = Bot(token=TELEGRAM_TOKEN)

# --- SETUP SELENIUM ---
def iniciar_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    return driver

# --- LOGIN NA ELEPHANTEBET ---
def login_elephantebet(driver):
    driver.get("https://elephantbet.co.ao")
    time.sleep(5)
    login_btn = driver.find_element(By.CLASS_NAME, "login")
    login_btn.click()
    time.sleep(2)
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.NAME, "password").send_keys(Keys.ENTER)
    time.sleep(5)

# --- COLETAR RESULTADOS DO BACBO ---
def coletar_resultados(driver):
    driver.get("https://elephantbet.co.ao/casino")
    time.sleep(10)
    resultados = []
    try:
        elementos = driver.find_elements(By.CSS_SELECTOR, ".history-result-circle")
        for e in elementos[:20]:
            texto = e.text.strip().upper()
            if texto in ["B", "P", "T"]:
                resultados.append(texto)
    except:
        pass
    return resultados

# --- ANALISAR TENDENCIA ---
def prever_sinal(resultados):
    if not resultados or len(resultados) < 3:
        return "Sem dados suficientes"
    ultimos = resultados[:5]
    count = {"B": 0, "P": 0, "T": 0}
    for r in ultimos:
        count[r] += 1
    if count["B"] >= 3:
        return "🔵 Azul"
    elif count["P"] >= 3:
        return "🔴 Vermelho"
    elif count["T"] >= 2:
        return "🟡 Empate"
    else:
        return "🔴 Vermelho"

# --- TAREFA PRINCIPAL ---
def enviar_sinal():
    driver = iniciar_driver()
    try:
        login_elephantebet(driver)
        resultados = coletar_resultados(driver)
        sinal = prever_sinal(resultados)
        bot.send_message(chat_id=CHAT_ID, text=f"Sinal Bac Bo: {sinal}")
    except Exception as e:
        logging.error(f"Erro: {e}")
    finally:
        driver.quit()

# --- AGENDAR EXECUCAO ---
schedule.every(2).minutes.do(enviar_sinal)

print("Bot de sinais Bac Bo iniciado...")
while True:
    schedule.run_pending()
    time.sleep(1)
