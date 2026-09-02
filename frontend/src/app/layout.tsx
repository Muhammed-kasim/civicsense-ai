import type { Metadata } from 'next'
import './globals.css'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'CivicSense AI - Infrastructure Complaint System',
  description: 'AI-powered infrastructure complaint management',
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-lg transition-colors">
      {children}
    </Link>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center gap-2">
                <div className="text-2xl font-bold text-blue-600">CivicSense</div>
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">AI</span>
              </div>
              <div className="flex items-center gap-1">
                <NavLink href="/">Dashboard</NavLink>
                <NavLink href="/complaints/new">New Complaint</NavLink>
                <NavLink href="/complaints">All Complaints</NavLink>
                <NavLink href="/danger-zones">Danger Zones</NavLink>
                <NavLink href="/verify">Verify Fix</NavLink>
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  )
}
