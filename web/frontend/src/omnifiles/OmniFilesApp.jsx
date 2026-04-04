import { useState, useMemo, useEffect } from 'react';
import { FileSystemProvider, useFileSystem } from './context/FileSystemContext';
import { useSelection } from './hooks/useSelection';
import { useDragDrop } from './hooks/useDragDrop';
import { useTags } from './hooks/useTags';

import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { FileGrid } from './components/core/FileGrid';
import { FilePreviewModal } from './components/core/FilePreviewModal';
import { ContextMenu } from './components/core/ContextMenu';
import { TagManager } from './components/core/TagManager';
import { WorkspaceSetup } from './components/settings/WorkspaceSetup';
import { ProviderSetup } from './components/settings/ProviderSetup';
import { SettingsScreen } from './components/settings/SettingsScreen';
import { WelcomeScreen } from './components/settings/WelcomeScreen';
import { MoveCopyModal } from './components/modals/MoveCopyModal';
import { DetailsPanel } from './components/layout/DetailsPanel';

import { useModal } from './context/ModalContext';
import { ClipboardProvider, useClipboard } from './context/ClipboardContext';
import { useToast } from './hooks/useToast';

const AppLayout = () => {
    const {
        appState, setAppState,
        workspaces, activeWorkspace, activeWorkspaceObj,
        files, currentPath, historyIndex, history,
        previewFile, setPreviewFile,
        currentFolderId,
        navigate, navigateBreadcrumb, navigateBack, navigateForward, navigateToPath, navigateUp,
        switchWorkspace, createWorkspace, updateWorkspaceData, resetSystem,
        createFolder, deleteFiles, renameFile, addFiles, importDroppedFiles, downloadFile,
        openLocalFolder,
        pasteFiles,
        isProcessing,
        toggleStar,
        moveFiles, copyFiles,
        restoreFiles, permanentDeleteFiles, emptyTrash, downloadFiles,
        loadSystem
    } = useFileSystem();

    // Debug logging
    console.log('[OmniFilesApp] files:', files, 'type:', typeof files, 'isArray:', Array.isArray(files));

    const { selectedFileIds, setSelectedFileIds, toggleSelection, clearSelection, selectRange, lastSelectedId } = useSelection();
    const { isDragging, handleDragOver, handleDragLeave, handleDrop } = useDragDrop(importDroppedFiles);
    const { clipboard, copy, cut, paste } = useClipboard();
    const toaster = useToast();

    const { openInput, openConfirm } = useModal();
    const [viewMode, setViewMode] = useState('grid');
    const [sortConfig, setSortConfig] = useState({ key: 'name', direction: 'asc' });
    const [searchQuery, setSearchQuery] = useState('');
    const [showSettings, setShowSettings] = useState(false);
    const [contextMenu, setContextMenu] = useState(null);
    const [setupWorkspaceName, setSetupWorkspaceName] = useState('');
    const [moveCopyModal, setMoveCopyModal] = useState({ isOpen: false, items: [] });

    const [folderPrefs, setFolderPrefs] = useState(() => {
        try { return JSON.parse(localStorage.getItem('omni_folder_prefs')) || {}; }
        catch { return {}; }
    });

    useEffect(() => {
        localStorage.setItem('omni_folder_prefs', JSON.stringify(folderPrefs));
    }, [folderPrefs]);

    useEffect(() => {
        const key = currentFolderId || 'root';
        const prefs = folderPrefs[key];
        if (prefs) {
            if (prefs.viewMode) setViewMode(prefs.viewMode);
            if (prefs.sortConfig) setSortConfig(prefs.sortConfig);
        }
    }, [currentFolderId]);

    const handleSetViewMode = (mode) => {
        setViewMode(mode);
        const key = currentFolderId || 'root';
        setFolderPrefs(prev => ({
            ...prev,
            [key]: { ...prev[key], viewMode: mode }
        }));
    };

    const handleRequestSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        const newSort = { key, direction };
        setSortConfig(newSort);
        const wsKey = currentFolderId || 'root';
        setFolderPrefs(prev => ({
            ...prev,
            [wsKey]: { ...prev[wsKey], sortConfig: newSort }
        }));
    };

    const [activeTagId, setActiveTagId] = useState(null);
    const { tags, addTag, updateTag, deleteTag, toggleFileTag } = useTags();

    const [isSidebarOpen, setIsSidebarOpen] = useState(() => {
        const saved = localStorage.getItem('omni_ui_sidebar');
        if (saved !== null) return JSON.parse(saved);
        return window.innerWidth >= 768;
    });

    const [showDetails, setShowDetails] = useState(() => {
        const saved = localStorage.getItem('omni_ui_details');
        if (saved !== null) return JSON.parse(saved);
        return false;
    });

    const [showTagManager, setShowTagManager] = useState(false);

    const toggleSidebar = () => {
        const newState = !isSidebarOpen;
        setIsSidebarOpen(newState);
        localStorage.setItem('omni_ui_sidebar', JSON.stringify(newState));
    };

    const toggleDetails = () => {
        const newState = !showDetails;
        setShowDetails(newState);
        localStorage.setItem('omni_ui_details', JSON.stringify(newState));
    };

    const handleFileSelect = (fileId, options = {}) => {
        const { ctrlKey, metaKey, shiftKey } = options;
        const isMulti = ctrlKey || metaKey;

        if (shiftKey && lastSelectedId) {
            const lastIndex = displayedFiles.findIndex(f => f.id === lastSelectedId);
            const currentIndex = displayedFiles.findIndex(f => f.id === fileId);

            if (lastIndex !== -1 && currentIndex !== -1) {
                const start = Math.min(lastIndex, currentIndex);
                const end = Math.max(lastIndex, currentIndex);
                const rangeIds = displayedFiles.slice(start, end + 1).map(f => f.id);

                if (isMulti) {
                    const newSelection = [...new Set([...selectedFileIds, ...rangeIds])];
                    selectRange(newSelection);
                } else {
                    selectRange(rangeIds);
                }
                return;
            }
        }

        toggleSelection(fileId, isMulti);
    };

    const displayedFiles = useMemo(() => {
        // Safety check
        const safeFiles = Array.isArray(files) ? files : [];
        let filtered = [];

        if (searchQuery.trim() !== '') {
            filtered = safeFiles.filter(f => f.name.toLowerCase().includes(searchQuery.toLowerCase()));
        } else if (['favorites', 'recent', 'trash'].includes(currentFolderId) || (currentFolderId && currentFolderId.startsWith('tag-'))) {
            filtered = safeFiles;
        } else if (currentFolderId === null && activeWorkspaceObj && activeWorkspaceObj.connections && activeWorkspaceObj.connections.length > 0) {
            filtered = activeWorkspaceObj.connections.map(conn => ({
                id: conn.id,
                name: conn.name,
                type: 'folder',
                isConnection: true,
                size: conn.total || '--',
                date: '--',
                tags: [],
                isStarred: false,
                workspaceId: activeWorkspace,
                parentId: null
            }));
        } else {
            filtered = safeFiles;
        }

        return filtered.sort((a, b) => {
            if (a.type === 'folder' && b.type !== 'folder') return -1;
            if (a.type !== 'folder' && b.type === 'folder') return 1;

            let valA = a[sortConfig.key] || '';
            let valB = b[sortConfig.key] || '';

            if (sortConfig.key === 'size') {
                valA = a.sizeRaw || 0;
                valB = b.sizeRaw || 0;
            }

            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();

            if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
            if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
            return 0;
        });
    }, [files, currentFolderId, searchQuery, sortConfig, activeWorkspace, activeWorkspaceObj, selectedFileIds]);

    useEffect(() => {
        const handleKeyDown = (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
                e.preventDefault();
                setIsSidebarOpen(prev => {
                    const newState = !prev;
                    localStorage.setItem('omni_ui_sidebar', JSON.stringify(newState));
                    return newState;
                });
            }

            if (e.ctrlKey || e.metaKey) {
                if (e.key.toLowerCase() === 'c' && selectedFileIds.length > 0) {
                    e.preventDefault();
                    const items = files.filter(f => selectedFileIds.includes(f.id));
                    copy(items);
                }
                if (e.key.toLowerCase() === 'x' && selectedFileIds.length > 0) {
                    e.preventDefault();
                    const items = files.filter(f => selectedFileIds.includes(f.id));
                    cut(items);
                }
                if (e.key.toLowerCase() === 'v') {
                    e.preventDefault();
                    paste();
                }
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [selectedFileIds, files, copy, cut, paste]);

    if (appState === 'welcome') {
        return (
            <WelcomeScreen 
                onQuickStart={async () => {
                    // Quick start: create default workspace and go to ready state
                    await createWorkspace('Meu Workspace');
                    setAppState('ready');
                }}
                onStart={() => setAppState('setup')} 
            />
        );
    }

    if (appState === 'setup') {
        return (
            <WorkspaceSetup
                onComplete={(wsName) => {
                    setSetupWorkspaceName(wsName);
                    setAppState('provider-setup');
                }}
            />
        );
    }

    if (appState === 'provider-setup') {
        return (
            <ProviderSetup
                workspaceName={setupWorkspaceName}
                onComplete={() => setAppState('ready')}
            />
        );
    }

    const selectedFiles = Array.isArray(files) ? files.filter(f => selectedFileIds.includes(f.id)) : [];

    return (
        <div className="h-full flex flex-col bg-background text-foreground">
            {showSettings && (
                <SettingsScreen
                    onClose={() => setShowSettings(false)}
                    workspaces={workspaces}
                    activeWorkspace={activeWorkspace}
                    onSwitchWorkspace={switchWorkspace}
                    onCreateWorkspace={createWorkspace}
                    onUpdateWorkspace={updateWorkspaceData}
                    onResetSystem={resetSystem}
                />
            )}

            {showTagManager && (
                <TagManager
                    tags={tags}
                    onAddTag={addTag}
                    onUpdateTag={updateTag}
                    onDeleteTag={deleteTag}
                    onClose={() => setShowTagManager(false)}
                />
            )}

            <div className="flex-1 flex overflow-hidden">
                {isSidebarOpen && (
                    <Sidebar
                        workspaces={workspaces}
                        activeWorkspaceObj={activeWorkspaceObj}
                        activeWorkspaceId={activeWorkspace}
                        onSwitchWorkspace={switchWorkspace}
                        onCreateWorkspace={createWorkspace}
                        onShowSettings={setShowSettings}
                        currentPath={currentPath}
                        onNavigateDrive={navigate}
                        isOpen={isSidebarOpen}
                        onGoHome={() => navigateToPath(null)}
                        onGoRecent={() => navigateToPath('recent')}
                        onGoFavorites={() => navigateToPath('favorites')}
                        onOpenLocal={openLocalFolder}
                        tags={tags}
                        activeTagId={activeTagId}
                        onNavigateTag={(tagId) => navigateToPath(`tag-${tagId}`)}
                        onGoTrash={() => navigateToPath('trash')}
                    />
                )}

                <div className="flex-1 flex flex-col overflow-hidden">
                    <Header
                        viewMode={viewMode}
                        setViewMode={handleSetViewMode}
                        searchQuery={searchQuery}
                        setSearchQuery={setSearchQuery}
                        selectedCount={selectedFileIds.length}
                        onClearSelection={clearSelection}
                        onUpload={(files) => addFiles(files, currentFolderId)}
                        onCreateFolder={() => {
                            openInput({
                                title: 'Nova Pasta',
                                placeholder: 'Nome da pasta',
                                onConfirm: (name) => createFolder(name, currentFolderId)
                            });
                        }}
                        onDelete={() => deleteFiles(selectedFileIds)}
                        onOpenTagManager={() => setShowTagManager(true)}
                        onToggleSidebar={toggleSidebar}
                        isSidebarOpen={isSidebarOpen}
                        onToggleDetails={toggleDetails}
                        showDetails={showDetails}
                        isProcessing={isProcessing}
                        currentPath={currentPath}
                        onNavigateBreadcrumb={navigateBreadcrumb}
                        onBack={navigateBack}
                        onForward={navigateForward}
                        historyIndex={historyIndex}
                        historyLength={history.length}
                        onRefresh={loadSystem}
                    />

                    <div
                        className="flex-1 overflow-auto"
                        onDrop={handleDrop}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onContextMenu={(e) => {
                            e.preventDefault();
                            setContextMenu({ x: e.clientX, y: e.clientY, file: null });
                        }}
                    >
                        <FileGrid
                            files={displayedFiles}
                            viewMode={viewMode}
                            sortConfig={sortConfig}
                            requestSort={handleRequestSort}
                            selectedFileIds={selectedFileIds}
                            onSelect={handleFileSelect}
                            onSelectRange={(ids) => setSelectedFileIds(ids)}
                            onNavigate={(file) => {
                                if (file.type === 'folder' || file.isConnection) {
                                    navigate(file);
                                    clearSelection();
                                } else {
                                    setPreviewFile(file);
                                }
                            }}
                            onContextMenu={(e, file) => {
                                e.preventDefault();
                                setContextMenu({ x: e.clientX, y: e.clientY, file });
                            }}
                            tags={tags}
                            onCreateFolder={() => {
                                openInput({
                                    title: 'Nova Pasta',
                                    placeholder: 'Nome da pasta',
                                    onConfirm: (name) => createFolder(name, currentFolderId)
                                });
                            }}
                            onUpload={(fileList) => {
                                const filesArray = Array.from(fileList);
                                addFiles(filesArray, currentFolderId);
                            }}
                            onRefresh={loadSystem}
                            isTrash={currentFolderId === 'trash'}
                        />
                    </div>
                </div>

                {showDetails && selectedFiles.length > 0 && (
                    <DetailsPanel
                        files={selectedFiles}
                        tags={tags}
                        onToggleTag={(fileId, tagId) => toggleFileTag(fileId, tagId)}
                    />
                )}
            </div>

            {previewFile && (
                <FilePreviewModal
                    file={previewFile}
                    onClose={() => setPreviewFile(null)}
                />
            )}

            {contextMenu && (
                <ContextMenu
                    x={contextMenu.x}
                    y={contextMenu.y}
                    file={contextMenu.file}
                    selectedFiles={selectedFiles}
                    onClose={() => setContextMenu(null)}
                    onRename={(file) => {
                        openInput({
                            title: 'Renomear',
                            placeholder: 'Novo nome',
                            defaultValue: file.name,
                            onConfirm: (newName) => renameFile(file.id, newName)
                        });
                    }}
                    onDelete={(files) => deleteFiles(files.map(f => f.id))}
                    onDownload={(file) => downloadFile(file.id)}
                    onToggleStar={(file) => toggleStar(file.id)}
                    onCopy={(files) => copy(files)}
                    onCut={(files) => cut(files)}
                    onPaste={() => paste()}
                    onMove={(files) => setMoveCopyModal({ isOpen: true, items: files, mode: 'move' })}
                    onCopyTo={(files) => setMoveCopyModal({ isOpen: true, items: files, mode: 'copy' })}
                />
            )}

            {moveCopyModal.isOpen && (
                <MoveCopyModal
                    items={moveCopyModal.items}
                    mode={moveCopyModal.mode}
                    onClose={() => setMoveCopyModal({ isOpen: false, items: [] })}
                    onConfirm={(targetId) => {
                        if (moveCopyModal.mode === 'move') {
                            moveFiles(moveCopyModal.items.map(i => i.id), targetId);
                        } else {
                            copyFiles(moveCopyModal.items.map(i => i.id), targetId);
                        }
                        setMoveCopyModal({ isOpen: false, items: [] });
                    }}
                />
            )}

            {isDragging && (
                <div className="fixed inset-0 bg-blue-500/20 border-4 border-dashed border-blue-500 flex items-center justify-center z-50 pointer-events-none">
                    <div className="bg-background p-8 rounded-lg shadow-xl">
                        <p className="text-xl font-semibold">Solte os arquivos aqui</p>
                    </div>
                </div>
            )}
        </div>
    );
};

const OmniFilesApp = () => {
    return (
        <FileSystemProvider>
            <ClipboardProvider>
                <AppLayout />
            </ClipboardProvider>
        </FileSystemProvider>
    );
};

export default OmniFilesApp;
