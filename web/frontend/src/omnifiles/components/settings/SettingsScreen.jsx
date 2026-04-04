import { useState } from 'react';
import { Settings, Briefcase, Plug, Monitor, X, Trash2, PlusCircle, LogOut, Tag } from 'lucide-react';
import { SERVICE_CATALOG } from '../../constants/services';
import { AddServiceModal } from './AddServiceModal';
import { ConfirmModal } from '../core/ConfirmModal';
import { TagManager } from './TagManager';
import { useToast } from '../../hooks/useToast';

const WorkspaceConfigPanel = ({ workspace, onSave, onDelete }) => {
    const [name, setName] = useState(workspace.name);

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
            <h2 className="text-2xl font-bold text-white flex items-center gap-2"><Briefcase className="text-orange-400" /> Workspace: {workspace.name}</h2>
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <label className="block text-sm font-medium text-slate-400 mb-2">Nome</label>
                <div className="flex gap-4">
                    <input
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white outline-none"
                    />
                    <button onClick={() => onSave(name)} className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium">Salvar</button>
                </div>
            </div>
            <div className="bg-red-900/10 rounded-xl p-6 border border-red-900/30">
                <h3 className="text-red-400 font-bold mb-2">Zona de Perigo</h3>
                <button onClick={onDelete} className="text-red-400 hover:text-red-300 text-sm font-medium border border-red-900/50 hover:bg-red-900/20 px-4 py-2 rounded-lg transition-colors">Excluir Workspace</button>
            </div>
        </div>
    );
};

