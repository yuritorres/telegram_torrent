import { useState } from 'react';
import { HardDrive, Laptop, Cloud, Database } from 'lucide-react';
import { useGoogleAuth } from '../../hooks/useGoogleAuth';
import toast from 'react-hot-toast';

export const ProviderSetup = ({ workspaceName, onComplete }) => {
    const [selected, setSelected] = useState({ browser: true, localFs: false, gdrive: false, s3: false });
    const [s3Config, setS3Config] = useState(null);
    const [showS3Form, setShowS3Form] = useState(false);

    // Google Auth
    const { login, isInitialized } = useGoogleAuth();
    const [driveToken, setDriveToken] = useState(null);

    const toggleWrapper = async (id) => {
        if (id === 'gdrive') {
            if (!selected.gdrive) {
                if (!isInitialized) {
                    toast.error("Google Scripts não carregados.");
                    return;
                }
                try {
                    const token = await login();
                    setDriveToken(token);
                    toast.success("Login Google realizado!");
                    setSelected(prev => ({ ...prev, [id]: true }));
                } catch (e) {
                    console.error(e);
                    toast.error("Falha no login Google.");
                }
            } else {
                setSelected(prev => ({ ...prev, [id]: false }));
            }
        } else if (id === 's3') {
            if (!selected.s3) {
                setShowS3Form(true);
            } else {
                setSelected(prev => ({ ...prev, [id]: false }));
                setS3Config(null);
            }
        } else {
            setSelected(prev => ({ ...prev, [id]: !prev[id] }));
        }
    };

    const handleS3Save = (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const config = {
            bucket: formData.get('bucket'),
            region: formData.get('region'),
            accessKeyId: formData.get('accessKeyId'),
            secretAccessKey: formData.get('secretAccessKey')
        };

        if (!config.bucket || !config.region || !config.accessKeyId || !config.secretAccessKey) {
            toast.error("Preencha todos os campos do S3.");
            return;
        }

        setS3Config(config);
        setSelected(prev => ({ ...prev, s3: true }));
        setShowS3Form(false);
        toast.success("Credenciais S3 salvas temporariamente.");
    };

    const handleFinishWithToken = () => {
        const connections = [];
        if (selected.browser) connections.push({ id: `conn-browser-${Date.now()}`, serviceId: 'browser', name: 'Navegador Local', used: '0KB', total: '500MB' });
        if (selected.localFs) connections.push({ id: `conn-local-${Date.now()}`, serviceId: 'local-fs', name: 'Meu Computador', used: 'System', total: 'Disk' });

        if (selected.gdrive && driveToken) {
            connections.push({
                id: `conn-gdrive-${Date.now()}`,
                serviceId: 'gdrive',
                name: 'Google Drive',
                used: '0GB',
                total: '15GB',
                token: driveToken
            });
        }

        if (selected.s3 && s3Config) {
            connections.push({
                id: `conn-s3-${Date.now()}`,
                serviceId: 's3',
                name: `AWS S3 (${s3Config.bucket})`,
                used: 'Cloud',
                total: 'Unlimited',
                config: s3Config
            });
        }

        if (connections.length === 0) {
            toast.error("Selecione pelo menos um local.");
            return;
        }
        onComplete(connections);
    };

    if (showS3Form) {
        return (
            <div className="fixed inset-0 bg-slate-950 flex flex-col items-center justify-center p-6 z-[60] animate-in fade-in zoom-in duration-300">
                <div className="bg-slate-900 border border-slate-800 p-8 rounded-2xl max-w-lg w-full shadow-2xl">
                    <div className="flex items-center gap-4 mb-6 text-orange-400">
                        <Database size={32} />
                        <h2 className="text-2xl font-bold text-white">Configurar AWS S3</h2>
                    </div>

                    <div className="bg-orange-950/30 border border-orange-500/20 p-4 rounded-lg mb-6 text-sm text-orange-200">
                        ⚠️ <strong>Atenção:</strong> Suas chaves de acesso serão salvas no <strong>LocalStorage</strong> deste navegador.
                        Certifique-se de usar um computador seguro e não usar chaves de root (use IAM com permissões restritas).
                    </div>

                    <form onSubmit={handleS3Save} className="space-y-4">
                        <div>
                            <label className="block text-slate-400 text-xs uppercase mb-1">Nome do Bucket</label>
                            <input name="bucket" required className="w-full bg-slate-800 border-slate-700 rounded p-2 text-white focus:ring-orange-500 focus:border-orange-500" placeholder="ex: meus-documentos" />
                        </div>
                        <div>
                            <label className="block text-slate-400 text-xs uppercase mb-1">Região</label>
                            <input name="region" required className="w-full bg-slate-800 border-slate-700 rounded p-2 text-white focus:ring-orange-500 focus:border-orange-500" placeholder="ex: us-east-1" defaultValue="us-east-1" />
                        </div>
                        <div>
                            <label className="block text-slate-400 text-xs uppercase mb-1">Access Key ID</label>
                            <input name="accessKeyId" required className="w-full bg-slate-800 border-slate-700 rounded p-2 text-white focus:ring-orange-500 focus:border-orange-500 font-mono" placeholder="AKIA..." />
                        </div>
                        <div>
                            <label className="block text-slate-400 text-xs uppercase mb-1">Secret Access Key</label>
                            <input name="secretAccessKey" type="password" required className="w-full bg-slate-800 border-slate-700 rounded p-2 text-white focus:ring-orange-500 focus:border-orange-500 font-mono" placeholder="Secret..." />
                        </div>

                        <div className="flex gap-3 mt-8">
                            <button type="button" onClick={() => setShowS3Form(false)} className="flex-1 py-3 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg">
                                Cancelar
                            </button>
                            <button type="submit" className="flex-1 py-3 bg-orange-600 hover:bg-orange-500 text-white font-bold rounded-lg shadow-lg shadow-orange-500/20">
                                Salvar Configuração
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-slate-950 flex flex-col items-center justify-center p-6 z-50 animate-in slide-in-from-right duration-500">
            <div className="max-w-6xl w-full text-center">
                <h1 className="text-4xl font-bold text-white mb-4">Conexões para "{workspaceName}"</h1>
                <p className="text-slate-400 mb-10">Onde deseja guardar ou aceder aos seus ficheiros?</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12 text-left">
                    {/* Browser */}
                    <div onClick={() => toggleWrapper('browser')} className={`cursor-pointer p-6 border rounded-2xl transition-all ${selected.browser ? 'bg-slate-900 border-emerald-500 ring-1 ring-emerald-500/50' : 'bg-slate-900/50 border-slate-800 hover:bg-slate-800'}`}>
                        <HardDrive size={32} className={`mb-4 ${selected.browser ? 'text-emerald-400' : 'text-slate-500'}`} />
                        <h3 className="font-bold text-white text-lg">Navegador</h3>
                        <p className="text-sm text-slate-400 mt-2">Memória temporária. Rápido e privado.</p>
                    </div>

                    {/* Local FS */}
                    <div onClick={() => toggleWrapper('localFs')} className={`cursor-pointer p-6 border rounded-2xl transition-all ${selected.localFs ? 'bg-slate-900 border-blue-500 ring-1 ring-blue-500/50' : 'bg-slate-900/50 border-slate-800 hover:bg-slate-800'}`}>
                        <Laptop size={32} className={`mb-4 ${selected.localFs ? 'text-blue-400' : 'text-slate-500'}`} />
                        <h3 className="font-bold text-white text-lg">Computador</h3>
                        <p className="text-sm text-slate-400 mt-2">Pastas do sistema operativo.</p>
                    </div>

                    {/* Cloud: Google Drive */}
                    <div onClick={() => toggleWrapper('gdrive')} className={`cursor-pointer p-6 border rounded-2xl transition-all ${selected.gdrive ? 'bg-slate-900 border-purple-500 ring-1 ring-purple-500/50' : 'bg-slate-900/50 border-slate-800 hover:bg-slate-800'}`}>
                        <Cloud size={32} className={`mb-4 ${selected.gdrive ? 'text-purple-400' : 'text-slate-500'}`} />
                        <h3 className="font-bold text-white text-lg">Google Drive</h3>
                        <p className="text-sm text-slate-400 mt-2">Acesse seus arquivos do Google.</p>
                    </div>

                    {/* Cloud: AWS S3 */}
                    <div onClick={() => toggleWrapper('s3')} className={`cursor-pointer p-6 border rounded-2xl transition-all ${selected.s3 ? 'bg-slate-900 border-orange-500 ring-1 ring-orange-500/50' : 'bg-slate-900/50 border-slate-800 hover:bg-slate-800'}`}>
                        <Database size={32} className={`mb-4 ${selected.s3 ? 'text-orange-400' : 'text-slate-500'}`} />
                        <h3 className="font-bold text-white text-lg">AWS S3</h3>
                        <p className="text-sm text-slate-400 mt-2">Storage de objetos compatível com S3.</p>
                    </div>
                </div>
                <button onClick={handleFinishWithToken} className="px-10 py-4 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/25 transition-all hover:scale-105">Iniciar Sistema</button>
            </div>
        </div>
    );
};
