import time
import logging
import schedule
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURAÇÕES ---
TELEGRAM_TOKEN = "8819802652:AAGs9akn3f51BY8LRvUVpp8sxT7GAmBslm4"
CHAT_ID = "@Luckevan_bot"
USERNAME = "925959236"
PASSWORD = "Senhas.50"

# --- LOG ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- TELEGRAM VIA REQUESTS ---
def enviar_mensagem_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False

# --- DRIVER COM OPÇÕES ANTI-DETECÇÃO (SEM UNDETECTED) ---
def iniciar_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# --- LOGIN ---
def login_elephantebet(driver):
    try:
        logger.info("Acessando site...")
        driver.get("https://elephantbet.co.ao")
        time.sleep(8)

        # Tentar clicar em "Entrar"
        seletores = [
            "button.sign-in",
            "a[href*='login']",
            "button[class*='login']",
            "button:contains('Entrar')",
            "a:contains('Entrar')"
        ]
        clicou = False
        for sel in seletores:
            try:
                btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                btn.click()
                clicou = True
                logger.info(f"Clicou com {sel}")
                break
            except:
                continue

        if not clicou:
            logger.warning("Indo para /login")
            driver.get("https://elephantbet.co.ao/login")
            time.sleep(5)

        wait = WebDriverWait(driver, 20)
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        username_field.clear()
        username_field.send_keys(USERNAME)

        password_field = driver.find_element(By.NAME, "password")
        password_field.clear()
        password_field.send_keys(PASSWORD)

        try:
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        except:
            password_field.send_keys(Keys.ENTER)

        time.sleep(8)

        if "login" not in driver.current_url.lower():
            logger.info("Login OK")
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Login error: {e}")
        try:
            driver.save_screenshot("login_error.png")
        except:
            pass
        return False

# --- COLETAR RESULTADOS ---
def coletar_resultados(driver):
    try:
        logger.info("Acessando Bac Bo...")
        driver.get("https://elephantbet.co.ao/pt/casino/game-view/420012128/bac-bo")
        time.sleep(12)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(3)

        resultados = []
        seletores = [
            ".history-result-circle",
            ".result-circle",
            ".history-item .result",
            "[class*='history'] [class*='circle']",
            ".game-result",
            "[class*='result'] [class*='history']",
            "div[class*='result'] span",
            ".history-list .item"
        ]
        for sel in seletores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, sel)
                if elementos:
                    for e in elementos[:20]:
                        texto = e.text.strip().upper()
                        if texto in ["B", "P", "T"]:
                            resultados.append(texto)
                        elif "BANCO" in texto:
                            resultados.append("B")
                        elif "JOGADOR" in texto or "PLAYER" in texto:
                            resultados.append("P")
                        elif "EMPATE" in texto or "TIE" in texto:
                            resultados.append("T")
                    if resultados:
                        logger.info(f"Resultados via {sel}")
                        break
            except:
                continue

        if not resultados:
            import re
            padroes = [r'[BPT](?=\s|$)', r'BANCO|JOGADOR|EMPATE']
            for padrao in padroes:
                matches = re.findall(padrao, driver.page_source)
                for match in matches[:20]:
                    if match in ["B", "P", "T"]:
                        resultados.append(match)
                    elif "BANCO" in match:
                        resultados.append("B")
                    elif "JOGADOR" in match:
                        resultados.append("P")
                    elif "EMPATE" in match:
                        resultados.append("T")
                if resultados:
                    break

        logger.info(f"Coletados: {resultados[:10]}")
        return resultados
    except Exception as e:
        logger.error(f"Erro ao coletar: {e}")
        return []

# --- ANÁLISE ---
def prever_sinal(resultados):
    if not resultados or len(resultados) < 3:
        return "📊 Aguardando mais dados..."
    ultimos = resultados[:10]
    count = {"B": 0, "P": 0, "T": 0}
    for r in ultimos:
        if r in count:
            count[r] += 1
    total = len(ultimos)
    perc_b = (count["B"] / total) * 100
    perc_p = (count["P"] / total) * 100
    perc_t = (count["T"] / total) * 100

    if perc_b >= 50:
        return f"🔵 BANCO - ({perc_b:.1f}%)"
    elif perc_p >= 50:
        return f"🔴 JOGADOR - ({perc_p:.1f}%)"
    elif perc_t >= 40:
        return f"🟡 EMPATE - ({perc_t:.1f}%)"
    else:
        maior = max(count, key=count.get)
        nomes = {"B": "BANCO", "P": "JOGADOR", "T": "EMPATE"}
        return f"📈 {nomes[maior]} - Tendência"

# --- TAREFA ---
def enviar_sinal():
    logger.info("Iniciando coleta...")
    driver = None
    try:
        driver = iniciar_driver()
        if login_elephantebet(driver):
            resultados = coletar_resultados(driver)
            sinal = prever_sinal(resultados)
            mensagem = f"""
🎯 *SINAL BAC BO - ELEPHANTBET*

📊 Análise: {sinal}

📈 Últimos: {' '.join(resultados[:10]) if resultados else 'Sem dados'}

⏰ {time.strftime('%H:%M:%S')}
            """
            enviar_mensagem_telegram(mensagem)
            logger.info("Enviado")
        else:
            enviar_mensagem_telegram("⚠️ Falha no login.")
    except Exception as e:
        logger.error(f"Erro: {e}")
        enviar_mensagem_telegram(f"❌ Erro: {str(e)[:100]}")
    finally:
        if driver:
            driver.quit()

# --- MAIN ---
def main():
    logger.info("🚀 Bot iniciado!")
    enviar_mensagem_telegram("🚀 Bot ONLINE!")
    enviar_sinal()
    schedule.every(2).minutes.do(enviar_sinal)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
