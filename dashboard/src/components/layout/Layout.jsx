/**
 * MindWall — Layout Component
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React from 'react'
import Sidebar from './Sidebar'
import TopBar from './TopBar'

export default function Layout({ children }) {
  return (
    <div className="flex min-h-screen bg-gray-950">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <TopBar />
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
