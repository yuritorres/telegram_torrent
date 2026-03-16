"""
Exemplo de uso da integração WhatsApp WAHA

Este arquivo demonstra como usar a API WhatsApp WAHA
para enviar mensagens e processar webhooks.
"""
import logging
from waha_api import WAHAApi
from waha_utils import (
    init_waha_client,
    send_whatsapp,
    get_whatsapp_qr,
    start_whatsapp_session,
    get_whatsapp_status,
    format_chat_id
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_send_text_message():
    """Exemplo: Enviar mensagem de texto"""
    print("\n=== Exemplo 1: Enviar Mensagem de Texto ===")
    
    # Inicializar cliente
    client = init_waha_client()
    
    if not client:
        print("❌ Erro ao inicializar cliente WAHA")
        return
    
    # Enviar mensagem
    chat_id = "5511999999999@c.us"  # Substitua pelo número real
    success = send_whatsapp(
        text="🤖 Olá! Esta é uma mensagem de teste do bot.",
        chat_id=chat_id
    )
    
    if success:
        print(f"✅ Mensagem enviada para {chat_id}")
    else:
        print("❌ Falha ao enviar mensagem")


def example_send_image():
    """Exemplo: Enviar imagem com legenda"""
    print("\n=== Exemplo 2: Enviar Imagem ===")
    
    client = WAHAApi(
        base_url="http://localhost:3000",
        api_key="local-dev-key-123"
    )
    
    chat_id = "5511999999999@c.us"
    image_url = "https://picsum.photos/800/600"
    
    success = client.send_image(
        chat_id=chat_id,
        image_url=image_url,
        caption="🖼️ Imagem de exemplo"
    )
    
    if success:
        print(f"✅ Imagem enviada para {chat_id}")
    else:
        print("❌ Falha ao enviar imagem")


def example_send_file():
    """Exemplo: Enviar arquivo"""
    print("\n=== Exemplo 3: Enviar Arquivo ===")
    
    client = WAHAApi(
        base_url="http://localhost:3000",
        api_key="local-dev-key-123"
    )
    
    chat_id = "5511999999999@c.us"
    file_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    
    success = client.send_file(
        chat_id=chat_id,
        file_url=file_url,
        filename="documento.pdf",
        caption="📄 Documento de exemplo"
    )
    
    if success:
        print(f"✅ Arquivo enviado para {chat_id}")
    else:
        print("❌ Falha ao enviar arquivo")


def example_get_qr_code():
    """Exemplo: Obter QR Code para autenticação"""
    print("\n=== Exemplo 4: Obter QR Code ===")
    
    # Iniciar sessão
    print("Iniciando sessão WhatsApp...")
    success = start_whatsapp_session()
    
    if success:
        print("✅ Sessão iniciada")
        
        # Obter QR Code
        qr_url = get_whatsapp_qr()
        
        if qr_url:
            print(f"📱 QR Code disponível em: {qr_url}")
            print("Abra este link no navegador e escaneie com seu WhatsApp")
        else:
            print("❌ Não foi possível obter o QR Code")
    else:
        print("❌ Falha ao iniciar sessão")


def example_check_status():
    """Exemplo: Verificar status da sessão"""
    print("\n=== Exemplo 5: Verificar Status ===")
    
    status = get_whatsapp_status()
    
    if status:
        print(f"📊 Status da sessão:")
        print(f"  - Nome: {status.get('name', 'N/A')}")
        print(f"  - Status: {status.get('status', 'N/A')}")
        print(f"  - Engine: {status.get('engine', 'N/A')}")
    else:
        print("❌ Não foi possível obter o status")


def example_get_contacts():
    """Exemplo: Listar contatos"""
    print("\n=== Exemplo 6: Listar Contatos ===")
    
    client = WAHAApi(
        base_url="http://localhost:3000",
        api_key="local-dev-key-123"
    )
    
    contacts = client.get_contacts()
    
    if contacts:
        print(f"📇 Total de contatos: {len(contacts)}")
        
        # Mostrar primeiros 5 contatos
        for i, contact in enumerate(contacts[:5], 1):
            name = contact.get('name', 'Sem nome')
            number = contact.get('id', 'N/A')
            print(f"  {i}. {name} ({number})")
    else:
        print("❌ Nenhum contato encontrado")


def example_notification_torrent_complete():
    """Exemplo: Notificar conclusão de torrent"""
    print("\n=== Exemplo 7: Notificação de Torrent ===")
    
    # Dados do torrent (exemplo)
    torrent_name = "Ubuntu 22.04 LTS Desktop"
    torrent_size = "3.5 GB"
    download_time = "15 minutos"
    
    # Formatar mensagem
    message = f"""
✅ *Download Concluído!*

📁 *Arquivo:* {torrent_name}
💾 *Tamanho:* {torrent_size}
⏱️ *Tempo:* {download_time}

Use /qtorrents para ver todos os downloads.
    """
    
    # Enviar para usuário autorizado
    chat_id = "5511999999999@c.us"
    success = send_whatsapp(message, chat_id)
    
    if success:
        print("✅ Notificação enviada")
    else:
        print("❌ Falha ao enviar notificação")


def example_format_chat_id():
    """Exemplo: Formatar número para chat_id"""
    print("\n=== Exemplo 8: Formatar Chat ID ===")
    
    numbers = [
        "5511999999999",
        "+55 11 99999-9999",
        "(11) 99999-9999",
        "5511999999999@c.us"
    ]
    
    for number in numbers:
        formatted = format_chat_id(number)
        print(f"  {number} → {formatted}")


def main():
    """Executa todos os exemplos"""
    print("=" * 60)
    print("EXEMPLOS DE USO DA API WHATSAPP WAHA")
    print("=" * 60)
    
    # Verificar status primeiro
    example_check_status()
    
    # Exemplos de envio (descomente para testar)
    # ATENÇÃO: Substitua os números de telefone antes de executar!
    
    # example_send_text_message()
    # example_send_image()
    # example_send_file()
    # example_get_qr_code()
    # example_get_contacts()
    # example_notification_torrent_complete()
    example_format_chat_id()
    
    print("\n" + "=" * 60)
    print("✅ Exemplos concluídos!")
    print("=" * 60)


if __name__ == "__main__":
    main()
