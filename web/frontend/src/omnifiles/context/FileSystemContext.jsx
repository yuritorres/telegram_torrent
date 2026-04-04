import React, { createContext, useContext, useEffect } from 'react';
import { useFileSystemInternal } from '../hooks/useFileSystem';

const FileSystemContext = createContext(null);

export const FileSystemProvider = ({ children }) => {
    const fs = useFileSystemInternal();

    // Debug Context Value
    useEffect(() => {
        if (!fs) {
            console.error("FileSystemProvider: FS Context is null/undefined!");
        } else {
            console.log("FileSystemProvider: FS Context initialized.");
        }
    }, [fs]);

    // Safety check: if fs is somehow null/undefined (e.g. hook crash?), provide empty or fallback?
    // But hook shouldn't return null.

    return (
        <FileSystemContext.Provider value={fs}>
            {children}
        </FileSystemContext.Provider>
    );
};

export const useFileSystem = () => {
    const context = useContext(FileSystemContext);
    if (!context) {
        throw new Error("useFileSystem must be used within a FileSystemProvider");
    }
    return context;
};
