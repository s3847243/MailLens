"use client";
import React, { useCallback, useEffect, useRef, useState } from 'react'
import { Textarea } from '../ui/textarea';
import { HiStop } from "react-icons/hi2";
import { FaArrowTurnUp } from "react-icons/fa6";
import { useParams, useRouter } from 'next/navigation';
import TypingDots from '../ui/TypingDots';
import { createChatSessions } from '../api/chatApi';
import { useChatSessions } from '@/context/ChatSessionContext';
import { useAskStream } from '@/hooks/useAskStream';
import { CitationPill } from '@/types';
import { CitationPills } from './CitationPills';
import EmailModal from './EmailModal';
// import { getChatSession } from '@/lib/chatApi';
// import { ChatSession } from '@/lib/types';
interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  citations?: CitationPill[]

}
type Params = { id: string };

const Main = () => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const router = useRouter();
  const [isGenerating, setIsGenerating] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [chatExists, setChatExists] = useState(false);
  const [showChatSetup, setShowChatSetup] = useState(false);
  const [isCreatingChat, setIsCreatingChat] = useState(false);
  const [isMessageLoading, setIsMessageLoading] = useState(false);
  const [isNearBottom, setIsNearBottom] = useState(true);
  const { updateChatMeta } = useChatSessions()
  const { start } = useAskStream()
  const initialChatIdRef = useRef<string | null>(null);
  const [previewCitation, setPreviewCitation] = useState<CitationPill | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  const streamRef = useRef<EventSource | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const messagesContainerRef = useRef<HTMLDivElement | null>(null);
  const forceScrollRef = useRef(false);


  const BOTTOM_THRESHOLD = 80; // px

  const calcIsNearBottom = () => {
    const el = messagesContainerRef.current;
    if (!el) return true;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    return distance <= BOTTOM_THRESHOLD;
  };

  const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior, block: "end" });
  };
  useEffect(() => {
    scrollToBottom("auto");
  }, []);


  useEffect(() => {
    if (forceScrollRef.current || isNearBottom) {
      scrollToBottom();       
      forceScrollRef.current = false;
    } 
  }, [messages, isMessageLoading, isNearBottom]);

  useEffect(() => {
    const onResize = () => {
      if (calcIsNearBottom()) scrollToBottom("auto");
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  
  const { id } = useParams<Params>();

  if (id && !initialChatIdRef.current) {
    initialChatIdRef.current = id;
  }
  const chatId = id ?? initialChatIdRef.current;
  const loadExistingChat = useCallback(async (chatId: string) => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/chats/${chatId}/messages`, {
        method: 'GET',
        "credentials": "include",
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Response:', data );
        setMessages(data.messages || []);
        setChatExists(true);
      } else if (response.status === 404) {
        
        router.push('/c');
        return;
      } else {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error loading chat:', error);
      router.push('/c');
    } finally {
      setIsLoading(false);
    }
  }, [router, setIsLoading, setMessages, setChatExists]);
  const startNewChat = async () => {
    try {
      setIsCreatingChat(true);
      const response = await createChatSessions();
      console.log(response);
      if (!response.id ) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      console.log('New chat started:', response);
      const newChatId = response.id;
      console.log('New chat ID:', newChatId);
      
      setChatExists(true);
      setShowChatSetup(false);
      
      router.push(`/c/${newChatId}`);
      
    } catch (error) {
      console.error('Error starting chat:', error);
      throw error;
    } finally {
      setIsCreatingChat(false);
    }
  };
const sendMessage = (question: string) => {
    if (!chatId || !question.trim() || isGenerating) return
    setIsGenerating(true)
    setIsMessageLoading(true);
    // temp user message
    const tempUserId = `u_${Date.now()}`
    const ts = new Date()
    setMessages(prev => [...prev, { id: tempUserId, role: 'user', content: question, timestamp: ts }])
    setInputValue('')

    // assistant streaming state
    const assistantId = `a_${Date.now()}`
    let assistantBuffer = ''
    let assistantShown = false

    const upsertAssistant = (content: string) => {
      setMessages(prev => {
        const last = prev[prev.length - 1]
        if (last && last.role === 'assistant' && last.id.startsWith('a_')) {
          const next = [...prev]
          next[next.length - 1] = { ...last, content }
          return next
        }
        return [...prev, { id: assistantId, role: 'assistant', content, timestamp: new Date() }]
      })
    }

    start(String(chatId), question, {
      onOpen: () => {
        console.log("searching")
      },
      onState: () => {
        // 'searching' | 'answering' 
        
      },
      onDelta: (delta) => {
                    
        setIsMessageLoading(false);
        if (!assistantShown) {
          assistantShown = true
          upsertAssistant('')
        }
        assistantBuffer += delta
        upsertAssistant(assistantBuffer)
        scrollToBottom()
      },
      onChat: (meta) => {
        // update sidebar title/ordering without a full refetch
        updateChatMeta(meta)
      },
      onFinal: ({ citations }) => {
        // attach citations to the last assistant bubble
        if (citations?.length) {
          setMessages(prev => {
            const next = [...prev]
            const i = [...next].reverse().findIndex(m => m.role === 'assistant')
            if (i !== -1) {
              const idx = next.length - 1 - i
              next[idx] = { ...next[idx], citations }
            }
            return next
          })
        }
        setIsGenerating(false)
        scrollToBottom()
      },
      onError: (err) => {
        console.error(err)
        setIsGenerating(false)
      },
      onClose: () => {
      },
    })
  }
useEffect(() => {
  return () => {
    if (streamRef.current) {
      streamRef.current.close();
      streamRef.current = null;
    }
  };
}, []);
  useEffect(() => {
    const initializeChat = async () => {
      if (id && id !== 'new') {
        await loadExistingChat(id);
      } else {
        setIsLoading(false);
        setChatExists(false);
        setShowChatSetup(true);
      }
    };

    initializeChat();
  }, [id, loadExistingChat]);
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
        textarea.style.height = 'auto'; 
        textarea.style.height = `${textarea.scrollHeight}px`;
    }
  };
  const handleGenerate = () => {
      const message = inputValue.trim();
      if (!message || isGenerating) return;

      setIsGenerating(true);
      setInputValue('');
      
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }

      try {
        sendMessage(message);
      } catch (error) {
        console.error('Error handling message:', error);
      } finally {
        setIsGenerating(false);
      }
    };

    const handleStartChat = async () => {
      if (isCreatingChat) return;
      
      try {
        await startNewChat();
      } catch (error) {
        console.error('Error starting chat:', error);
      }
    };


    if (isLoading) {
      return (
        <div className="w-full h-screen flex items-center justify-center">
          <div className="text-gray-500">Loading chat...</div>
        </div>
      );
    }

  return (
    <div className="w-full h-screen relative">
      <div className="flex flex-col h-full max-h-screen">
        <div className="border-b border-gray-200 px-4 py-3 bg-white">
          
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              
              <div className="flex flex-col">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-slate-500 via-blue-600 to-red-300 bg-clip-text text-transparent tracking-tight leading-tight">
                  {isLoading ? (
                    <span className="flex items-center space-x-2">
                      <span>Loading</span>
                      <div className="flex space-x-1">
                        <div className="w-1 h-1 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                        <div className="w-1 h-1 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                        <div className="w-1 h-1 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                      </div>
                    </span>
                  ) : (
                    // chat?.title ?? "Untitled Chat"
                    ""
                  )}
                </h1>
                
                <div className="flex items-center space-x-2 mt-0.5">
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse shadow-sm"></div>
                    <span className="text-xs text-gray-500 font-medium">
                      {isLoading ? "Initializing..." : "Active Session"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      <div 
        className="flex-1 overflow-y-auto px-4 py-6 space-y-6 bg-gradient-to-b from-slate-50 to-slate-100"
        ref={messagesContainerRef}
        onScroll={() => setIsNearBottom(calcIsNearBottom())}
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 space-y-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-400 to-blue-500 flex items-center justify-center shadow-lg animate-pulse">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p className="text-center">Start a conversation by typing a message below</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-4 fade-in-0 duration-500`}
              style={{
                animationDelay: `${index * 100}ms`
              }}
            >
              {message.role === 'assistant' && (
                <div className="flex-shrink-0 mr-3 mb-auto mt-1">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center shadow-lg border-2 border-white">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                </div>
              )}
              <div
                className={`relative max-w-[75%] px-5 py-3 shadow-lg backdrop-blur-sm border transition-all duration-300 hover:shadow-xl hover:scale-[1.02] ${
                  message.role === 'user'
                    ? 'bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-[20px] rounded-br-[8px] border-purple-400/30 shadow-purple-200/50'
                    : 'bg-white/80 text-gray-800 rounded-[20px] rounded-bl-[8px] border-gray-200/50 shadow-gray-200/50'
                }`}
              >
                <div className="relative z-10">
                  {message.content}
                </div>
                {message.role === 'assistant' && message.citations?.length ? (
                  <CitationPills
                    citations={message.citations}
                    onOpen={(c) => {
                      setPreviewCitation(c)
                      setModalOpen(true)
                    }}
                  />
                ) : null}
                
                <div 
                  className={`absolute inset-0 rounded-[20px] opacity-20 blur-xl -z-10 ${
                    message.role === 'user' 
                      ? 'bg-purple-500' 
                      : 'bg-blue-400'
                  }`}
                />

                <div
                  className={`absolute bottom-0 w-0 h-0 ${
                    message.role === 'user'
                      ? 'right-0 border-l-[12px] border-l-purple-500 border-t-[12px] border-t-transparent'
                      : 'left-0 border-r-[12px] border-r-white/80 border-t-[12px] border-t-transparent'
                  }`}
                />

                
              </div>

              {message.role === 'user' && (
                <div className="flex-shrink-0 ml-3 mb-auto mt-1">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center shadow-lg border-2 border-white">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                </div>
              )}
            </div>
            
          ))
          
        )}
          
          <EmailModal
                  open={modalOpen}
                  onClose={() => setModalOpen(false)}
                  pill={previewCitation}
            />
          {isMessageLoading && (
            <div className="relative max-w-[95%] rounded-lg px-4 py-2 bg-blue-100 text-gray-900 mr-auto shadow-sm">
              <div className="flex items-center gap-2">
                <TypingDots />
              </div>
            </div>
          )}
          
          {isGenerating && (
            <div className="relative max-w-[95%] rounded-lg px-4 py-1.5 bg-blue-100 text-gray-900 mr-auto shadow-sm">
              <div className="flex items-center space-x-2">
                <div className="animate-pulse">Thinking...</div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
            
        </div>
          

  {chatExists && (
    <div className="border-t border-gray-200/30 px-4 py-4 bg-gradient-to-t from-slate-100 to-white backdrop-blur-xl">
      <div className="max-w-4xl mx-auto relative">
        <div 
          className="group relative rounded-[24px] border-2 border-purple-200/50 bg-white/90 backdrop-blur-xl shadow-xl hover:shadow-2xl transition-all duration-300 hover:border-purple-300/60 cursor-text overflow-hidden"
          onClick={() => {
            if (textareaRef.current) {
              textareaRef.current.focus();
            }
          }}
        >
          <div className="absolute inset-0 rounded-[24px] bg-gradient-to-r from-purple-400/20 to-blue-400/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl -z-10" />
          
          <div className="relative p-4 pb-2">
            <Textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => {
                setInputValue(e.target.value);
                adjustTextareaHeight();
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleGenerate();
                }
              }}
              placeholder="Type any questions or messages here..."
              className="w-full h-fit resize-none bg-transparent focus:outline-none border-none max-h-[150px] text-gray-800 placeholder-gray-500 leading-relaxed pr-16 text-base"
              rows={1}
            />
            
            <div className="absolute right-2 bottom-2">
              <button 
                className={`group/btn relative p-3 rounded-full transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105 ${
                  isGenerating 
                    ? 'bg-red-500 hover:bg-red-600' 
                    : inputValue.trim() 
                      ? 'bg-gradient-to-br from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700' 
                      : 'bg-gray-300 hover:bg-gray-400'
                } ${inputValue.trim() || isGenerating ? 'text-white' : 'text-gray-600'}`}
                onClick={handleGenerate} 
                disabled={!inputValue.trim() && !isGenerating}
              >
                <div className={`absolute inset-0 rounded-full blur-lg opacity-30 transition-opacity duration-300 ${
                  isGenerating ? 'bg-red-400' : inputValue.trim() ? 'bg-purple-400' : 'bg-transparent'
                }`} />
                
                <div className="relative z-10">
                  {isGenerating ? (
                    <HiStop className="text-sm animate-pulse" />
                  ) : (
                    <FaArrowTurnUp className="text-sm transition-transform duration-200 group-hover/btn:translate-y-[-1px]" />
                  )}
                </div>
              </button>
            </div>
          </div>

          {/* Bottom Status Bar */}
          <div className="px-4 py-2 bg-gradient-to-r from-gray-50/50 to-purple-50/50 border-t border-gray-100/50">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
                  <span>Ready to chat</span>
                </div>
                {inputValue.length > 0 && (
                  <span className="text-gray-400">• {inputValue.length} characters</span>
                )}
              </div>
              <div className="text-gray-400">
                Press Enter to send • Shift+Enter for new line
                          </div>
                        </div>
                      </div>
                    </div>  
                  </div>
                </div>
              )}
        </div>

      
      {showChatSetup && (
        <div className="absolute inset-0 bg-red/80 backdrop-blur-md flex items-center justify-center z-50">
          <div className="bg-red/95 backdrop-blur-xl rounded-[24px] shadow-2xl border-2 border-black-200/50 p-8 max-w-md w-full mx-4 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-50/50 to-blue-50/50 rounded-[24px]" />
            
            <div className="relative z-10">
              <div className="flex flex-col items-center mb-8">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-red-500 to-blue-600 flex items-center justify-center shadow-lg mb-4">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-red-600 to-blue-600 bg-clip-text text-transparent text-center">
                  Start New Chat
                </h2>
              </div>

              <div className="space-y-6">
              
                <div className="flex space-x-3">
                  <button
                    onClick={handleStartChat}
                    disabled={ isCreatingChat}
                    className="flex-1 group relative px-6 py-4 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 disabled:from-gray-300 disabled:to-gray-400 text-white rounded-2xl font-semibold shadow-lg hover:shadow-xl disabled:shadow-none transition-all duration-300 transform hover:scale-[1.02] disabled:scale-100 disabled:cursor-not-allowed overflow-hidden"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-purple-400/30 to-blue-400/30 opacity-0 group-hover:opacity-100 group-disabled:opacity-0 transition-opacity duration-300 blur-lg" />
                    
                    <span className="relative z-10 flex items-center justify-center space-x-2">
                      {isCreatingChat ? (
                        <>
                          <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          <span>Creating...</span>
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                          </svg>
                          <span>Start Chat</span>
                        </>
                      )}
                    </span>
                  </button>
                </div>
            </div>
          </div>
        </div>
      </div>
    )}     
    </div>
  );
}

export default Main
