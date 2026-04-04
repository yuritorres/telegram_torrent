import toast from 'react-hot-toast';

export const useToast = () => {
    const success = (message) => toast.success(message, {
        style: {
            background: '#1e293b',
            color: '#e2e8f0',
            border: '1px solid #334155',
        },
        iconTheme: {
            primary: '#3b82f6',
            secondary: '#1e293b',
        }
    });

    const error = (message) => toast.error(message, {
        style: {
            background: '#1e293b',
            color: '#ef4444',
            border: '1px solid #7f1d1d',
        },
        iconTheme: {
            primary: '#ef4444',
            secondary: '#1e293b',
        }
    });

    const loading = (message) => toast.loading(message, {
        style: {
            background: '#1e293b',
            color: '#94a3b8',
            border: '1px solid #334155',
        }
    });

    const dismiss = (toastId) => toast.dismiss(toastId);

    const custom = (message, icon) => toast(message, {
        icon: icon,
        style: {
            background: '#1e293b',
            color: '#e2e8f0',
            border: '1px solid #334155',
        }
    });

    return { success, error, loading, dismiss, custom };
};
