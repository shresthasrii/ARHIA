import { AssistantState } from '../types';

type MessageHandler = (data: any) => void;

class ArhieaWebSocketService {
  private socket: WebSocket | null = null;
  private handlers: Set<MessageHandler> = new Set();
  private reconnectInterval: number = 2000;
  private isConnected: boolean = false;
  private currentAudio: HTMLAudioElement | null = null;

  public getWsUrl(): string {
    const isHttps = window.location.protocol === 'https:';
    const protocol = isHttps ? 'wss:' : 'ws:';
    const host = window.location.port === '5173'
      ? `${window.location.hostname}:8000`
      : (window.location.host || '127.0.0.1:8000');
    return `${protocol}//${host}/ws`;
  }

  public connect(url?: string) {
    const targetUrl = url || this.getWsUrl();
    try {
      this.socket = new WebSocket(targetUrl);

      this.socket.onopen = () => {
        this.isConnected = true;
        console.log('[ARHIEA WS] Connected to backend engine at', targetUrl);
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleIncoming(data);
        } catch (e) {
          console.error('[ARHIEA WS] Parse error:', e);
        }
      };

      this.socket.onclose = () => {
        this.isConnected = false;
        console.warn('[ARHIEA WS] Disconnected. Reconnecting in 2s...');
        setTimeout(() => this.connect(targetUrl), this.reconnectInterval);
      };

      this.socket.onerror = (err) => {
        console.error('[ARHIEA WS] WebSocket error:', err);
      };
    } catch (e) {
      console.error('[ARHIEA WS] Connection initiation error:', e);
    }
  }

  public subscribe(handler: MessageHandler): () => void {
    this.handlers.add(handler);
    return () => {
      this.handlers.delete(handler);
    };
  }

  public send(data: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.warn('[ARHIEA WS] Socket not open, failed to send:', data);
    }
  }

  public sendMessage(text: string, isVoice: boolean = false) {
    this.send({
      type: 'message',
      text,
      is_voice: isVoice
    });
  }

  public bargeIn() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }
    if ('speechSynthesis' in window && window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
    }
    this.send({ type: 'barge_in' });
  }

  public playAudioBase64(base64Data: string, onEnded?: () => void) {
    try {
      if (this.currentAudio) {
        this.currentAudio.pause();
      }
      const audioUrl = `data:audio/mp3;base64,${base64Data}`;
      this.currentAudio = new Audio(audioUrl);
      this.currentAudio.onended = () => {
        this.currentAudio = null;
        if (onEnded) onEnded();
      };
      this.currentAudio.play().catch((err) => {
        console.warn('[ARHIEA Audio] Play notice:', err);
      });
    } catch (e) {
      console.error('[ARHIEA Audio] Failed to play audio:', e);
    }
  }

  public speakBrowserSpeech(text: string) {
    try {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const clean = text.replace(/[`*#_~\[\]]/g, ' ').replace(/\s+/g, ' ').trim();
        if (clean) {
          const utterance = new SpeechSynthesisUtterance(clean);
          utterance.rate = 1.05;
          utterance.pitch = 1.0;
          window.speechSynthesis.speak(utterance);
        }
      }
    } catch (e) {
      console.debug('[ARHIEA Browser Speech] Notice:', e);
    }
  }

  private handleIncoming(data: any) {
    if (data.audio_base64) {
      this.playAudioBase64(data.audio_base64);
    } else if (data.type === 'agent_response' && data.is_voice && data.response) {
      this.speakBrowserSpeech(data.response);
    }
    this.handlers.forEach((h) => h(data));
  }
}

export const wsService = new ArhieaWebSocketService();
