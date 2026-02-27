/**
 * MindWall — Sidebar Navigation
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React from 'react'
import { NavLink } from 'react-router-dom'
import { Shield, LayoutDashboard, Bell, Users, Settings, ExternalLink } from 'lucide-react'
import clsx from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Alerts', href: '/alerts', icon: Bell },
  { name: 'Employees', href: '/employees', icon: Users },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Sidebar() {
  return (
    <div className="flex flex-col w-64 bg-gray-900 border-r border-gray-800 min-h-screen">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-800">
        <Shield className="h-8 w-8 text-mindwall-500" />
        <div>
          <h1 className="text-lg font-bold text-white">MindWall</h1>
          <p className="text-xs text-gray-500">Cognitive Firewall</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-mindwall-600/10 text-mindwall-400 border border-mindwall-500/20'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              )
            }
          >
            <item.icon className="h-5 w-5" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-gray-800">
        <div className="text-xs text-gray-600">
          <p>Developed by</p>
          <a 
            href="https://pradyumntandon.com" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-gray-500 hover:text-mindwall-400 flex items-center gap-1 mt-1"
          >
            Pradyumn Tandon <ExternalLink className="h-3 w-3" />
          </a>
          <a 
            href="https://vrip7.com" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-gray-500 hover:text-mindwall-400 flex items-center gap-1 mt-0.5"
          >
            VRIP7 <ExternalLink className="h-3 w-3" />
          </a>
        </div>
        <p className="text-xs text-gray-700 mt-2">v1.0.0</p>
      </div>
    </div>
  )
}
