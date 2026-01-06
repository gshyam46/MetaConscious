'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { apiRequest } from '@/lib/api-config';

export function ChatInterface({ onPlanGenerated, onDataChanged }) {
  const CHAT_STORAGE_KEY = 'metaconscious_chat_history';
  const MAX_STORED_MESSAGES = 50; // Limit storage size
  
  // Initialize messages from localStorage or default
  const [messages, setMessages] = useState(() => {
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem(CHAT_STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
          // Convert timestamp strings back to Date objects
          return parsed.map(msg => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }));
        }
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    }
    // Default welcome message
    return [
      {
        id: 1,
        type: 'ai',
        content: 'I\'m MetaConscious, your autonomous planning assistant. I have FINAL AUTHORITY over your schedule. Ask me about your tasks, goals, or planning decisions.',
        timestamp: new Date()
      }
    ];
  });
  
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef(null);
  const inputRef = useRef(null);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (typeof window !== 'undefined' && messages.length > 0) {
      try {
        // Keep only the most recent messages to avoid storage limits
        const messagesToStore = messages.slice(-MAX_STORED_MESSAGES);
        localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messagesToStore));
      } catch (error) {
        console.error('Failed to save chat history:', error);
      }
    }
  }, [messages]);

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await apiRequest('/api/chat', {
        method: 'POST',
        body: JSON.stringify({
          content: userMessage.content,
          timestamp: userMessage.timestamp.toISOString()
        })
      });

      if (response.ok) {
        const data = await response.json();
        const aiMessage = {
          id: Date.now() + 1,
          type: 'ai',
          content: data.response,
          timestamp: new Date(data.timestamp),
          actions: data.suggestions || []
        };
        setMessages(prev => [...prev, aiMessage]);
        
        // Check if plan was updated and notify parent
        if (data.plan_updated && onPlanGenerated) {
          onPlanGenerated();
        }
        
        // Check if any data changed and notify parent
        if (data.context_used && onDataChanged) {
          onDataChanged();
        }
      } else {
        throw new Error('Failed to get AI response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      
      // Determine error type and provide specific feedback
      let errorMessage = 'I\'m temporarily unavailable. Please try again.';
      let toastMessage = 'Failed to get AI response';
      
      if (error.message?.includes('fetch')) {
        errorMessage = 'I\'m having trouble connecting to the server. Please check your internet connection and try again.';
        toastMessage = 'Network error - check your connection';
      } else if (error.message?.includes('timeout')) {
        errorMessage = 'The request took too long. Please try again with a shorter message.';
        toastMessage = 'Request timeout';
      } else if (error.message?.includes('rate limit')) {
        errorMessage = 'I\'m receiving too many requests right now. Please wait a moment before trying again.';
        toastMessage = 'Rate limit exceeded';
      }
      
      toast.error(toastMessage);
      const errorMsg = {
        id: Date.now() + 1,
        type: 'ai',
        content: errorMessage,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleActionClick = async (action) => {
    try {
      const response = await apiRequest('/api/chat/action', {
        method: 'POST',
        body: JSON.stringify(action)
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          toast.success(result.message || 'Action completed successfully');
          
          // Notify parent components of data changes
          if (onDataChanged) {
            onDataChanged();
          }
          
          // If plan was regenerated, notify parent
          if (result.plan_regenerated && onPlanGenerated) {
            onPlanGenerated();
          }
          
          // Add a system message about the action
          const systemMessage = {
            id: Date.now(),
            type: 'ai',
            content: `✅ ${result.message}${result.plan_regenerated ? ' I also regenerated your daily plan to incorporate these new priorities.' : ''}`,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, systemMessage]);
        } else {
          toast.error(result.error || 'Action failed');
          
          // Add error message to chat
          const errorMessage = {
            id: Date.now(),
            type: 'ai',
            content: `❌ Failed to execute action: ${result.error || 'Unknown error'}`,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, errorMessage]);
        }
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to execute action');
      }
    } catch (error) {
      console.error('Action error:', error);
      toast.error(error.message || 'Failed to execute action');
      
      // Add error message to chat
      const errorMessage = {
        id: Date.now(),
        type: 'ai',
        content: `❌ Action failed: ${error.message || 'Please try again'}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5" />
          AI Planning Assistant
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col p-0">
        <ScrollArea ref={scrollAreaRef} className="flex-1 px-4 max-h-[480px]">
          <div className="space-y-4 pb-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.type === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.type === 'ai' && (
                  <div className="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                    <Bot className="h-4 w-4 text-primary-foreground" />
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-lg px-3 py-2 break-words ${
                    message.type === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
                  <p className="text-xs opacity-70 mt-1">
                    {formatTime(message.timestamp)}
                  </p>
                  
                  {/* Action buttons for AI messages */}
                  {message.type === 'ai' && message.actions && message.actions.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {message.actions.map((action, idx) => (
                        <Button
                          key={idx}
                          size="sm"
                          variant="outline"
                          onClick={() => handleActionClick(action)}
                          className="text-xs h-7"
                        >
                          {action.label}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
                {message.type === 'user' && (
                  <div className="flex-shrink-0 w-8 h-8 bg-secondary rounded-full flex items-center justify-center">
                    <User className="h-4 w-4 text-secondary-foreground" />
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-3 justify-start">
                <div className="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary-foreground" />
                </div>
                <div className="bg-muted rounded-lg px-3 py-2">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-muted-foreground">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
        <div className="border-t p-4">
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about your tasks, goals, or planning decisions..."
              disabled={isLoading}
              className="flex-1"
            />
            <Button type="submit" disabled={isLoading || !inputValue.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  );
}