import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import Navigation from "@/components/Navigation";
import { Mic, MicOff, Send, VolumeX, Volume2, RotateCcw, User, Bot } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  audioUrl?: string;
}

const CustomerChat = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      content: 'Hello! I\'m Voxaide, your AI support assistant. How can I help you today? You can speak to me or type your message.',
      timestamp: new Date()
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await sendAudioToServer(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      toast({
        title: "Microphone Error",
        description: "Could not access microphone. Please check permissions.",
        variant: "destructive"
      });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendAudioToServer = async (audioBlob: Blob) => {
    setIsLoading(true);
    
    // Add user message placeholder
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: 'Voice message...',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.wav');

      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const apiBaseUrl = isLocal ? 'http://localhost:5000' : 'https://voxaide-ai.onrender.com';

      const response = await fetch(`${apiBaseUrl}/talk`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        
        // Update user message with transcription
        setMessages(prev => prev.map(msg => 
          msg.id === userMessage.id 
            ? { ...msg, content: result.user_message || 'Voice message' }
            : msg
        ));

        // Add bot response
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'bot',
          content: result.response || 'I apologize, but I couldn\'t process your request.',
          timestamp: new Date(),
          audioUrl: result.audio_url
        };
        setMessages(prev => [...prev, botMessage]);

        // Auto-play response if audio is available
        if (result.audio_url) {
          playAudio(result.audio_url);
        }
      } else {
        throw new Error('Failed to get response from server');
      }
    } catch (error) {
      console.error('Error sending audio:', error);
      toast({
        title: "Connection Error",
        description: "Could not connect to Voxaide server. Please try again.",
        variant: "destructive"
      });
      
      // Remove the placeholder user message on error
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
    } finally {
      setIsLoading(false);
    }
  };

  const playAudio = async (audioUrl: string) => {
    try {
      setIsPlaying(true);
      const audio = new Audio(audioUrl);
      audio.onended = () => setIsPlaying(false);
      audio.onerror = () => {
        setIsPlaying(false);
        toast({
          title: "Audio Error",
          description: "Could not play audio response.",
          variant: "destructive"
        });
      };
      await audio.play();
    } catch (error) {
      console.error('Error playing audio:', error);
      setIsPlaying(false);
    }
  };

  const resetSession = async () => {
    try {
      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const apiBaseUrl = isLocal ? 'http://localhost:5000' : 'https://voxaide-ai.onrender.com';

      await fetch(`${apiBaseUrl}/reset`, { method: 'POST' });
      setMessages([{
        id: Date.now().toString(),
        type: 'bot',
        content: 'Session reset! How can I help you today?',
        timestamp: new Date()
      }]);
      toast({
        title: "Session Reset",
        description: "Started a new conversation."
      });
    } catch (error) {
      console.error('Error resetting session:', error);
      toast({
        title: "Reset Error",
        description: "Could not reset session. Please try again.",
        variant: "destructive"
      });
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="pt-16 pb-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold mb-2">
              Chat with <span className="gradient-text">Voxaide</span>
            </h1>
            <p className="text-muted-foreground">
              Try our AI voice assistant. Ask about orders, policies, or general support.
            </p>
          </div>

          {/* Chat Container */}
          <div className="bg-card rounded-2xl shadow-large border border-border overflow-hidden">
            {/* Messages */}
            <div className="h-96 overflow-y-auto p-6 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex items-start space-x-3 ${
                    message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}
                >
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.type === 'user' ? 'bg-primary' : 'bg-accent'
                  }`}>
                    {message.type === 'user' ? (
                      <User className="h-4 w-4 text-white" />
                    ) : (
                      <Bot className="h-4 w-4 text-white" />
                    )}
                  </div>
                  <div className={`flex-1 max-w-xs sm:max-w-md ${
                    message.type === 'user' ? 'text-right' : ''
                  }`}>
                    <div className={`inline-block px-4 py-2 rounded-2xl ${
                      message.type === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground'
                    }`}>
                      <p className="text-sm">{message.content}</p>
                    </div>
                    {message.audioUrl && message.type === 'bot' && (
                      <button
                        onClick={() => playAudio(message.audioUrl!)}
                        className="mt-2 text-xs text-primary hover:text-primary-hover flex items-center space-x-1"
                      >
                        {isPlaying ? <VolumeX className="h-3 w-3" /> : <Volume2 className="h-3 w-3" />}
                        <span>Play Audio</span>
                      </button>
                    )}
                    <div className="text-xs text-muted-foreground mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center">
                    <Bot className="h-4 w-4 text-white" />
                  </div>
                  <div className="bg-muted rounded-2xl px-4 py-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Controls */}
            <div className="border-t border-border p-6">
              <div className="flex items-center justify-center space-x-4">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={resetSession}
                  disabled={isLoading}
                >
                  <RotateCcw className="h-4 w-4" />
                </Button>
                
                <Button
                  variant={isRecording ? "destructive" : "hero"}
                  size="lg"
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={isLoading}
                  className="min-w-32"
                >
                  {isRecording ? (
                    <>
                      <MicOff className="mr-2 h-5 w-5" />
                      Stop
                    </>
                  ) : (
                    <>
                      <Mic className="mr-2 h-5 w-5" />
                      Speak
                    </>
                  )}
                </Button>

                <div className="text-xs text-muted-foreground text-center max-w-32">
                  {isRecording ? (
                    <span className="text-destructive">Recording...</span>
                  ) : isLoading ? (
                    "Processing..."
                  ) : (
                    "Press to speak"
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Demo Notice */}
          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              This is a demo environment. Try asking: "Where is my order ZMT1003?" or "What is your return policy?"
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CustomerChat;