export const SettingsScreen = ({ onClose, data, onUpdateData, onResetSystem, activeWorkspaceId, tagActions }) => {
    const [activeTab, setActiveTab] = useState('workspace-config');
    const [isAddingService, setIsAddingService] = useState(false);
    const [confirmModal, setConfirmModal] = useState({ isOpen: false, title: '', message: '', onConfirm: () => { }, isDanger: false });
    const currentWs = data.workspaces.find(w => w.id === activeWorkspaceId) || data.workspaces[0];
    const toast = useToast();

    // Removed useEffect for editingWsName sync - handled by key in WorkspaceConfigPanel

    const handleSaveWsName = (newName) => {
        onUpdateData({ workspaces: data.workspaces.map(w => w.id === currentWs.id ? { ...w, name: newName } : w) });
        toast.success('Nome atualizado!');
    };

    const handleAddConnection = async (service, customName, authData) => {
        if (!currentWs) {
            toast.error("Erro: Workspace não encontrado.");
            return;
        }
        try {
            console.log("Adicionando conexão:", service.name, customName);
            const newConnection = {
                id: `conn-${Date.now()}`,
                serviceId: service.id,
                name: customName,
                used: '0KB',
                total: 'Unlimited',
                ...authData
            };
            const updatedWorkspaces = data.workspaces.map(w => w.id === currentWs.id ? { ...w, connections: [...(w.connections || []), newConnection] } : w);

            await onUpdateData({ workspaces: updatedWorkspaces });
            toast.success("Conexão adicionada com sucesso!");
        } catch (error) {
            console.error("Erro ao adicionar conexão:", error);
            toast.error("Falha ao salvar conexão.");
        }
    };
    const handleRemoveConnection = (connId) => {
        setConfirmModal({
            isOpen: true,
            title: 'Remover Conexão',
            message: 'Tem a certeza que deseja remover esta conexão?',
            confirmText: 'Remover',
            isDanger: true,
            onConfirm: async () => {
                try {
                    const updatedWorkspaces = data.workspaces.map(w => w.id === currentWs.id ? { ...w, connections: w.connections.filter(c => c.id !== connId) } : w);
                    await onUpdateData({ workspaces: updatedWorkspaces });
                    toast.success("Conexão removida.");
                } catch (error) {
                    console.error("Erro ao remover conexão:", error);
                    toast.error("Falha ao remover conexão.");
                }
            }
        });
    };
    const handleDeleteWorkspace = () => {
        if (data.workspaces.length <= 1) return toast.error("Mínimo de 1 workspace.");
        setConfirmModal({
            isOpen: true,
            title: 'Excluir Workspace',
            message: 'Tem a certeza? Esta ação não pode ser desfeita.',
            confirmText: 'Excluir',
            isDanger: true,
            onConfirm: () => {
                onUpdateData({ workspaces: data.workspaces.filter(w => w.id !== currentWs.id) });
                onClose();
            }
        });
    };

    const handleResetSystemClick = () => {
        setConfirmModal({
            isOpen: true,
            title: 'Reset de Fábrica',
            message: 'Isto irá APAGAR TODOS os dados locais. Tem a certeza absoluta?',
            confirmText: 'Sim, Apagar Tudo',
            isDanger: true,
            onConfirm: onResetSystem
        });
    };

    return (
        <div className="fixed inset-0 bg-slate-950 z-50 flex animate-in fade-in duration-200">
            {isAddingService && <AddServiceModal onClose={() => setIsAddingService(false)} onAdd={handleAddConnection} />}
            <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
                <div className="p-6"><h1 className="text-xl font-bold text-white flex items-center gap-2"><Settings className="text-blue-500" /> Definições</h1></div>
                <nav className="flex-1 px-4 space-y-1">
                    <div className="px-4 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider mt-4 mb-1">Workspace Atual</div>
                    <button onClick={() => setActiveTab('workspace-config')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'workspace-config' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}><Briefcase size={18} /> Geral</button>
                    <button onClick={() => setActiveTab('connections')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'connections' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}><Plug size={18} /> Conexões</button>
                    <button onClick={() => setActiveTab('tags')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'tags' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}><Tag size={18} /> Tags</button>
                    <div className="px-4 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider mt-6 mb-1">Global</div>
                    <button onClick={() => setActiveTab('system')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'system' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}><Monitor size={18} /> Sistema</button>
                </nav>
            </div>
            <div className="flex-1 bg-slate-950 flex flex-col relative">
                <button onClick={onClose} className="absolute top-6 right-6 p-2 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white rounded-full border border-slate-800 z-10"><X size={20} /></button>
                <div className="flex-1 overflow-y-auto p-12 max-w-4xl mx-auto w-full">
                    {activeTab === 'workspace-config' && (
                        <WorkspaceConfigPanel
                            key={currentWs.id}
                            workspace={currentWs}
                            onSave={handleSaveWsName}
                            onDelete={handleDeleteWorkspace}
                        />
                    )}
                    {activeTab === 'connections' && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <div className="flex justify-between items-center"><h2 className="text-2xl font-bold text-white flex items-center gap-2"><Plug className="text-emerald-400" /> Serviços Conectados</h2><button onClick={() => setIsAddingService(true)} className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2"><PlusCircle size={18} /> Adicionar</button></div>
                            <div className="grid gap-4">
                                {(!currentWs.connections || currentWs.connections.length === 0) && <div className="p-8 text-center border-2 border-dashed border-slate-800 rounded-xl text-slate-500">Nenhum serviço conectado.</div>}
                                {currentWs.connections?.map(conn => {
                                    const serviceInfo = SERVICE_CATALOG.find(s => s.id === conn.serviceId) || SERVICE_CATALOG[0];
                                    return (
                                        <div key={conn.id} className="bg-slate-800/40 border border-slate-700 p-4 rounded-xl flex items-center justify-between">
                                            <div className="flex items-center gap-4"><div className={`p-3 rounded-lg bg-slate-900 ${serviceInfo.color}`}><serviceInfo.icon size={24} /></div><div><h3 className="font-bold text-slate-200">{conn.name}</h3><p className="text-xs text-slate-500">{serviceInfo.name}</p></div></div>
                                            <button onClick={() => handleRemoveConnection(conn.id)} className="p-2 text-slate-500 hover:text-red-400"><LogOut size={18} /></button>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                    {activeTab === 'system' && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <h2 className="text-2xl font-bold text-white flex items-center gap-2"><Monitor className="text-blue-400" /> Sistema Global</h2>
                            <div className="bg-red-900/10 rounded-xl p-6 border border-red-900/30">
                                <h3 className="text-red-200 font-medium mb-2">Reset de Fábrica</h3>
                                <p className="text-sm text-red-300/70 mb-4">Isto irá apagar todos os dados guardados localmente e reiniciar a aplicação para o ecrã de boas-vindas.</p>
                                <button onClick={handleResetSystemClick} className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"><Trash2 size={16} /> Limpar Tudo e Reiniciar</button>
                            </div>

                            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                                <h3 className="text-slate-200 font-bold mb-4">Idioma / Language</h3>
                                <div className="flex gap-4">
                                    <button
                                        onClick={() => { import('../../i18n').then(i18n => i18n.default.changeLanguage('pt')); toast.success('Idioma alterado para Português'); }}
                                        className="px-4 py-2 bg-slate-700 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors"
                                    >
                                        Português
                                    </button>
                                    <button
                                        onClick={() => { import('../../i18n').then(i18n => i18n.default.changeLanguage('en')); toast.success('Language changed to English'); }}
                                        className="px-4 py-2 bg-slate-700 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors"
                                    >
                                        English
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                    {activeTab === 'tags' && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <TagManager
                                tags={data.tags}
                                onAddTag={tagActions.addTag}
                                onUpdateTag={tagActions.updateTag}
                                onDeleteTag={tagActions.deleteTag}
                            />
                        </div>
                    )}
                </div>
            </div>

            <ConfirmModal
                isOpen={confirmModal.isOpen}
                title={confirmModal.title}
                message={confirmModal.message}
                confirmText={confirmModal.confirmText}
                isDanger={confirmModal.isDanger}
                onClose={() => setConfirmModal({ ...confirmModal, isOpen: false })}
                onConfirm={confirmModal.onConfirm}
            />
        </div >
    );
};
