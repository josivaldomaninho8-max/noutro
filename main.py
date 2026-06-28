import time
import logging
import os
import schedule
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from telegram import Bot

# --- CONFIGURAÇÕES DE SEGURANÇA (USANDO VARIÁVEIS DE AMBIENTE) ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', "8730616898:AAFo4A7ooNt1mjmAduemWWDLez38uumltzo")
CHAT_ID = os.environ.get('CHAT_ID', "@Lukevan_bot")
USERNAME = os.environ.get('ELEPHANT_USERNAME', "925959236")
PASSWORD = os.environ.get('ELEPHANT_PASSWORD', "Senhas.925")

# --- CONFIGURAÇÃO DE LOG ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- SETUP TELEGRAM ---
bot = Bot(token=TELEGRAM_TOKEN)

# --- SETUP SELENIUM PARA RENDER ---
def iniciar_driver():
    options = Options()
    options.add_argument('--headless')  # Modo sem interface gráfica
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    
    # Configurações específicas para o Render
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        logger.error(f"Erro ao iniciar driver: {e}")
        raise

# --- LOGIN NA ELEPHANTEBET (COM TRATAMENTO DE ERROS) ---
def login_elephantebet(driver):
    try:
        logger.info("Acessando ElephantBet...")
        driver.get("https://elephantbet.co.ao")
        time.sleep(5)
        
        # Tentar encontrar o botão de login
        try:
            login_btn = driver.find_element(By.CLASS_NAME, "login")
            login_btn.click()
            logger.info("Botão de login clicado")
        except:
            # Tentar outro seletor se o primeiro falhar
            login_btn = driver.find_element(By.CSS_SELECTOR, "a[href*='login']")
            login_btn.click()
        
        time.sleep(3)
        
        # Preencher credenciais
        username_field = driver.find_element(By.NAME, "username")
        username_field.send_keys(USERNAME)
        
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(PASSWORD)
        password_field.send_keys(Keys.ENTER)
        
        time.sleep(5)
        logger.info("Login realizado com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        # Salvar screenshot para debug
        try:
            driver.save_screenshot("login_error.png")
        except:
            pass
        return False

# --- COLETAR RESULTADOS DO BACBO (COM MELHORIA) ---
def coletar_resultados(driver):
    try:
        logger.info("Coletando resultados do Bac Bo...")
        driver.get("https://elephantbet.co.ao/casino")
        time.sleep(10)  # Tempo para carregar completamente
        
        resultados = []
        # Múltiplos seletores para tentar capturar os resultados
        seletores = [
            ".history-result-circle",
            ".result-circle",
            ".history-item .result",
            "[class*='history'] [class*='circle']"
        ]
        
        for seletor in seletores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                if elementos:
                    for e in elementos[:20]:
                        texto = e.text.strip().upper()
                        # Normalizar texto
                        if "BANCO" in texto or "B" in texto:
                            resultados.append("B")
                        elif "JOGADOR" in texto or "P" in texto or "PLAYER" in texto:
                            resultados.append("P")
                        elif "EMPATE" in texto or "T" in texto or "TIE" in texto:
                            resultados.append("T")
                    if resultados:
                        break
            except:
                continue
        
        logger.info(f"Resultados coletados: {resultados[:10]}")
        return resultados
    except Exception as e:
        logger.error(f"Erro ao coletar resultados: {e}")
        return []

# --- ANALISAR TENDÊNCIA (MELHORADA) ---
def prever_sinal(resultados):
    if not resultados or len(resultados) < 3:
        return "📊 Aguardando mais dados..."
    
    # Pegar os últimos 10 resultados
    ultimos = resultados[:10]
    count = {"B": 0, "P": 0, "T": 0}
    for r in ultimos:
        if r in count:
            count[r] += 1
    
    # Análise mais completa
    total = len(ultimos)
    perc_b = (count["B"] / total) * 100 if total > 0 else 0
    perc_p = (count["P"] / total) * 100 if total > 0 else 0
    perc_t = (count["T"] / total) * 100 if total > 0 else 0
    
    # Lógica de decisão
    if perc_b >= 50:
        return f"🔵 BANCO - ({perc_b:.1f}% chance)"
    elif perc_p >= 50:
        return f"🔴 JOGADOR - ({perc_p:.1f}% chance)"
    elif perc_t >= 40:
        return f"🟡 EMPATE - ({perc_t:.1f}% chance)"
    else:
        # Se nenhuma tendência clara, recomendar o que está mais quente
        maior = max(count, key=count.get)
        nomes = {"B": "BANCO", "P": "JOGADOR", "T": "EMPATE"}
        return f"📈 {nomes[maior]} - Tendência detectada"

# --- TAREFA PRINCIPAL COM STATUS ---
def enviar_sinal():
    logger.info("Iniciando coleta de sinais...")
    driver = None
    try:
        driver = iniciar_driver()
        if login_elephantebet(driver):
            resultados = coletar_resultados(driver)
            sinal = prever_sinal(resultados)
            
            # Formatar mensagem
            mensagem = f"""
🎯 *SINAL BAC BO - ELEPHANTBET*

📊 Análise: {sinal}

📈 Últimos resultados: {' '.join(resultados[:10]) if resultados else 'Sem dados'}

⏰ Atualizado: {time.strftime('%H:%M:%S')}
            """
            
            bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode='Markdown')
            logger.info(f"Sinal enviado com sucesso: {sinal}")
        else:
            bot.send_message(chat_id=CHAT_ID, text="⚠️ Falha no login. Verificando...")
            logger.error("Falha no login")
    except Exception as e:
        logger.error(f"Erro na execução: {e}")
        try:
            bot.send_message(chat_id=CHAT_ID, text=f"❌ Erro: {str(e)[:100]}")
        except:
            pass
    finally:
        if driver:
            driver.quit()
            logger.info("Driver fechado")

# --- INICIALIZAÇÃO ---
def main():
    logger.info("🤖 Bot de Sinais Bac Bo iniciado!")
    logger.info(f"📱 Canal: {CHAT_ID}")
    
    # Enviar mensagem de inicialização
    try:
        bot.send_message(chat_id=CHAT_ID, text="🚀 Bot de Sinais Bac Bo está ONLINE!")
    except:
        logger.warning("Não foi possível enviar mensagem de inicialização")
    
    # Agendar execução a cada 2 minutos
    schedule.every(2).minutes.do(enviar_sinal)
    
    # Também executar imediatamente na inicialização
    enviar_sinal()
    
    # Loop principal
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
