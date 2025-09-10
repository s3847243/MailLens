
'use client'

import { useState } from 'react'
import Link from 'next/link'
import { api } from '@/components/api/axiosInstance'

const GoogleIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24">
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
  </svg>
)

interface FeatureCardProps {
  icon: string
  title: string
  description: string
}

const FeatureCard = ({ icon, title, description }: FeatureCardProps) => (
  <div className="card-hover bg-white p-8 rounded-2xl shadow-soft border border-gray-200/50">
    <div className="w-12 h-12 bg-gradient-to-br from-accent-light to-accent rounded-xl flex items-center justify-center mb-4 text-2xl">
      {icon}
    </div>
    <h3 className="text-xl font-semibold text-gray-800 mb-2">{title}</h3>
    <p className="text-gray-500 leading-relaxed">{description}</p>
  </div>
)

const Header = () => (
  <header className="glass-effect py-6">
    <div className="max-w-6xl mx-auto px-8">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-lg flex items-center justify-center text-white font-semibold">
            ML
          </div>
          <span className="text-xl font-bold text-gray-900">MailLens</span>
        </div>
        <nav className="hidden md:block">
          <ul className="flex gap-8">
            <li><Link href="#features" className="text-gray-500 hover:text-primary-600 font-medium transition-colors">Features</Link></li>
            <li><Link href="#privacy" className="text-gray-500 hover:text-primary-600 font-medium transition-colors">Privacy</Link></li>
            <li><Link href="#about" className="text-gray-500 hover:text-primary-600 font-medium transition-colors">About</Link></li>
          </ul>
        </nav>
      </div>
    </div>
  </header>
)

const HeroSection = () => (
  <div className="text-center max-w-4xl mx-auto mb-12 animate-fade-in">
    <h1 className="text-hero md:text-hero-mobile gradient-text mb-6">
      Unlock the Power of Your Gmail
    </h1>
    <p className="text-xl text-gray-500 mb-8 leading-relaxed max-w-2xl mx-auto">
      MailLens uses AI to analyze your emails, helping you find information, track conversations, 
      and get insights from your inbox like never before.
    </p>
  </div>
)

const ConnectSection = () => {
  const [isConnecting, setIsConnecting] = useState(false)
  const handleGoogleConnect = async () => {
  try {
      setIsConnecting(true)

      // call backend with axios
      const res = await api.get('/auth/google/login')
      const data = res.data

      if (!data.auth_url) throw new Error('No auth_url')
      window.location.href = data.auth_url
    } catch (e) {
      console.error(e)
      setIsConnecting(false)
    }
  }

  return (
    <div className="bg-white rounded-4xl p-10 shadow-large border border-gray-200/50 mb-12 min-w-96 animate-slide-up">
      <h2 className="text-2xl font-semibold text-gray-800 mb-4 text-center">
        Get Started in Seconds
      </h2>
      <p className="text-gray-500 mb-8 text-center leading-relaxed">
        Connect your Gmail account securely and start asking questions about your emails instantly.
      </p>
      
      <button
        onClick={handleGoogleConnect}
        disabled={isConnecting}
        className="button-hover w-full flex items-center justify-center gap-3 bg-white text-gray-700 border-2 border-gray-200 px-8 py-4 rounded-xl font-semibold text-lg shadow-medium hover:border-primary-300 hover:shadow-glow disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isConnecting ? (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
        ) : (
          <GoogleIcon />
        )}
        {isConnecting ? 'Connecting...' : 'Connect with Google'}
      </button>
      
      <div className="mt-6 p-4 bg-blue-50/70 border-l-4 border-primary-400 rounded-lg">
        <p className="text-primary-800 text-sm flex items-center gap-2">
          <span>🔒</span>
          Your data is encrypted and secure. We only access your emails to provide the analysis you request.
        </p>
      </div>
    </div>
  )
}

const FeaturesGrid = () => {
  const features = [
    {
      icon: '🔍',
      title: 'Smart Search',
      description: 'Ask questions in natural language and get precise answers from your email history.'
    },
    {
      icon: '📊',
      title: 'Email Insights',
      description: 'Get analytics on your communication patterns, response times, and email trends.'
    },
    {
      icon: '🤖',
      title: 'AI-Powered',
      description: 'Powered by advanced AI to understand context and provide meaningful responses.'
    }
  ]

  return (
    <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto mt-12">
      {features.map((feature, index) => (
        <FeatureCard key={index} {...feature} />
      ))}
    </div>
  )
}

export default function HomePage() {
  return (
    <>
      <Header />
      <main className="flex flex-col items-center justify-center min-h-[calc(100vh-100px)] px-8 py-16">
        <div className="max-w-6xl mx-auto">
          <HeroSection />
          <div className="flex justify-center">
            <ConnectSection />
          </div>
          <FeaturesGrid />
        </div>
      </main>
    </>
  )
}