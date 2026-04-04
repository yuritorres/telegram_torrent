import { useState } from 'react';
import { Plug, X } from 'lucide-react';
import { SERVICE_CATALOG } from '../../constants/services';
import { useGoogleAuth } from '../../hooks/useGoogleAuth';

export const AddServiceModal = ({ onClose, onAdd }) => {
    const [step, setStep] = useState(1);
    const [selectedService, setSelectedService] = useState(null);
    const [customName, setCustomName] = useState('');
    const [isAuthenticating, setIsAuthenticating] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [authData, setAuthData] = useState(null);

    const { login, isInitialized } = useGoogleAuth();

    const handleSelect = (service) => {
        setSelectedService(service);
        setCustomName(service.name);
        // Reset auth state
        setIsAuthenticated(false);
        setAuthData(null);
        setStep(2);
    };

    const handleConnect = async () => {
        if (selectedService.id === 'google-drive') {
            setIsAuthenticating(true);
            try {
                const token = await login();

                // Fetch User Info
                const userInfoRes = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
                    headers: { Authorization: `Bearer ${token}` }
                });
                const userInfo = await userInfoRes.json();

                setIsAuthenticated(true);
                setAuthData({ token, email: userInfo.email, name: userInfo.name, picture: userInfo.picture });
                setCustomName(`Google Drive (${userInfo.email})`);

            } catch (error) {
                console.error("Google Auth Failed", error);
                alert("Falha na autenticação Google. Verifique se o Client ID está configurado no .env");
            } finally {
                setIsAuthenticating(false);
            }
        } else {
            // Dropbox Mock (Still mock for now as we focus on Google)
            setIsAuthenticating(true);
            setTimeout(() => {
                const mockEmail = "dropbox@exemplo.com";
                setIsAuthenticating(false);
                setIsAuthenticated(true);
                setAuthData({ token: 'mock-dropbox-' + Date.now(), email: mockEmail });
                setCustomName(`${selectedService.name} (${mockEmail})`);
            }, 1500);
        }
    };

    const handleConfirm = () => {
        if (!customName.trim()) return;
        // Pass auth data to parent
        onAdd(selectedService, customName, authData);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-[60] bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 w-full max-w-2xl rounded-2xl border border-slate-700 shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
                <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-800/50">
                    <h3 className="font-bold text-white flex items-center gap-2"><Plug size={18} className="text-blue-400" /> Adicionar Nova Conexão</h3>
                    <button onClick={onClose}><X size={20} className="text-slate-400 hover:text-white" /></button>
                </div>
                <div className="p-6">
                    {step === 1 ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {SERVICE_CATALOG.map(service => (
                                <button
                                    key={service.id}
                                    onClick={() => !service.comingSoon && handleSelect(service)}
                                    disabled={service.comingSoon}
                                    className={`flex flex-col items-start p-4 rounded-xl border transition-all text-left group relative
                                        ${service.comingSoon
                                            ? 'border-slate-800 bg-slate-900/30 opacity-50 cursor-not-allowed'
                                            : 'border-slate-700 bg-slate-800/30 hover:bg-slate-800 hover:border-blue-500/50 cursor-pointer'
                                        }
                                    `}
                                >
                                    {service.comingSoon && (
                                        <span className="absolute top-2 right-2 text-[10px] font-bold uppercase tracking-wider bg-slate-700 text-slate-300 px-2 py-0.5 rounded-full">
                                            Em breve
                                        </span>
                                    )}
                                    <div className={`p-2 rounded-lg bg-slate-900 mb-3 ${service.color}`}><service.icon size={24} /></div>
                                    <div className={`font-semibold transition-colors ${service.comingSoon ? 'text-slate-500' : 'text-slate-200 group-hover:text-blue-400'}`}>{service.name}</div>
                                    <div className="text-xs text-slate-500 mt-1">{service.desc}</div>
                                </button>
                            ))}
                        </div>
                    ) : (
                        <div className="space-y-6">
                            <div className="flex items-center gap-4 p-4 bg-blue-900/10 border border-blue-500/20 rounded-xl">
                                <div className={`p-3 rounded-lg bg-slate-900 ${selectedService.color}`}><selectedService.icon size={32} /></div>
                                <div><h4 className="font-bold text-white text-lg">{selectedService.name}</h4><p className="text-sm text-slate-400">Configurar credenciais e acesso</p></div>
                            </div>

                            {/* Auth Section */}
                            {(selectedService.id === 'google-drive' || selectedService.id === 'dropbox') && !isAuthenticated && (
                                <div className="p-4 border border-slate-700 rounded-xl bg-slate-800/20 text-center">
                                    <p className="text-slate-300 mb-4 text-sm">É necessário autenticar com sua conta para acessar os arquivos.</p>
                                    <button
                                        onClick={handleConnect}
                                        disabled={isAuthenticating}
                                        className="px-4 py-2 bg-white text-slate-900 rounded-lg font-bold hover:bg-slate-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 mx-auto"
                                    >
                                        {isAuthenticating ? 'Conectando...' : `Conectar com ${selectedService.name}`}
                                    </button>
                                </div>
                            )}

                            <div>
                                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Nome de Exibição</label>
                                <input type="text" value={customName} onChange={(e) => setCustomName(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-white focus:border-blue-500 outline-none" />
                            </div>

                            <div className="flex justify-end gap-3 pt-4">
                                <button onClick={() => setStep(1)} className="px-4 py-2 text-slate-400 hover:text-white">Voltar</button>
                                <button
                                    onClick={handleConfirm}
                                    disabled={(selectedService.id === 'google-drive' && !isAuthenticated)}
                                    className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Confirmar Conexão
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
