import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'GEOScope',
  description: 'AI 搜索引擎可见性分析',
}

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  )
}

