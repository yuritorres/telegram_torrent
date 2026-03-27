import React, { useState, useEffect } from 'react'
import axios from '../utils/axios'

const AuthenticatedImage = ({ src, alt, className, fallback = null }) => {
  const [imageSrc, setImageSrc] = useState(null)
  const [error, setError] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!src) {
      setLoading(false)
      setError(true)
      return
    }

    const loadImage = async () => {
      try {
        setLoading(true)
        setError(false)
        
        const response = await axios.get(src, {
          responseType: 'blob',
        })

        const imageUrl = URL.createObjectURL(response.data)
        setImageSrc(imageUrl)
        setLoading(false)
      } catch (err) {
        console.error('Error loading authenticated image:', err)
        setError(true)
        setLoading(false)
      }
    }

    loadImage()

    return () => {
      if (imageSrc) {
        URL.revokeObjectURL(imageSrc)
      }
    }
  }, [src])

  if (loading) {
    return (
      <div className={`${className} bg-gray-800 animate-pulse flex items-center justify-center`}>
        <div className="w-8 h-8 border-2 border-gray-600 border-t-gray-400 rounded-full animate-spin"></div>
      </div>
    )
  }

  if (error || !imageSrc) {
    if (fallback) {
      return fallback
    }
    return (
      <div className={`${className} bg-gray-800 flex items-center justify-center text-gray-500`}>
        <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
    )
  }

  return <img src={imageSrc} alt={alt} className={className} />
}

export default AuthenticatedImage
