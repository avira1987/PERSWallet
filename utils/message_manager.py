"""Utility functions for managing bot messages and deletion"""

from telegram import Update
from telegram.ext import ContextTypes
from utils.encryption import decrypt_state, encrypt_state


async def delete_previous_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   db_manager, user_id: str, delete_user_message: bool = True):
    """
    Delete previous bot message (if stored in state) and optionally user message
    
    Args:
        update: Telegram update object
        context: Bot context
        db_manager: Database manager instance
        user_id: User ID string
        delete_user_message: Whether to delete user's message (default: True)
    
    Returns:
        None
    """
    # Delete user message if requested
    if delete_user_message and update.message:
        try:
            await update.message.delete()
        except:
            pass
    
    # Get state and delete previous bot message
    encrypted_state = db_manager.get_user_state(user_id)
    if encrypted_state:
        state = decrypt_state(encrypted_state)
        last_bot_message_id = state.get('last_bot_message_id')
        
        if last_bot_message_id:
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=last_bot_message_id
                )
            except:
                pass  # Message might already be deleted or not accessible


async def send_and_save_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, 
                                text: str, db_manager, user_id: str, 
                                reply_markup=None, parse_mode=None, **kwargs):
    """
    Send a message and save its ID in state for later deletion
    
    Args:
        context: Bot context
        chat_id: Chat ID
        text: Message text
        db_manager: Database manager instance
        user_id: User ID string
        reply_markup: Optional reply markup
        parse_mode: Optional parse mode
        **kwargs: Additional arguments for send_message
    
    Returns:
        Message object
    """
    from utils.encryption import decrypt_state, encrypt_state
    
    # Send message
    message = await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        **kwargs
    )
    
    # Save message ID in state
    encrypted_state = db_manager.get_user_state(user_id)
    if encrypted_state:
        state = decrypt_state(encrypted_state)
    else:
        state = {}
    
    state['last_bot_message_id'] = message.message_id
    encrypted_state = encrypt_state(state)
    db_manager.update_user_state(user_id, encrypted_state)
    
    return message


async def edit_and_save_message(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                text: str, db_manager, user_id: str,
                                reply_markup=None, parse_mode=None, **kwargs):
    """
    Edit a message (from callback query) and save its ID in state
    
    Args:
        update: Telegram update object
        context: Bot context
        text: Message text
        db_manager: Database manager instance
        user_id: User ID string
        reply_markup: Optional reply markup
        parse_mode: Optional parse mode
        **kwargs: Additional arguments for edit_message_text
    
    Returns:
        Message object
    """
    from utils.encryption import decrypt_state, encrypt_state
    
    if not update.callback_query:
        return None
    
    # Edit message
    message = await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        **kwargs
    )
    
    # Save message ID in state
    encrypted_state = db_manager.get_user_state(user_id)
    if encrypted_state:
        state = decrypt_state(encrypted_state)
    else:
        state = {}
    
    state['last_bot_message_id'] = message.message_id
    encrypted_state = encrypt_state(state)
    db_manager.update_user_state(user_id, encrypted_state)
    
    return message
