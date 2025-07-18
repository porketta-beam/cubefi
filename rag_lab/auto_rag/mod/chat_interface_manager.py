"""Chat interface management module"""

import streamlit as st
from typing import List, Dict, Optional


class ChatInterfaceManager:
    """Chat interface management class"""
    
    def __init__(self):
        self.chat_messages = []
        
    def add_message(self, role: str, content: str, contexts: Optional[List[str]] = None):
        """Add message"""
        message = {"role": role, "content": content}
        if contexts:
            message["contexts"] = contexts
        self.chat_messages.append(message)
        
    def clear_messages(self):
        """Clear messages"""
        self.chat_messages = []
        
    def get_messages(self) -> List[Dict]:
        """Get message list"""
        return self.chat_messages.copy()
    
    def get_message_count(self) -> int:
        """Get message count"""
        return len(self.chat_messages)
    
    def get_last_message(self) -> Optional[Dict]:
        """Get last message"""
        if self.chat_messages:
            return self.chat_messages[-1]
        return None
        
    def display_messages(self):
        """Display messages in Streamlit"""
        for message in self.chat_messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])
                    if "contexts" in message:
                        with st.expander("Reference Documents"):
                            for j, context in enumerate(message["contexts"]):
                                st.write(f"**Document {j+1}:**")
                                st.write(context[:300] + "..." if len(context) > 300 else context)
                                st.write("---")
    
    def export_conversation(self) -> str:
        """Export conversation to text"""
        conversation_text = ""
        for i, message in enumerate(self.chat_messages):
            if message["role"] == "user":
                conversation_text += f"User: {message['content']}\n\n"
            else:
                conversation_text += f"AI: {message['content']}\n\n"
        return conversation_text
    
    def import_conversation(self, conversation_data: List[Dict]):
        """Import conversation data"""
        self.chat_messages = conversation_data.copy()
    
    def remove_message(self, index: int):
        """Remove specific message"""
        if 0 <= index < len(self.chat_messages):
            self.chat_messages.pop(index)
    
    def update_message(self, index: int, content: str):
        """Update specific message content"""
        if 0 <= index < len(self.chat_messages):
            self.chat_messages[index]["content"] = content