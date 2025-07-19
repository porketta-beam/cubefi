#!/usr/bin/env python3
"""
Test script for empty VectorDB exception handling
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

def test_empty_vectordb_api():
    """Test API endpoints with empty VectorDB"""
    print("=== Testing Empty VectorDB API Endpoints ===")
    
    # Test RAG chat with empty DB
    print("\n1. Testing RAG chat with empty VectorDB:")
    chat_data = {
        "question": "What is tax law?",
        "model": "gpt-4o-mini",
        "temperature": 0.0,
        "search_type": "similarity",
        "k": 3
    }
    
    response = requests.post(f"{BASE_URL}/api/rag/chat", json=chat_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Answer: {result['answer']}")
        print(f"Success: {result['success']}")
    else:
        print(f"Error: {response.text}")
    
    # Test question generation with empty DB
    print("\n2. Testing question generation with empty VectorDB:")
    question_data = {
        "model": "gpt-4o-mini",
        "temperature": 0.9,
        "num_questions": 3
    }
    
    response = requests.post(f"{BASE_URL}/api/rag/generate-questions", json=question_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Questions: {result['questions']}")
        print(f"Success: {result['success']}")
        if not result['success']:
            print(f"Error: {result['error']}")
    else:
        print(f"Error: {response.text}")
    
    # Test evaluation with empty DB
    print("\n3. Testing evaluation with empty VectorDB:")
    eval_data = {
        "questions": ["What is tax law?", "How do I calculate tax?"],
        "model": "gpt-4o-mini",
        "temperature": 0.0,
        "search_type": "similarity",
        "k": 5
    }
    
    response = requests.post(f"{BASE_URL}/api/rag/evaluate", json=eval_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Results: {len(result['results'])} items")
        print(f"Success: {result['success']}")
        if not result['success']:
            print(f"Error: {result['error']}")
    else:
        print(f"Error: {response.text}")

async def test_empty_vectordb_websocket():
    """Test WebSocket with empty VectorDB"""
    print("\n=== Testing Empty VectorDB WebSocket ===")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("WebSocket connected successfully")
            
            # Test question with empty DB
            test_question = "What is tax law?"
            message = {"message": test_question}
            
            print(f"Sending question: {test_question}")
            await websocket.send(json.dumps(message))
            
            # Receive response
            response = await asyncio.wait_for(websocket.recv(), timeout=30)
            data = json.loads(response)
            
            print(f"Response type: {data['type']}")
            print(f"Response message: {data['message']}")
            
            # Test empty question
            print("\nTesting empty question:")
            empty_message = {"message": ""}
            await websocket.send(json.dumps(empty_message))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            data = json.loads(response)
            
            print(f"Empty question response: {data['message']}")
            
    except Exception as e:
        print(f"WebSocket test error: {e}")

def test_input_validation():
    """Test input validation"""
    print("\n=== Testing Input Validation ===")
    
    # Test with empty question
    print("\n1. Testing empty question:")
    chat_data = {
        "question": "",
        "model": "gpt-4o-mini"
    }
    
    response = requests.post(f"{BASE_URL}/api/rag/chat", json=chat_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Answer: {result['answer']}")
        print(f"Success: {result['success']}")
    
    # Test with invalid number of questions
    print("\n2. Testing invalid number of questions:")
    question_data = {
        "model": "gpt-4o-mini",
        "num_questions": 0
    }
    
    response = requests.post(f"{BASE_URL}/api/rag/generate-questions", json=question_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result['success']}")
        if not result['success']:
            print(f"Error: {result['error']}")
    
    # Test evaluation with no questions
    print("\n3. Testing evaluation with no questions:")
    eval_data = {
        "questions": [],
        "model": "gpt-4o-mini"
    }
    
    response = requests.post(f"{BASE_URL}/api/rag/evaluate", json=eval_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result['success']}")
        if not result['success']:
            print(f"Error: {result['error']}")

def main():
    """Run all tests"""
    print("=== Empty VectorDB Exception Handling Tests ===")
    
    # Start server
    server_proc = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'server:app', '--port', '8001'], 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    print("Starting server...")
    sleep(5)
    
    try:
        # Test API endpoints
        test_empty_vectordb_api()
        test_input_validation()
        
        # Test WebSocket
        print("\nTesting WebSocket...")
        asyncio.run(test_empty_vectordb_websocket())
        
        print("\n=== All Tests Completed ===")
        
    except Exception as e:
        print(f"Test error: {e}")
    finally:
        # Stop server
        server_proc.terminate()
        server_proc.wait()
        print("Server stopped")

if __name__ == "__main__":
    main()