import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
from jellyfin_api import JellyfinAPI

# Configuração de logging
logger = logging.getLogger(__name__)

class JellyfinTelegramBot:
    def __init__(self):
        load_dotenv()
        self.jellyfin_url = os.getenv('JELLYFIN_URL')
        self.jellyfin_username = os.getenv('JELLYFIN_USERNAME')
        self.jellyfin_password = os.getenv('JELLYFIN_PASSWORD')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.authorized_users = self._parse_authorized_users()
        
        # Cache para evitar spam de notificações
        self.last_check = datetime.now()
        self.known_items = set()
        
    def _parse_authorized_users(self):
        """Parse dos usuários autorizados do .env"""
        users_str = os.getenv('AUTHORIZED_USERS', '')
        if users_str:
            return [int(user_id.strip()) for user_id in users_str.split(',')]
        return []
    
    def is_authorized(self, user_id: int) -> bool:
        """Verifica se o usuário está autorizado"""
        return not self.authorized_users or user_id in self.authorized_users
    
    def format_item_info(self, item: Dict) -> str:
        """Formata informações de um item para exibição"""
        name = item.get('Name', 'N/A')
        item_type = item.get('Type', 'N/A')
        year = item.get('ProductionYear', 'N/A')
        overview = item.get('Overview', 'Sem descrição')
        
        if len(overview) > 200:
            overview = overview[:200] + "..."
        
        user_data = item.get('UserData', {})
        watched = "✅ Assistido" if user_data.get('Played', False) else "⏸️ Não assistido"
        
        genres = item.get('Genres', [])
        genres_str = ", ".join(genres[:3]) if genres else "N/A"
        
        return f"""
🎬 **{name}** ({year})
📁 Tipo: {item_type}
🎭 Gêneros: {genres_str}
{watched}

📝 {overview}
        """.strip()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Você não tem permissão para usar este bot.")
            return
            
        welcome_text = """
🎬 **Jellyfin Manager Bot**

Comandos disponíveis:
/recent - Ver itens recentemente adicionados
/search <termo> - Buscar conteúdo
/libraries - Listar bibliotecas
/status - Status do servidor
/help - Mostrar esta ajuda

Use os botões inline para interagir com o conteúdo!
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def recent_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /recent"""
        if not self.is_authorized(update.effective_user.id):
            return
            
        await update.message.reply_text("🔍 Buscando itens recentes...")
        
        try:
            async with JellyfinAPI(self.jellyfin_url, self.jellyfin_username, self.jellyfin_password) as api:
                items = await api.get_recent_items(10)
                
                if not items:
                    await update.message.reply_text("❌ Nenhum item encontrado.")
                    return
                
                for item in items[:5]:
                    item_info = self.format_item_info(item)
                    
                    keyboard = [
                        [
                            InlineKeyboardButton("✅ Marcar Assistido", callback_data=f"watch_{item['Id']}"),
                            InlineKeyboardButton("⏸️ Marcar Não Assistido", callback_data=f"unwatch_{item['Id']}")
                        ],
                        [InlineKeyboardButton("ℹ️ Mais Detalhes", callback_data=f"details_{item['Id']}")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(item_info, parse_mode='Markdown', reply_markup=reply_markup)
                    
        except Exception as e:
            logger.error(f"Erro no comando recent: {e}")
            await update.message.reply_text(f"❌ Erro ao buscar itens: {str(e)}")
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /search"""
        if not self.is_authorized(update.effective_user.id):
            return
            
        if not context.args:
            await update.message.reply_text("❌ Use: /search <termo de busca>")
            return
        
        query = " ".join(context.args)
        await update.message.reply_text(f"🔍 Buscando por: {query}")
        
        try:
            async with JellyfinAPI(self.jellyfin_url, self.jellyfin_username, self.jellyfin_password) as api:
                items = await api.search_items(query, 5)
                
                if not items:
                    await update.message.reply_text("❌ Nenhum item encontrado.")
                    return
                
                for item in items:
                    item_info = self.format_item_info(item)
                    
                    keyboard = [
                        [
                            InlineKeyboardButton("✅ Marcar Assistido", callback_data=f"watch_{item['Id']}"),
                            InlineKeyboardButton("⏸️ Marcar Não Assistido", callback_data=f"unwatch_{item['Id']}")
                        ],
                        [InlineKeyboardButton("ℹ️ Mais Detalhes", callback_data=f"details_{item['Id']}")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(item_info, parse_mode='Markdown', reply_markup=reply_markup)
                    
        except Exception as e:
            logger.error(f"Erro no comando search: {e}")
            await update.message.reply_text(f"❌ Erro na busca: {str(e)}")
    
    async def libraries_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /libraries"""
        if not self.is_authorized(update.effective_user.id):
            return
            
        try:
            async with JellyfinAPI(self.jellyfin_url, self.jellyfin_username, self.jellyfin_password) as api:
                libraries = await api.get_libraries()
                
                if not libraries:
                    await update.message.reply_text("❌ Nenhuma biblioteca encontrada.")
                    return
                
                text = "📚 **Bibliotecas Disponíveis:**\n\n"
                for lib in libraries:
                    name = lib.get('Name', 'N/A')
                    lib_type = lib.get('CollectionType', 'N/A')
                    text += f"• {name} ({lib_type})\n"
                
                await update.message.reply_text(text, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Erro no comando libraries: {e}")
            await update.message.reply_text(f"❌ Erro ao buscar bibliotecas: {str(e)}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /status"""
        if not self.is_authorized(update.effective_user.id):
            return
            
        try:
            async with JellyfinAPI(self.jellyfin_url, self.jellyfin_username, self.jellyfin_password) as api:
                libraries = await api.get_libraries()
                recent_items = await api.get_recent_items(1)
                
                status_text = f"""
🟢 **Status do Servidor Jellyfin**

🌐 Servidor: {self.jellyfin_url}
👤 Usuário: {self.jellyfin_username}
📚 Bibliotecas: {len(libraries)}
🆕 Último item: {recent_items[0].get('Name', 'N/A') if recent_items else 'N/A'}

✅ Conexão OK
                """.strip()
                
                await update.message.reply_text(status_text, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Erro no comando status: {e}")
            await update.message.reply_text(f"❌ Erro de conexão: {str(e)}")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manipula callbacks dos botões inline"""
        if not self.is_authorized(update.effective_user.id):
            return
            
        query = update.callback_query
        await query.answer()
        
        action, item_id = query.data.split('_', 1)
        
        try:
            async with JellyfinAPI(self.jellyfin_url, self.jellyfin_username, self.jellyfin_password) as api:
                if action == "watch":
                    success = await api.mark_watched(item_id)
                    if success:
                        await query.edit_message_text("✅ Marcado como assistido!")
                    else:
                        await query.edit_message_text("❌ Erro ao marcar como assistido.")
                        
                elif action == "unwatch":
                    success = await api.mark_unwatched(item_id)
                    if success:
                        await query.edit_message_text("⏸️ Marcado como não assistido!")
                    else:
                        await query.edit_message_text("❌ Erro ao marcar como não assistido.")
                        
                elif action == "details":
                    item = await api.get_item_details(item_id)
                    if item:
                        item_info = self.format_item_info(item)
                        await query.edit_message_text(item_info, parse_mode='Markdown')
                    else:
                        await query.edit_message_text("❌ Não foi possível obter detalhes do item.")
                        
        except Exception as e:
            logger.error(f"Erro no callback: {e}")
            await query.edit_message_text(f"❌ Ocorreu um erro: {str(e)}")
    
    async def check_new_content(self, context: ContextTypes.DEFAULT_TYPE):
        """Verifica novos conteúdos (job periódico)"""
        try:
            async with JellyfinAPI(self.jellyfin_url, self.jellyfin_username, self.jellyfin_password) as api:
                # Busca itens das últimas 24 horas
                items = await api.get_recent_items(20)
                new_items = []
                
                for item in items:
                    if item['Id'] not in self.known_items:
                        new_items.append(item)
                        self.known_items.add(item['Id'])
                
                if new_items and self.authorized_users:
                    message = "🎬 **Novos itens adicionados!**\n\n"
                    for item in new_items[:5]:  # Limita a 5 itens na notificação
                        message += f"• {item.get('Name')} ({item.get('Type')})\n"
                    
                    for user_id in self.authorized_users:
                        try:
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=message,
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logger.error(f"Erro ao enviar notificação para {user_id}: {e}")
                
                self.last_check = datetime.now()
                
        except Exception as e:
            logger.error(f"Erro ao verificar novos conteúdos: {e}")
    
    def run(self):
        """Inicia o bot"""
        if not all([self.telegram_token, self.jellyfin_url, self.jellyfin_username, self.jellyfin_password]):
            logger.error("Variáveis de ambiente necessárias não configuradas.")
            return
        
        application = Application.builder().token(self.telegram_token).build()
        
        # Handlers de comandos
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("recent", self.recent_command))
        application.add_handler(CommandHandler("search", self.search_command))
        application.add_handler(CommandHandler("libraries", self.libraries_command))
        application.add_handler(CommandHandler("status", self.status_command))
        
        # Handler para callbacks de botões
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Job para verificar novos conteúdos a cada hora
        job_queue = application.job_queue
        job_queue.run_repeating(
            self.check_new_content,
            interval=3600,  # 1 hora
            first=10  # Primeira execução em 10 segundos
        )
        
        logger.info("Bot iniciado!")
        application.run_polling()
