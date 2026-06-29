import time
import logging
import os
import schedule
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- CONFIGURAÇÕES ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', "8730616898:AAFo4A7ooNt1mjmAduemWWDLez38uumltzo")
CHAT_ID = os.environ.get('CHAT_ID', "@Lukevan_bot")
USERNAME = os.environ.get('ELEPHANT_USERNAME', "925959236")
PASSWORD = os.environ.get('ELEPHANT_PASSWORD', "Senhas.50")

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- ENVIO DE MENSAGEM VIA TELEGRAM (USANDO REQUESTS) ---
def enviar_mensagem_telegram(mensagem):
    """Envia mensagem via API do Telegram usando requests"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': mensagem,
        'parse_mode': 'Markdown'
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("Mensagem enviada com sucesso")
            return True
        else:
            logger.error(f"Erro ao enviar: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Erro na requisição: {e}")
        return False

# --- DRIVER ---
def iniciar_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # Desabilitar imagens para carregar mais rápido (opcional)
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=options)
    return driver

# --- LOGIN MELHORADO ---
def login_elephantebet(driver):
    try:
        logger.info("Acessando ElephantBet...")
        driver.get("https://elephantbet.co.ao")
        time.sleep(8)
        
        # Primeiro tenta clicar no botão login
        login_btn = None
        selectors = [
            "a.login",
            "button.login",
            "a[href*='login']",
            "button[class*='login']",
            "a:contains('Login')",
            "button:contains('Login')"
        ]
        for selector in selectors:
            try:
                login_btn = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue
        if login_btn:
            login_btn.click()
            logger.info("Botão de login clicado")
            time.sleep(5)
        else:
            logger.info("Botão não encontrado, tentando direto na página de login")
            driver.get("https://elephantbet.co.ao/login")
            time.sleep(5)
        
        # Aguardar o formulário
        try:
            # Esperar pelo campo de usuário
            username_field = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(USERNAME)
            
            password_field = driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            
            # Tentar submeter
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            submit_btn.click()
            time.sleep(5)
            
            # Verificar se o login foi bem sucedido (verificar se o URL mudou ou se aparece algum elemento de usuário logado)
            if "login" not in driver.current_url.lower():
                logger.info("Login aparentemente bem-sucedido")
                return True
            else:
                # Tentar ver se há mensagem de erro
                try:
                    error_msg = driver.find_element(By.CLASS_NAME, "error").text
                    logger.error(f"Mensagem de erro: {error_msg}")
                except:
                    pass
                return False
        except Exception as e:
            logger.error(f"Erro ao preencher credenciais: {e}")
            driver.save_screenshot("login_error.png")
            return False
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return False

# --- COLETA DE RESULTADOS (como antes) ---
def coletar_resultados(driver):
    try:
        logger.info("Coletando resultados do Bac Bo...")
        driver.get("https://elephantbet.co.ao/casino")
        time.sleep(10)
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
                        logger.info(f"Resultados encontrados com seletor: {seletor}")
                        break
            except:
                continue
        
        # Fallback com regex
        if not resultados:
            logger.info("Tentando extrair do HTML...")
            import re
            html = driver.page_source
            # Procurar padrões como B, P, T em classes ou textos
            matches = re.findall(r'[BPT](?=[\s<])', html)
            for m in matches[:20]:
                if m in ["B", "P", "T"]:
                    resultados.append(m)
        
        logger.info(f"Resultados coletados: {resultados[:10]}")
        return resultados
    except Exception as e:
        logger.error(f"Erro ao coletar resultados: {e}")
        return []

# --- ANÁLISE (igual) ---
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
        return "📊 Sem dados suficientes"
    
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
        return f"📈 {nomes[maior]} - Tendência detectada"

# --- TAREFA PRINCIPAL ---
def enviar_sinal():
    logger.info("Iniciando coleta de sinais...")
    driver = None
    try:
        driver = iniciar_driver()
        if login_elephantebet(driver):
            resultados = coletar_resultados(driver)
            sinal = prever_sinal(resultados)
            
            mensagem = f"""
🎯 *SINAL BAC BO - ELEPHANTBET*

📊 Análise: {sinal}

📈 Últimos resultados: {' '.join(resultados[:10]) if resultados else 'Sem dados'}

⏰ Atualizado: {time.strftime('%H:%M:%S')}
            """
            
            enviar_mensagem_telegram(mensagem)
            logger.info(f"Sinal enviado: {sinal}")
        else:
            enviar_mensagem_telegram("⚠️ Falha no login. Verificando...")
            logger.error("Falha no login")
    except Exception as e:
        logger.error(f"Erro na execução: {e}")
        enviar_mensagem_telegram(f"❌ Erro: {str(e)[:100]}")
    finally:
        if driver:
            driver.quit()
            logger.info("Driver fechado")

# --- MAIN ---
def main():
    logger.info("🤖 Bot de Sinais Bac Bo iniciado!")
    logger.info(f"📱 Canal: {CHAT_ID}")
    
    enviar_mensagem_telegram("🚀 Bot de Sinais Bac Bo está ONLINE!")
    enviar_sinal()
    schedule.every(2).minutes.do(enviar_sinal)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
