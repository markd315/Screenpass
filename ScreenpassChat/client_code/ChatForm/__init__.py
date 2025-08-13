import anvil.server
from anvil import *
from ._template import ChatTemplate
from datetime import datetime
import json


class ChatForm(ChatTemplate):
    def __init__(self, **properties):
        self.init_components_base(**properties)
        
        # Initialize conversation state
        self.conversation_history = []
        self.conversation_start_time = datetime.now()
        self.session_id = str(self.conversation_start_time.timestamp())
        self.lead_source = None
        self.company = None
        self.conversation_active = True
        
        # Set up event handlers
        self.setup_event_handlers()
        
        # Get URL parameters and initialize
        self.init_from_url_params()
        
    def setup_event_handlers(self):
        # Button event handlers
        self.submit_btn.set_event_handler('click', self.submit_query)
        self.end_chat_btn.set_event_handler('click', self.end_chat)
        
        # Text area event handlers
        self.query_input.set_event_handler('change', self.update_char_count)
        self.query_input.set_event_handler('pressed_enter', self.handle_enter_key)
        
    def handle_enter_key(self, **event_args):
        # Submit on Ctrl+Enter
        if event_args.get('ctrl', False):
            self.submit_query()
            
    def update_char_count(self, **event_args):
        char_count = len(self.query_input.text or "")
        self.char_counter.text = f"{char_count}/1000 characters"
        
        # Limit to 1000 characters
        if char_count > 1000:
            self.query_input.text = self.query_input.text[:1000]
            self.char_counter.text = "1000/1000 characters"
            
    def get_url_params(self):
        """Get URL parameters using JavaScript"""
        try:
            # Get URL parameters from browser
            url = anvil.js.call('window.location.href')
            if '?' in url:
                params_str = url.split('?')[1]
                params = {}
                for param in params_str.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value
                return params
        except:
            pass
        return {}
        
    def init_from_url_params(self):
        """Initialize conversation with URL parameters"""
        params = self.get_url_params()
        self.lead_source = params.get('leadSource', 'direct')
        self.company = params.get('company', 'companyA')
        
        # Initialize conversation with server
        try:
            response = anvil.server.call('init_conversation', 
                                       self.lead_source, 
                                       self.company, 
                                       self.session_id)
            if response.get('success'):
                self.add_message_to_chat('Screenpass', response.get('message', ''))
                self.show_status('Connected successfully!', 'success')
            else:
                self.add_message_to_chat('Screenpass', response.get('message', 'Welcome! I\'m here to help you with your trucking career.'))
                self.show_status('Connection issue, but chat is ready', 'error')
        except Exception as e:
            print(f"Error initializing conversation: {e}")
            self.add_message_to_chat('Screenpass', 'Welcome! I\'m here to help you with your trucking career.')
            self.show_status('Connection issue, but chat is ready', 'error')
            
    def add_message_to_chat(self, speaker, message):
        """Add a message to the chat area"""
        self.conversation_history.append(f">{speaker}: {message}")
        
        # Format message for display
        if speaker == 'Trucker':
            color = "#2196f3"
            bg_color = "#e3f2fd"
        else:  # Screenpass
            color = "#9c27b0"
            bg_color = "#f3e5f5"
            
        # Create HTML for the message
        message_html = f"""
        <div style="margin-bottom: 15px; padding: 12px; border-radius: 8px; 
                    background-color: {bg_color}; border-left: 4px solid {color};">
            <strong style="color: {color};">{speaker}:</strong> {message}
        </div>
        """
        
        # Update chat content
        current_content = self.chat_area.content or ""
        if current_content == "<p><strong>Screenpass:</strong> Initializing chat...</p>":
            current_content = ""
        
        self.chat_area.content = current_content + message_html
        
        # Scroll to bottom (simulate)
        anvil.js.call('setTimeout', lambda: self.scroll_chat_to_bottom(), 100)
        
    def scroll_chat_to_bottom(self):
        """Scroll chat area to bottom"""
        try:
            anvil.js.call('document.querySelector', '.anvil-rich-text').scrollTop = anvil.js.call('document.querySelector', '.anvil-rich-text').scrollHeight
        except:
            pass
            
    def show_status(self, message, status_type):
        """Show a status message"""
        if status_type == 'success':
            self.status_message.foreground = "#155724"
            self.status_message.background = "#d4edda"
        else:  # error
            self.status_message.foreground = "#721c24"
            self.status_message.background = "#f8d7da"
            
        self.status_message.text = message
        self.status_message.visible = True
        
        # Auto-hide after 3 seconds
        anvil.js.call('setTimeout', lambda: setattr(self.status_message, 'visible', False), 3000)
        
    def set_loading(self, is_loading):
        """Set loading state"""
        self.submit_btn.enabled = not is_loading
        self.query_input.enabled = not is_loading
        
        if is_loading:
            self.submit_btn.text = "Processing..."
            self.submit_btn.icon = "fa:spinner fa-spin"
        else:
            self.submit_btn.text = "Submit"
            self.submit_btn.icon = "fa:paper-plane"
            
    def submit_query(self, **event_args):
        """Handle submit button click"""
        query_text = (self.query_input.text or "").strip()
        
        if not query_text or not self.conversation_active:
            return
            
        # Add user message to chat
        self.add_message_to_chat('Trucker', query_text)
        
        # Clear input
        self.query_input.text = ""
        self.update_char_count()
        
        # Set loading state
        self.set_loading(True)
        
        # Send to server
        try:
            response = anvil.server.call('process_prompt', 
                                       query_text, 
                                       self.conversation_history,
                                       self.session_id)
            self.set_loading(False)
            
            if response.get('success'):
                self.add_message_to_chat('Screenpass', response.get('message', ''))
            else:
                self.add_message_to_chat('Screenpass', 'I\'m sorry, I encountered an error. Please try again.')
                self.show_status('Error processing message', 'error')
        except Exception as e:
            print(f"Error processing prompt: {e}")
            self.set_loading(False)
            self.add_message_to_chat('Screenpass', 'I\'m sorry, I encountered an error. Please try again.')
            self.show_status('Network error', 'error')
            
    def end_chat(self, **event_args):
        """Handle end chat button click"""
        if not self.conversation_active:
            return
            
        # Confirm with user
        if not anvil.confirm("Are you sure you want to end this chat? This will save and analyze the conversation."):
            return
            
        self.conversation_active = False
        self.set_loading(True)
        
        # Call summarize endpoint
        try:
            conversation_end_time = datetime.now()
            response = anvil.server.call('summarize_conversation',
                                       self.conversation_history,
                                       self.conversation_start_time,
                                       conversation_end_time,
                                       self.lead_source,
                                       self.company,
                                       self.session_id)
            
            self.set_loading(False)
            
            if response.get('success'):
                self.add_message_to_chat('Screenpass', 'Thank you for your time! The conversation has been saved and analyzed.')
                self.show_status('Chat ended successfully', 'success')
            else:
                self.add_message_to_chat('Screenpass', 'Chat ended, but there was an error saving the summary.')
                self.show_status('Error ending chat', 'error')
                
            # Disable controls
            self.submit_btn.enabled = False
            self.end_chat_btn.enabled = False
            self.query_input.enabled = False
            self.query_input.placeholder = 'Chat has ended'
            
        except Exception as e:
            print(f"Error ending chat: {e}")
            self.set_loading(False)
            self.add_message_to_chat('Screenpass', 'Chat ended, but there was an error saving the summary.')
            self.show_status('Network error', 'error')
            
            # Disable controls anyway
            self.submit_btn.enabled = False
            self.end_chat_btn.enabled = False
            self.query_input.enabled = False
            self.query_input.placeholder = 'Chat has ended'