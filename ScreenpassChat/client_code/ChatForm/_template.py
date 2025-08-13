import anvil
from anvil import *


class ChatTemplate(HtmlPanel):

    def init_components_base(self, **properties):
        super().__init__()
        self.clear()
        self.html = '@theme:standard-page.html'
        self.content_panel = GridPanel()
        self.add_component(self.content_panel)
        
        # Title
        self.title_label = Label(text="🚛 Screenpass Chat", font_size=24, bold=True)
        self.add_component(self.title_label, slot="title")
        
        # Main card
        self.card_1 = GridPanel(role="card")
        self.main_content = FlowPanel(align="center")
        self.card_1.add_component(self.main_content, row="A", col_sm=2, width_sm=10)
        self.content_panel.add_component(self.card_1, row="A", col_sm=1, width_sm=10)
        
        # Chat area
        self.chat_area = RichText(
            height=400,
            content="<p><strong>Screenpass:</strong> Initializing chat...</p>",
            enable_slots=False
        )
        self.main_content.add_component(self.chat_area)
        
        # Input area
        self.query_input = TextArea(
            placeholder="Type your message here... (Press Ctrl+Enter to send quickly)",
            height=100,
            width="100%"
        )
        self.main_content.add_component(self.query_input)
        
        # Character counter
        self.char_counter = Label(text="0/1000 characters", align="right", font_size=12, foreground="#666")
        self.main_content.add_component(self.char_counter)
        
        # Buttons panel
        self.button_panel = FlowPanel(align="center", spacing="medium")
        
        # Submit button
        self.submit_btn = Button(
            text="Submit",
            role="primary-color",
            icon="fa:paper-plane",
            spacing_above="small"
        )
        
        # End chat button  
        self.end_chat_btn = Button(
            text="End Chat",
            role="secondary-color", 
            icon="fa:times",
            spacing_above="small"
        )
        
        self.button_panel.add_component(self.submit_btn)
        self.button_panel.add_component(self.end_chat_btn)
        self.main_content.add_component(self.button_panel)
        
        # Status message
        self.status_message = Label(text="", visible=False, spacing_above="small")
        self.main_content.add_component(self.status_message)