/**
 * WebSocket 통신 유틸리티
 * D-TAX BOT과의 실시간 채팅을 위한 WebSocket 연결 및 메시지 처리
 */

class WebSocketClient {
  constructor(url = 'ws://localhost:8000/ws/chat') {
    this.url = url;
    this.ws = null;
    this.connectionTimeout = null;
    this.isConnected = false;
    this.messageCallbacks = {
      onStart: null,
      onChunk: null,
      onDone: null,
      onError: null,
      onConnect: null,
      onDisconnect: null
    };
  }

  /**
   * WebSocket 연결 설정
   * @param {Object} options - 연결 옵션
   * @param {number} options.timeout - 연결 타임아웃 (ms)
   * @param {Function} options.onConnect - 연결 성공 콜백
   * @param {Function} options.onDisconnect - 연결 해제 콜백
   */
  connect(options = {}) {
    const { timeout = 5000, onConnect, onDisconnect } = options;
    
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
        
        // 연결 타임아웃 설정
        this.connectionTimeout = setTimeout(() => {
          if (this.ws.readyState !== WebSocket.OPEN) {
            this.ws.close();
            reject(new Error('연결 시간이 초과되었습니다.'));
          }
        }, timeout);

        this.ws.onopen = () => {
          console.log('WebSocket 연결됨');
          this.isConnected = true;
          clearTimeout(this.connectionTimeout);
          
          if (onConnect) onConnect();
          if (this.messageCallbacks.onConnect) this.messageCallbacks.onConnect();
          resolve();
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket 연결 종료', event.code, event.reason);
          this.isConnected = false;
          clearTimeout(this.connectionTimeout);
          
          if (onDisconnect) onDisconnect(event);
          if (this.messageCallbacks.onDisconnect) this.messageCallbacks.onDisconnect(event);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket 오류:', error);
          this.isConnected = false;
          clearTimeout(this.connectionTimeout);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 메시지 전송
   * @param {string} message - 전송할 메시지
   */
  sendMessage(message) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket이 연결되지 않았습니다.');
    }
    
    this.ws.send(JSON.stringify({ message }));
  }

  /**
   * 메시지 수신 처리 설정
   * @param {Object} callbacks - 콜백 함수들
   * @param {Function} callbacks.onStart - 스트리밍 시작 콜백
   * @param {Function} callbacks.onChunk - 청크 수신 콜백
   * @param {Function} callbacks.onDone - 스트리밍 완료 콜백
   * @param {Function} callbacks.onError - 오류 콜백
   */
  onMessage(callbacks) {
    this.messageCallbacks = { ...this.messageCallbacks, ...callbacks };
    
    if (this.ws) {
      this.ws.onmessage = (event) => {
        this.handleMessage(event);
      };
    }
  }

  /**
   * 메시지 처리
   * @param {MessageEvent} event - WebSocket 메시지 이벤트
   */
  handleMessage(event) {
    console.log('받은 메시지:', event.data);
    
    try {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'start':
          console.log('스트리밍 시작');
          if (this.messageCallbacks.onStart) {
            this.messageCallbacks.onStart();
          }
          break;
          
        case 'chunk':
          console.log('청크 내용:', data.content);
          if (this.messageCallbacks.onChunk) {
            this.messageCallbacks.onChunk(data.content);
          }
          break;
          
        case 'done':
          console.log('스트리밍 완료');
          if (this.messageCallbacks.onDone) {
            this.messageCallbacks.onDone();
          }
          break;
          
        case 'error':
          console.error('서버 오류:', data.message);
          if (this.messageCallbacks.onError) {
            this.messageCallbacks.onError(data.message);
          }
          break;
          
        default:
          console.warn('알 수 없는 메시지 타입:', data.type);
      }
    } catch (parseError) {
      console.error('JSON 파싱 오류:', parseError, 'Raw data:', event.data);
      // JSON 파싱 실패시 원본 데이터 처리
      if (typeof event.data === 'string' && event.data.trim()) {
        if (this.messageCallbacks.onChunk) {
          this.messageCallbacks.onChunk(event.data);
        }
      }
    }
  }

  /**
   * 연결 종료
   */
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, '사용자 요청');
      this.isConnected = false;
      clearTimeout(this.connectionTimeout);
    }
  }

  /**
   * 연결 상태 확인
   * @returns {boolean} 연결 상태
   */
  isConnected() {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }
}

/**
 * 채팅 메시지 전송 및 스트리밍 처리
 * @param {string} message - 전송할 메시지
 * @param {Object} options - 옵션
 * @param {Function} options.onStart - 스트리밍 시작 콜백
 * @param {Function} options.onChunk - 청크 수신 콜백
 * @param {Function} options.onDone - 스트리밍 완료 콜백
 * @param {Function} options.onError - 오류 콜백
 * @returns {Promise} 처리 결과
 */
export const sendChatMessage = async (message, options = {}) => {
  const wsClient = new WebSocketClient();
  
  try {
    await wsClient.connect({
      timeout: 5000,
      onConnect: () => {
        console.log('채팅 연결 성공');
        if (options.onStart) options.onStart();
      },
      onDisconnect: (event) => {
        console.log('채팅 연결 종료:', event);
      }
    });

    wsClient.onMessage({
      onStart: () => {
        if (options.onStart) options.onStart();
      },
      onChunk: (content) => {
        if (options.onChunk) options.onChunk(content);
      },
      onDone: () => {
        if (options.onDone) options.onDone();
        wsClient.disconnect();
      },
      onError: (errorMessage) => {
        if (options.onError) options.onError(errorMessage);
        wsClient.disconnect();
      }
    });

    wsClient.sendMessage(message);
    
  } catch (error) {
    console.error('WebSocket 연결 실패:', error);
    if (options.onError) {
      options.onError(error.message);
    }
    wsClient.disconnect();
  }
};

export default WebSocketClient; 