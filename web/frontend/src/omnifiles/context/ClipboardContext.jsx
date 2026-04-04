import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useToast } from '../hooks/useToast';

const ClipboardContext = createContext();

export const useClipboard = () => {
    const context = useContext(ClipboardContext);
    if (!context) {
        throw new Error('useClipboard must be used within a ClipboardProvider');
    }
    return context;
};

export const ClipboardProvider = ({ children, onPaste }) => {
    // clipboard: { items: [{id, name, type, ...}], action: 'copy' | 'cut' }
    const [clipboard, setClipboard] = useState(null);
    const toaster = useToast();

    const copy = useCallback((items) => {
        if (!items || items.length === 0) return;
        setClipboard({ items, action: 'copy' });
        toaster.success(`${items.length} itens a copiar.`);
    }, []);

    const cut = useCallback((items) => {
        if (!items || items.length === 0) return;
        setClipboard({ items, action: 'cut' });
        toaster.custom(`${items.length} itens para mover.`, '✂️');
    }, []);

    const paste = useCallback(() => {
        if (!clipboard) return;
        if (onPaste) {
            onPaste(clipboard.items, clipboard.action);
        }

        // Se for recortar, limpa o clipboard após colar
        if (clipboard.action === 'cut') {
            setClipboard(null);
        }
    }, [clipboard, onPaste]);

    const clear = useCallback(() => {
        setClipboard(null);
    }, []);

    return (
        <ClipboardContext.Provider value={{ clipboard, copy, cut, paste, clear }}>
            {children}
        </ClipboardContext.Provider>
    );
};
