import React from 'react'
import OmniFilesApp from '../../omnifiles/OmniFilesApp'
import { Toaster } from 'react-hot-toast'
import { ModalProvider } from '../../omnifiles/context/ModalContext'
import '../../omnifiles/i18n'

const FileManagerApp = () => {
  return (
    <ModalProvider>
      <div className="h-full w-full">
        <OmniFilesApp />
        <Toaster position="bottom-right" />
      </div>
    </ModalProvider>
  )
}

export default FileManagerApp
