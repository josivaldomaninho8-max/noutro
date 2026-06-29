import time
import logging
import schedule
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

# --- CONFIGURAÇÕES ---
TELEGRAM_TOKEN = "8819802652:AAGs9akn3f51BY8LRvUVpp8sxT7GAmBslm4"
CHAT_ID = "@Luckevan_bot"
USERNAME = "925959236"
PASSWORD = "Senhas.50"

# --- LOG ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- TELEGRAM VIA REQUESTS (SEM WARNINGS) ---
def enviar_mensagem_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            logger.error(f"Telegram API error: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        return False

# --- DRIVER COM UNDETECTED ---
def iniciar_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    driver = uc.Chrome(options=options)
    return driver

# --- LOGIN MAIS ROBUSTO ---
def login_elephantebet(driver):
    try:
        logger.info("Acessando site...")
        driver.get("https://elephantbet.co.ao")
        time.sleep(8)

        # Tenta clicar no botão "Entrar" (vários seletores)
        seletores_login_btn = [
            "button.sign-in",
            "a[href*='login']",
            "button[class*='login']",
            "button:contains('Entrar')",
            "a:contains('Entrar')"
        ]
        clicou = False
        for seletor in seletores_login_btn:
            try:
                btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, seletor))
                )
                btn.click()
                clicou = True
                logger.info(f"Botão clicado com seletor: {seletor}")
                break
            except:
                continue

        if not clicou:
            logger.warning("Botão não encontrado, indo para /login")
            driver.get("https://elephantbet.co.ao/login")
            time.sleep(5)

        # Aguardar campos
        wait = WebDriverWait(driver, 20)
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        username_field.clear()
        username_field.send_keys(USERNAME)

        password_field = driver.find_element(By.NAME, "password")
        password_field.clear()
        password_field.send_keys(PASSWORD)

        # Submeter
        try:
            submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            submit.click()
        except:
            password_field.send_keys(Keys.ENTER)

        time.sleep(8)

        # Verifica se login foi bem-sucedido (pela URL ou presença de elemento de usuário)
        if "login" not in driver.current_url.lower():
            logger.info("Login bem-sucedido!")
            return True
        else:
            # Verifica se há erro
            try:
                erro = driver.find_element(By.CSS_SELECTOR, ".error, .alert-danger").text
                logger.error(f"Mensagem de erro: {erro}")
            except:
                pass
            return False
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        try:
            driver.save_screenshot("login_error.png")
        except:
            pass
        return False

# --- COLETAR RESULTADOS (DIRETO DA PÁGINA DO BAC BO) ---
def coletar_resultados(driver):
    try:
        logger.info("Acessando página do Bac Bo...")
        # URL do jogo (pode ser a versão ao vivo ou normal)
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
        for seletor in seletores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
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
                        logger.info(f"Resultados com seletor: {seletor}")
                        break
            except:
                continue

        # Fallback: regex no HTML
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

        logger.info(f"Resultados coletados: {resultados[:10]}")
        return resultados
    except Exception as e:
        logger.error(f"Erro ao coletar: {e}")
        return []

# --- ANÁLISE DE TENDÊNCIA ---
def prever_sinal(resultados):
    if not resultados or len(resultados) < 3:
        return "📊 Aguardando mais dados..."
    ultimos = resultados[:10]
    count = {"B": 0, "P": 0, "T": 0}
    for r in ultimos:
        if r in count:
            count[r] += 1
    total = len(ultimos)
    if total == 0:
        return "📊 Sem dados"
    perc_b = (count["B"] / total) * 100
    perc_p = (count["P"] / total) * 100
    perc_t = (count["T"] / total) * 100
    if perc_b >= 50:
        return f"🔵 BANCO - ({perc_b:.1f}% chance)"
    elif perc_p >= 50:
        return f"🔴 JOGADOR - ({perc_p:.1f}% chance)"
    elif perc_t >= 40:
        return f"🟡 EMPATE - ({perc_t:.1f}% chance)"
    else:
        maior = max(count, key=count.get)
        nomes = {"B": "BANCO", "P": "JOGADOR", "T": "EMPATE"}
        return f"📈 {nomes[maior]} - Tendência"

# --- TAREFA PRINCIPAL ---
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
            logger.info("Sinal enviado")
        else:
            enviar_mensagem_telegram("⚠️ Falha no login. Verifique credenciais.")
    except Exception as e:
        logger.error(f"Erro na execução: {e}")
        enviar_mensagem_telegram(f"❌ Erro: {str(e)[:100]}")
    finally:
        if driver:
            driver.quit()
            logger.info("Driver fechado")

# --- INICIALIZAÇÃO ---
def main():
    logger.info("🤖 Bot de Sinais Bac Bo iniciado!")
    logger.info(f"📱 Canal: {CHAT_ID}")
    enviar_mensagem_telegram("🚀 Bot está ONLINE! (versão com requests)")
    enviar_sinal()
    schedule.every(2).minutes.do(enviar_sinal)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
