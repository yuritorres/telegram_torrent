import React from 'react';
import { Settings, Plus, Home, Clock, FolderOpen, Star, Tag, Trash2, Github, ExternalLink } from 'lucide-react';
import { SERVICE_CATALOG } from '../../constants/services';
import { useTranslation } from 'react-i18next';
import PropTypes from 'prop-types';

export const Sidebar = ({
    workspaces,
    activeWorkspaceObj,
    activeWorkspaceId,
    onSwitchWorkspace,
    onCreateWorkspace,
    onShowSettings,
    currentPath,
    onNavigateDrive,
    isOpen,
    onGoHome,
    onGoRecent,
    onGoFavorites,
    onOpenLocal,
    tags,
    activeTagId,
    onNavigateTag,
    onGoTrash
}) => {
    const { t } = useTranslation();
    const activeConnections = activeWorkspaceObj?.connections || [];
    const currentFolderId = currentPath.length > 0 ? currentPath[currentPath.length - 1].id : null;

    return (
        <aside className={`${isOpen ? 'w-[260px] border-r' : 'w-0 border-none'} flex flex-col border-slate-800 bg-slate-900/50 backdrop-blur-sm relative transition-all duration-300 ease-in-out flex-shrink-0 overflow-hidden`}>
            <div className="w-[260px] flex flex-col h-full">
                <div className="p-4 border-b border-slate-800">
                    <label className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2 block">{t('sidebar.workspace')}</label>
                    <div className="relative group">
                        <button aria-label={t('sidebar.workspaceSettings')} className="w-full flex items-center justify-between bg-slate-800 hover:bg-slate-700 p-2 rounded-lg border border-slate-700 transition-all">
                            <div className="flex items-center gap-2">
                                <div className={`w-6 h-6 rounded ${activeWorkspaceObj?.color || 'bg-blue-600'} flex items-center justify-center text-xs font-bold uppercase text-white`}>
                                    {activeWorkspaceObj?.name?.[0]}
                                </div>
                                <span className="text-sm font-medium truncate w-32 text-left">{activeWorkspaceObj?.name}</span>
                            </div>
                            <Settings size={14} className="text-slate-400 hover:text-white cursor-pointer" onClick={(e) => { e.stopPropagation(); onShowSettings(true); }} aria-label={t('sidebar.settings')} />
                        </button>
                        <div className="hidden group-hover:block absolute top-full left-0 w-full mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-20 overflow-hidden">
                            {workspaces.map(ws => (
                                <div key={ws.id} onClick={() => onSwitchWorkspace(ws.id)} role="button" tabIndex={0} aria-label={`Switch to ${ws.name}`} className={`p-2 text-sm hover:bg-slate-700 cursor-pointer flex items-center gap-2 ${activeWorkspaceId === ws.id ? 'text-white bg-slate-700' : 'text-slate-400'}`}>
                                    <div className={`w-2 h-2 rounded-full ${ws.color || 'bg-slate-500'}`}></div>
                                    {ws.name}
                                </div>
                            ))}
                            <div onClick={onCreateWorkspace} role="button" tabIndex={0} aria-label={t('sidebar.newWorkspace')} className="border-t border-slate-700 p-2 text-xs text-blue-400 hover:bg-slate-700 cursor-pointer flex items-center gap-2">
                                <Plus size={12} /> {t('sidebar.newWorkspace')}
                            </div>
                            <div onClick={onOpenLocal} role="button" tabIndex={0} aria-label={t('sidebar.openLocalFolder')} className="border-t border-slate-700 p-2 text-xs text-green-400 hover:bg-slate-700 cursor-pointer flex items-center gap-2">
                                <FolderOpen size={12} /> {t('sidebar.openLocalFolder')}
                            </div>
                        </div>
                    </div>
                </div>
                <div className="flex-1 overflow-y-auto py-4 scrollbar-hide px-3">
                    <div className="mb-6">
                        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-2 mb-2">{t('sidebar.navigation', 'NAVEGAÇÃO')}</h3>
                        <nav className="space-y-0.5" aria-label="Main Navigation">
                            <div onClick={onGoHome} role="button" tabIndex={0} aria-label={t('sidebar.home')} className={`flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors ${!currentFolderId ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`}>
                                <Home size={18} /><span className="text-sm">{t('sidebar.home')}</span>
                            </div>
                            <div onClick={onGoRecent} role="button" tabIndex={0} aria-label={t('sidebar.recent')} className={`flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors ${currentFolderId === 'recent' ? 'bg-slate-800 text-blue-400' : 'text-slate-400 hover:bg-slate-800 hover:text-blue-400'}`}>
                                <Clock size={18} /><span className="text-sm">{t('sidebar.recent')}</span>
                            </div>
                            <div onClick={onGoFavorites} role="button" tabIndex={0} aria-label={t('sidebar.favorites')} className={`flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors ${currentFolderId === 'favorites' ? 'bg-slate-800 text-yellow-400' : 'text-slate-400 hover:bg-slate-800 hover:text-yellow-400'}`}>
                                <Star size={18} /><span className="text-sm">{t('sidebar.favorites')}</span>
                            </div>
                            <div onClick={onGoTrash} role="button" tabIndex={0} aria-label={t('sidebar.trash', 'Lixeira')} className={`flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors ${currentFolderId === 'trash' ? 'bg-slate-800 text-red-400' : 'text-slate-400 hover:bg-slate-800 hover:text-red-400'}`}>
                                <Trash2 size={18} /><span className="text-sm">{t('sidebar.trash', 'Lixeira')}</span>
                            </div>
                        </nav>
                    </div>
                    <div>
                        <div className="flex items-center justify-between px-2 mb-2 group">
                            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{t('sidebar.connections')}</h3>
                            <Settings size={14} className="text-slate-500 hover:text-blue-400 cursor-pointer" onClick={() => onShowSettings(true)} />
                        </div>
                        <div className="space-y-2">
                            {activeConnections.length === 0 && <div className="text-xs text-slate-500 px-2 italic">{t('sidebar.noConnections')}</div>}
                            {activeConnections.map(conn => {
                                const isActive = currentPath.length > 0 && currentPath[0].id === conn.id;
                                const serviceInfo = SERVICE_CATALOG.find(s => s.id === conn.serviceId) || SERVICE_CATALOG[0];
                                return (
                                    <div key={conn.id} onClick={() => onNavigateDrive(conn)} className={`group p-2 rounded-lg cursor-pointer border transition-all ${isActive ? 'bg-slate-800 border-slate-700' : 'border-transparent hover:bg-slate-800/50 hover:border-slate-700/50'}`}>
                                        <div className="flex items-center gap-2 mb-1">
                                            <serviceInfo.icon size={16} className={serviceInfo.color} />
                                            <span className={`text-sm font-medium truncate ${isActive ? 'text-white' : 'text-slate-300'}`}>{conn.name}</span>
                                        </div>
                                        {conn.used && <div className="w-full bg-slate-900 h-1 rounded-full mt-1 overflow-hidden"><div className={`h-full ${serviceInfo.color.replace('text-', 'bg-')} w-1/3 rounded-full`} /></div>}
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* Tags Section */}
                    <div className="mt-6">
                        <div className="flex items-center justify-between px-2 mb-2 group">
                            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{t('sidebar.tags')}</h3>
                        </div>
                        <div className="space-y-1">
                            {tags.length === 0 && <div className="text-xs text-slate-500 px-2 italic">Nenhuma tag</div>}
                            {tags.map(tag => (
                                <div
                                    key={tag.id}
                                    onClick={() => onNavigateTag(tag.id)}
                                    className={`flex items-center gap-2 group p-2 rounded-lg cursor-pointer border transition-all ${activeTagId === tag.id ? 'bg-slate-800 border-slate-700' : 'border-transparent hover:bg-slate-800/50 hover:border-slate-700/50'}`}
                                >
                                    <div className={`w-3 h-3 rounded-full ${tag.color}`}></div>
                                    <span className={`text-sm font-medium truncate ${activeTagId === tag.id ? 'text-white' : 'text-slate-300'}`}>{tag.name}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Footer Links */}
                <div className="p-3 border-t border-slate-800 space-y-1.5">
                    <a
                        href="https://crom.run/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition-colors group"
                    >
                        <ExternalLink size={15} className="text-blue-400 group-hover:text-blue-300" />
                        <span>Crom.Run</span>
                    </a>
                    <a
                        href="https://github.com/MrJc01/crom-omnifiles"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition-colors group"
                    >
                        <Github size={15} className="text-slate-400 group-hover:text-white" />
                        <span>GitHub</span>
                    </a>
                </div>
            </div>
        </aside>
    );
};

Sidebar.propTypes = {
    workspaces: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        color: PropTypes.string,
        connections: PropTypes.array
    })).isRequired,
    activeWorkspaceObj: PropTypes.object,
    activeWorkspaceId: PropTypes.string,
    onSwitchWorkspace: PropTypes.func.isRequired,
    onCreateWorkspace: PropTypes.func.isRequired,
    onShowSettings: PropTypes.func.isRequired,
    currentPath: PropTypes.array.isRequired,
    onNavigateDrive: PropTypes.func.isRequired,
    isOpen: PropTypes.bool.isRequired,
    onGoHome: PropTypes.func.isRequired,
    onGoRecent: PropTypes.func.isRequired,
    onGoFavorites: PropTypes.func.isRequired,
    onOpenLocal: PropTypes.func,
    tags: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        color: PropTypes.string
    })),
    activeTagId: PropTypes.string,
    onNavigateTag: PropTypes.func,
    onGoTrash: PropTypes.func
};
