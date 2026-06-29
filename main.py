import time
import logging
import os
import schedule
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import telegram

# --- CONFIGURAÇÕES DE SEGURANÇA (USANDO VARIÁVEIS DE AMBIENTE) ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', "8730616898:AAFo4A7ooNt1mjmAduemWWDLez38uumltzo")
CHAT_ID = os.environ.get('CHAT_ID', "@Lukevan_bot")
USERNAME = os.environ.get('ELEPHANT_USERNAME', "925959236")
PASSWORD = os.environ.get('ELEPHANT_PASSWORD', "Senhas.50")  # <-- Senha corrigida

# --- CONFIGURAÇÃO DE LOG ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- SETUP TELEGRAM (VERSÃO SÍNCRONA) ---
def enviar_mensagem_telegram(mensagem):
    """Envia mensagem para o Telegram de forma síncrona"""
    try:
        # Usamos a versão síncrona do Bot (sem async)
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode='Markdown')
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        return False

# --- SETUP SELENIUM PARA RENDER ---
def iniciar_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        logger.error(f"Erro ao iniciar driver: {e}")
        raise

# --- LOGIN NA ELEPHANTEBET (COM WAITS EXPLÍCITOS) ---
def login_elephantebet(driver):
    try:
        logger.info("Acessando ElephantBet...")
        driver.get("https://elephantbet.co.ao")
        time.sleep(8)
        
        # Tentar clicar no botão de login usando múltiplos seletores
        login_encontrado = False
        seletores_login = [
            (By.CLASS_NAME, "login"),
            (By.CSS_SELECTOR, "a[href*='login']"),
            (By.CSS_SELECTOR, "button[class*='login']"),
            (By.CSS_SELECTOR, "a[class*='login']"),
            (By.XPATH, "//a[contains(text(), 'Login')]"),
            (By.XPATH, "//button[contains(text(), 'Login')]"),
            (By.CSS_SELECTOR, ".user-login"),
            (By.CSS_SELECTOR, "[class*='login']")
        ]
        
        for seletor in seletores_login:
            try:
                login_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(seletor)
                )
                login_btn.click()
                login_encontrado = True
                logger.info(f"Login clicado com seletor: {seletor}")
                break
            except:
                continue
        
        if not login_encontrado:
            # Tentar acesso direto à página de login
            logger.info("Tentando acesso direto à página de login...")
            driver.get("https://elephantbet.co.ao/login")
            time.sleep(5)
        
        # Preencher credenciais com waits
        try:
            username_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(USERNAME)
            
            password_field = driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            
            # Submeter o formulário
            try:
                submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                submit_btn.click()
            except:
                password_field.send_keys(Keys.ENTER)
            
            time.sleep(5)
            
            # Verificar se o login foi bem-sucedido (redirecionamento)
            if "login" not in driver.current_url.lower():
                logger.info("Login realizado com sucesso!")
                return True
            else:
                logger.warning("Possível falha no login, mas continuando...")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao preencher credenciais: {e}")
            # Salvar screenshot para debug
            try:
                driver.save_screenshot("login_error.png")
                logger.info("Screenshot salvo como login_error.png")
            except:
                pass
            return False
            
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return False

# --- COLETAR RESULTADOS DO BACBO ---
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
        
        # Fallback: extrair do HTML
        if not resultados:
            logger.info("Tentando extrair do HTML...")
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
        logger.error(f"Erro ao coletar resultados: {e}")
        return []

# --- ANALISAR TENDÊNCIA ---
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

# --- INICIALIZAÇÃO ---
def main():
    logger.info("🤖 Bot de Sinais Bac Bo iniciado!")
    logger.info(f"📱 Canal: {CHAT_ID}")
    
    enviar_mensagem_telegram("🚀 Bot de Sinais Bac Bo está ONLINE!")
    
    # Executar imediatamente
    enviar_sinal()
    
    # Agendar a cada 2 minutos
    schedule.every(2).minutes.do(enviar_sinal)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
