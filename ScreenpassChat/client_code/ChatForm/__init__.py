import anvil.server
from anvil import *
from ._template import ChatTemplate
from datetime import datetime
import json


class ChatForm(ChatTemplate):
    """
    Screenpass Chat Form
    
    URL Hash Parameters:
    - leadSource: Source of the lead (e.g., 'google', 'facebook', 'direct')
    - company: Company configuration to use ('companyA' or 'companyB')
    
    Example URLs:
    - http://localhost:8080/#leadSource=google&company=companyB
    - http://localhost:8080/#leadSource=facebook&company=companyA
    """
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
            
    def update_char_count(self, **event_args):
        char_count = len(self.query_input.text or "")
        self.char_counter.text = f"{char_count}/1000 characters"
        
        # Limit to 1000 characters
        if char_count > 1000:
            self.query_input.text = self.query_input.text[:1000]
            self.char_counter.text = "1000/1000 characters"
            
    def get_hash_params(self):
        """Get parameters from URL hash using Anvil's routing system"""
        print("Getting parameters from URL hash...")
        
        try:
            from anvil import get_url_hash
            url_hash = get_url_hash()
            
            params = {}
            
            if url_hash:
                # If it's a dictionary, use it directly
                if isinstance(url_hash, dict):
                    params = url_hash
                else:
                    # If it's a string, parse it manually
                    hash_str = str(url_hash)
                    
                    # Parse the string like "leadSource=google&company=companyB"
                    for param in hash_str.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            params[key] = value
                
                # Extract the specific parameters we need
                result = {}
                if 'leadSource' in params:
                    result['leadSource'] = str(params['leadSource'])
                if 'company' in params:
                    result['company'] = str(params['company'])
                    
                print(f"Final extracted hash params: {result}")
                return result
                
        except Exception as e:
            print(f"Error getting hash params: {e}")
            
        return {}
        
    def init_from_url_params(self):
        """Initialize conversation with URL hash parameters"""
        # Debug: Show current URL
        try:
            current_url = anvil.js.call('window.location.href')
            print(f"Current URL: {current_url}")
        except Exception as e:
            print(f"Could not get current URL: {e}")
        
        # Get parameters from URL hash
        params = self.get_hash_params()
        
        # Set lead source and company from hash params
        self.lead_source = params.get('leadSource', 'direct')
        self.company = params.get('company', 'companyA')
        
        print(f"Final values - lead_source: {self.lead_source}, company: {self.company}")
        
        # Manual override for testing - you can set these directly
        # Uncomment these lines to test specific values:
        # self.lead_source = 'google'
        # self.company = 'companyB'
        # print(f"MANUAL OVERRIDE - lead_source: {self.lead_source}, company: {self.company}")
        
        self.start_conversation()
        
    def start_conversation(self):
        """Start the conversation with the server"""
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
        
        # Format message for display - simple text only
        message_text = f">{speaker}: {message}\n\n"
        
        # Update chat content
        current_content = self.chat_area.content or ""
        if current_content == ">Screenpass: Initializing chat...":
            current_content = ""
        
        self.chat_area.content = current_content + message_text
        
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
            self.submit_btn.icon = "fa:spinner"
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