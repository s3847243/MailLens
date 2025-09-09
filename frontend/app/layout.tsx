import type { Metadata , Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Inter } from 'next/font/google'


const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});


const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'MailLens - AI-Powered Email Analysis',
  description: 'Unlock the power of your Gmail with AI. Analyze your emails, find information, track conversations, and get insights from your inbox like never before.',
  keywords: ['email analysis', 'Gmail AI', 'email search', 'email insights', 'RAG application'],
  authors: [{ name: 'MailLens Team' }],
  openGraph: {
    title: 'MailLens - AI-Powered Email Analysis',
    description: 'Unlock the power of your Gmail with AI. Get instant insights from your email history.',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'MailLens - AI-Powered Email Analysis',
    description: 'Unlock the power of your Gmail with AI. Get instant insights from your email history.',
  },
  robots: 'index, follow',
}
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.className} antialiased`}
      >
        
        {children}
      </body>
    </html>
  );
}
