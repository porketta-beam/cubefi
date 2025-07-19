#!/usr/bin/env python3
"""
Test script for RAG functionality with documents
"""

import requests
import json
import asyncio
import websockets
from time import sleep
import subprocess
import sys

BASE_URL = "http://localhost:8001"
WS_URL = "ws://localhost:8001/ws/chat"

def test_document_sync():
    """Test document synchronization"""
    print("=== Testing Document Synchronization ===")
    
    # Check current status
    response = requests.get(f"{BASE_URL}/api/documents/status")
    print(f"Current status: {response.json()}")
    
    # Sync documents
    sync_data = {
        "chunk_size": 500,
        "chunk_overlap": 100
    }
    
    response = requests.post(f"{BASE_URL}/api/documents/sync", json=sync_data)
    print(f"Sync status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Sync result: {result}")
        return result['success'] and result['total_documents'] > 0
    else:
        print(f"Sync error: {response.text}")
        return False

def test_rag_config():
    """Test RAG configuration"""
    print("\n=== Testing RAG Configuration ===")
    
    # Set RAG configuration
    config_data = {
        "model": "gpt-4o-mini",
        "temperature": 0.1,
        "search_type": "similarity",
        "k": 5
    }
    
    response = requests.post(f"{BASE_URL}/api/rag/set", json=config_data)
    print(f"Config set status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Config result: {result}")
        return result['success']
    else:
        print(f"Config error: {response.text}")
        return False

def test_rag_chat():
    """Test RAG chat"""
    print("\n=== Testing RAG Chat ===")
    
    chat_data = {
        "question": "What is tax law?",
        "model": "gpt-4o-mini",
        "temperature": 0.0,
        "search_type": "similarity",
        "k": 3
    }
    
    response = requests.post(f"{BASE_URL}/api/rag/chat", json=chat_data)
    print(f"Chat status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Answer: {result['answer'][:100]}...")
        print(f"Context count: {len(result['contexts'])}")
        print(f"Success: {result['success']}")
        return result['success']
    else:
        print(f"Chat error: {response.text}")
        return False

async def test_websocket_chat():
    """Test WebSocket chat"""
    print("\n=== Testing WebSocket Chat ===")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("WebSocket connected successfully")
            
            # Send question
            test_question = "What is tax law?"
            message = {"message": test_question}
            
            print(f"Sending question: {test_question}")
            await websocket.send(json.dumps(message))
            
            # Receive streaming response
            response_chunks = []
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30)
                    data = json.loads(response)
                    
                    if data["type"] == "start":
                        print(f"Stream started: {data['message']}")
                    elif data["type"] == "chunk":
                        content = data["content"]
                        response_chunks.append(content)
                        print(content, end="", flush=True)
                    elif data["type"] == "done":
                        print("\\nStream completed")
                        break
                    elif data["type"] == "error":
                        print(f"Error: {data['message']}")
                        return False
                        
                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    return False
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    return False
            
            full_response = "".join(response_chunks)
            print(f"Full response length: {len(full_response)} characters")
            return len(full_response) > 0
            
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        return False

def main():
    """Run all tests with documents"""
    print("=== RAG Functionality Tests with Documents ===")
    
    # Start server
    server_proc = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'server:app', '--port', '8001'], 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    print("Starting server...")
    sleep(5)
    
    try:
        # Test document sync
        sync_success = test_document_sync()
        
        if sync_success:
            # Test RAG configuration
            config_success = test_rag_config()
            
            if config_success:
                # Test RAG chat
                chat_success = test_rag_chat()
                
                # Test WebSocket
                ws_success = asyncio.run(test_websocket_chat())
                
                print(f"\\n=== Test Results ===")
                print(f"Document Sync: {'✅ PASS' if sync_success else '❌ FAIL'}")
                print(f"RAG Config: {'✅ PASS' if config_success else '❌ FAIL'}")
                print(f"RAG Chat: {'✅ PASS' if chat_success else '❌ FAIL'}")
                print(f"WebSocket: {'✅ PASS' if ws_success else '❌ FAIL'}")
                
                if all([sync_success, config_success, chat_success, ws_success]):
                    print("\\n🎉 All tests passed!")
                else:
                    print("\\n❌ Some tests failed")
            else:
                print("\\n❌ RAG configuration failed, skipping other tests")
        else:
            print("\\n❌ Document sync failed, skipping other tests")
            
    except Exception as e:
        print(f"Test error: {e}")
    finally:
        # Stop server
        server_proc.terminate()
        server_proc.wait()
        print("Server stopped")

if __name__ == "__main__":
    main()