import { createContext, useContext, useState, useCallback } from 'react';
import { InputModal } from '../components/core/InputModal';
import { ConfirmModal } from '../components/core/ConfirmModal';

const ModalContext = createContext();

export function ModalProvider({ children }) {
    const [inputModal, setInputModal] = useState({
        isOpen: false,
        title: '',
        initialValue: '',
        placeholder: '',
        onConfirm: () => { }
    });

    const [confirmModal, setConfirmModal] = useState({
        isOpen: false,
        title: '',
        message: '',
        confirmText: 'Confirmar',
        isDanger: false,
        onConfirm: () => { }
    });

    const closeInput = useCallback(() => {
        setInputModal(prev => ({ ...prev, isOpen: false }));
    }, []);

    const openInput = useCallback(({ title, initialValue = '', placeholder = '', onConfirm }) => {
        setInputModal({
            isOpen: true,
            title,
            initialValue,
            placeholder,
            onConfirm: (value) => {
                onConfirm(value);
                closeInput();
            }
        });
    }, [closeInput]);

    const closeConfirm = useCallback(() => {
        setConfirmModal(prev => ({ ...prev, isOpen: false }));
    }, []);

    const openConfirm = useCallback(({ title, message, confirmText = 'Confirmar', isDanger = false, onConfirm }) => {
        setConfirmModal({
            isOpen: true,
            title,
            message,
            confirmText,
            isDanger,
            onConfirm: () => {
                onConfirm();
                closeConfirm();
            }
        });
    }, [closeConfirm]);

    return (
        <ModalContext.Provider value={{ openInput, closeInput, openConfirm, closeConfirm }}>
            {children}
            {/* Global Modals Rendered Here */}
            <InputModal
                isOpen={inputModal.isOpen}
                title={inputModal.title}
                initialValue={inputModal.initialValue}
                placeholder={inputModal.placeholder}
                onClose={closeInput}
                onConfirm={inputModal.onConfirm}
            />
            <ConfirmModal
                isOpen={confirmModal.isOpen}
                title={confirmModal.title}
                message={confirmModal.message}
                confirmText={confirmModal.confirmText}
                isDanger={confirmModal.isDanger}
                onClose={closeConfirm}
                onConfirm={confirmModal.onConfirm}
            />
        </ModalContext.Provider>
    );
}

export function useModal() {
    const context = useContext(ModalContext);
    if (!context) {
        throw new Error('useModal must be used within a ModalProvider');
    }
    return context;
}
