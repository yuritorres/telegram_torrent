import { useRef, useState, useEffect, useCallback, useMemo } from 'react';
import { db } from '../db';
import { useToast } from './useToast';
import { getProvider } from '../providers/ProviderFactory';
import { GoogleDriveProvider } from '../providers/GoogleDriveProvider';
import { useFileProcessor } from './useFileProcessor';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';

export function useFileSystemInternal() {
    const [appState, setAppState] = useState('loading'); // 'loading', 'welcome', 'setup-workspace', 'setup-providers', 'explorer', 'error'
    const [workspaces, setWorkspaces] = useState([]);
    const [files, setFiles] = useState([]);
    const [activeWorkspace, setActiveWorkspace] = useState('');
    const [currentPath, setCurrentPath] = useState([]);
    const [history, setHistory] = useState([]);
    const [historyIndex, setHistoryIndex] = useState(-1);
    const [previewFile, setPreviewFile] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);

    // Ensure files is always an array
    const safeFiles = useMemo(() => Array.isArray(files) ? files : [], [files]);

    const toast = useToast();

    const activeWorkspaceObj = useMemo(() =>
        workspaces.find(w => w.id === activeWorkspace) || workspaces[0],
        [workspaces, activeWorkspace]);

    const provider = useMemo(() => {
        // 1. Check if we are inside a Connection (Drive/S3) based on Path Root
        console.log("[FileSystem] Computing provider. CurrentPath:", currentPath);
        if (currentPath.length > 0 && activeWorkspaceObj?.connections) {
            const rootId = currentPath[0].id;
            const activeConnection = activeWorkspaceObj.connections.find(c => c.id === rootId);
            console.log("[FileSystem] RootID:", rootId, "Connection:", activeConnection);

            if (activeConnection) {
                console.log(`[FileSystem] Switching to Provider: ${activeConnection.name} (${activeConnection.serviceId})`);
                if (activeConnection.serviceId === 'google-drive') {
                    // Pass activeWorkspace ID so files are filtered correctly in App.jsx
                    return new GoogleDriveProvider(activeWorkspace, activeConnection.token, activeConnection.id);
                }
                // Add other providers here
            }
        }
        // 2. Fallback to Workspace Default Provider
        console.log("[FileSystem] Using Default Provider (IndexedDB)");
        return getProvider(activeWorkspaceObj);
    }, [activeWorkspaceObj, currentPath, activeWorkspace]);

    const { calculateHash, generateThumbnail } = useFileProcessor();

    // Initial Load - Carregamento Assíncrono do IndexedDB
    const loadSystem = useCallback(async () => {
        try {
            // Tenta inicializar defaults se necessário (REMOVIDO para permitir Welcome Screen)
            // const defaultId = await db.initializeDefaults();
            const defaultId = null;

            // Carrega todos os dados do banco
            const storedWorkspaces = await db.workspaces.toArray();
            const storedFiles = await db.files.toArray();

            // Atualiza estado local
            setWorkspaces(storedWorkspaces);
            setFiles(storedFiles || []);

            // Lógica de Workspace Ativo
            if (storedWorkspaces.length > 0) {
                // Try to restore from localStorage
                const savedWsId = localStorage.getItem('omni_active_workspace');
                const initialWsId = (savedWsId && storedWorkspaces.find(w => w.id === savedWsId))
                    ? savedWsId
                    : (defaultId || storedWorkspaces[0].id);

                setActiveWorkspace(initialWsId);

                const wsObj = storedWorkspaces.find(w => w.id === initialWsId);
                if (wsObj && wsObj.connections?.length > 0) {
                    const firstConn = wsObj.connections[0];
                    const path = [{ id: firstConn.id, name: firstConn.name }];
                    setCurrentPath(path);
                    setHistory([path]);
                    setHistoryIndex(0);
                }
                setAppState('explorer');
            } else {
                // No workspaces — show welcome screen
                setWorkspaces([]);
                setFiles([]);
                setAppState('welcome');
            }
        } catch (error) {
            console.error("Falha ao carregar sistema de arquivos:", error);
            setAppState('error');
        }
    }, []);

    useEffect(() => {
        loadSystem();
    }, [loadSystem]);



    const currentFolderId = useMemo(() =>
        currentPath.length > 0 ? currentPath[currentPath.length - 1].id : null,
        [currentPath]);

    // Helper to process file in background (Hash & Thumbnail)
    const processFileInBackground = useCallback(async (fileRecord, fileBlob) => {
        if (!fileBlob) return;

        try {
            // 1. Calculate Hash
            const hash = await calculateHash(fileBlob);

            // 2. Generate Thumbnail (if image)
            let thumbnail = null;
            if (fileRecord.type === 'image') {
                thumbnail = await generateThumbnail(fileBlob);
            }

            // 3. Update DB & State
            if (hash || thumbnail) {
                const updates = {};
                if (hash) updates.hash = hash;
                if (thumbnail) updates.thumbnail = thumbnail;

                await db.files.update(fileRecord.id, updates);

                // Update local state to reflect changes (e.g. valid thumbnail)
                setFiles(prev => prev.map(f => f.id === fileRecord.id ? { ...f, ...updates } : f));
            }
        } catch (err) {
            console.error(`Processing failed for ${fileRecord.name}:`, err);
        }
    }, [calculateHash, generateThumbnail]);

    // Helpers de Navegação
    const updateHash = (wsId, folderId) => {
        const fId = folderId || 'root';
        const newHash = `/ws/${wsId}/folder/${fId}`;
        if (window.location.hash !== '#' + newHash) {
            window.location.hash = newHash;
        }
    };

    const navigate = useCallback(async (item) => {
        if (!item) return;

        console.log(`[FileSystem] Navigate to: ${item.name} (${item.type})`, item);

        if (item.type !== 'folder') {
            // It's a file - open preview
            console.log("[FileSystem] Opening file preview...");

            // Check if content is already loaded
            if (item.content !== undefined && item.content !== null) {
                console.log("[FileSystem] Content already loaded.");
                setPreviewFile(item);
                return;
            }

            // Fetch content from provider if missing
            if (provider) {
                console.log("[FileSystem] Provider instance:", provider);
                console.log("[FileSystem] Provider methods:", Object.getOwnPropertyNames(Object.getPrototypeOf(provider)));

                if (typeof provider.debugDownload === 'function' || typeof provider.getContent === 'function') {
                    console.log("[FileSystem] Fetching content via provider...");
                    const loadingToast = toast.loading(`Baixando ${item.name}...`);
                    try {
                        const content = typeof provider.debugDownload === 'function'
                            ? await provider.debugDownload(item.id)
                            : await provider.getContent(item.id);
                        console.log("[FileSystem] Content fetched:", content);

                        if (content === null || content === undefined) {
                            toast.dismiss(loadingToast);
                            toast.error("Não foi possível baixar o arquivo. Tente novamente.");
                            return;
                        }

                        const updatedFile = { ...item, content };

                        // Update state to cache content
                        setFiles(prev => prev.map(f => f.id === item.id ? updatedFile : f));

                        setPreviewFile(updatedFile);
                        toast.dismiss(loadingToast);
                    } catch (error) {
                        console.error("Error fetching file content:", error);
                        toast.dismiss(loadingToast);
                        toast.error(`Erro ao abrir arquivo: ${error.message}`);
                    }
                } else {
                    console.log("[FileSystem] No provider getContent, opening as is.");
                    // No provider or no getContent method - try opening anyway (might be empty)
                    setPreviewFile(item);
                }
                return;
            }
            return;
        }

        // Folder Navigation
        const newPath = [...currentPath, { id: item.id, name: item.name }];
        setCurrentPath(newPath);

        // Update URL Hash
        // We use a safe/url-friendly version of name? No, just ID is enough for logic, 
        // but typically hash routing wants hierarchy.
        // Our handleHashChange uses /ws/WSID/folder/FOLDERID
        // So we strictly need the ID.
        window.location.hash = `#/ws/${activeWorkspace}/folder/${item.id}`;

    }, [currentPath, activeWorkspace, provider, toast, setFiles, setPreviewFile]);

    const navigateBreadcrumb = useCallback((idx) => {
        const newPath = currentPath.slice(0, idx + 1);
        const newHistory = history.slice(0, historyIndex + 1);
        newHistory.push(newPath);
        setHistory(newHistory);
        setHistoryIndex(newHistory.length - 1);
        setCurrentPath(newPath);

        // Sync URL
        const folderId = newPath.length > 0 ? newPath[newPath.length - 1].id : null;
        updateHash(activeWorkspace, folderId);
    }, [currentPath, history, historyIndex, activeWorkspace]);

    const navigateBack = useCallback(() => {
        if (historyIndex > 0) {
            const newIndex = historyIndex - 1;
            const prevPath = history[newIndex];
            setHistoryIndex(newIndex);
            setCurrentPath(prevPath);

            // Sync URL hash
            const folderId = prevPath.length > 0 ? prevPath[prevPath.length - 1].id : null;
            updateHash(activeWorkspace, folderId);
        }
    }, [history, historyIndex, activeWorkspace]);

    const navigateForward = useCallback(() => {
        if (historyIndex < history.length - 1) {
            const newIndex = historyIndex + 1;
            const nextPath = history[newIndex];
            setHistoryIndex(newIndex);
            setCurrentPath(nextPath);

            // Sync URL hash
            const folderId = nextPath.length > 0 ? nextPath[nextPath.length - 1].id : null;
            updateHash(activeWorkspace, folderId);
        }
    }, [history, historyIndex, activeWorkspace]);

    const navigateToPath = useCallback((path) => {
        const newHistory = history.slice(0, historyIndex + 1);
        newHistory.push(path);
        setHistory(newHistory);
        setHistoryIndex(newHistory.length - 1);
        setCurrentPath(path);

        const folderId = path.length > 0 ? path[path.length - 1].id : null;
        updateHash(activeWorkspace, folderId);
    }, [history, historyIndex, activeWorkspace]);

    const navigateUp = useCallback(() => {
        if (currentPath.length > 1) {
            navigateBreadcrumb(currentPath.length - 2);
        } else if (currentPath.length === 1) {
            // Navigate to root
            navigateToPath([]);
        }
    }, [currentPath, navigateBreadcrumb, navigateToPath]);

    const switchWorkspace = useCallback((wsId) => {
        setActiveWorkspace(wsId);
        localStorage.setItem('omni_active_workspace', wsId); // Persist
        const ws = workspaces.find(w => w.id === wsId);
        if (ws && ws.connections.length > 0) {
            const conn = ws.connections[0];
            const path = [{ id: conn.id, name: conn.name }];
            setCurrentPath(path);
            setHistory([path]);
            setHistoryIndex(0);
            updateHash(wsId, conn.id);
        } else {
            setCurrentPath([]);
            updateHash(wsId, null);
        }
    }, [workspaces]);

    // --- ACTIONS (CRUD com IndexedDB) ---

    // 1. Create Workspace
    const createWorkspace = async (name, connections) => {
        const newWs = {
            id: `ws-${Date.now()}`, // String ID Explícito
            name,
            type: 'local',
            color: 'bg-blue-600',
            connections
        };

        try {
            await db.workspaces.put(newWs); // Persistência
            // Atualização de Estado
            setWorkspaces(prev => [...prev, newWs]);
            setActiveWorkspace(newWs.id);

            if (connections.length > 0) {
                const first = connections[0];
                const path = [{ id: first.id, name: first.name }];
                setCurrentPath(path);
                setHistory([path]);
                setHistoryIndex(0);
            }
            setAppState('explorer');
            toast.success(`Workspace "${name}" criado!`);
        } catch (error) {
            console.error("Erro ao criar workspace:", error);
            toast.error("Erro ao criar workspace.");
        }
    };

    // 1.1 Open Local Folder (File System Access API)
    const openLocalFolder = async () => {
        try {
            if (!window.showDirectoryPicker) {
                toast.error("Seu navegador não suporta acesso a pastas locais.");
                return;
            }

            const handle = await window.showDirectoryPicker();
            // Check if workspace already exists for this folder? 
            // For now, clean simple logic: create new workspace mode.

            const wsId = `ws-local-${Date.now()}`;
            const newWs = {
                id: wsId,
                name: handle.name,
                type: 'local-fs',
                color: 'bg-green-600',
                handle: handle, // Persists to IndexedDB
                connections: []
            };

            await db.workspaces.put(newWs);
            setWorkspaces(prev => [...prev, newWs]);
            setActiveWorkspace(wsId);
            setAppState('explorer');
            toast.success(`Pasta "${handle.name}" aberta!`);

        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error("Error opening local folder:", error);
                toast.error("Erro ao abrir pasta.");
            }
        }
    };



    const lastLoadRef = useRef({
        folderId: null,
        providerId: null,
        timestamp: 0,
        isLoading: false
    });

    // 1. Load Files (Triggered by Provider/Path changes)
    const loadFiles = useCallback(async () => {
        if (!provider) return;

        const providerId = provider.workspaceId || 'unknown';
        const now = Date.now();

        // Prevent rapid re-fetching loop (within 500ms) or parallel loads for same scope
        if (
            lastLoadRef.current.folderId === currentFolderId &&
            lastLoadRef.current.providerId === providerId
        ) {
            if (lastLoadRef.current.isLoading) {
                console.log(`[FileSystem] Skipping load - already in progress (Folder: ${currentFolderId})`);
                return;
            }
            if ((now - lastLoadRef.current.timestamp) < 500) {
                console.log(`[FileSystem] Skipping load - too soon (Folder: ${currentFolderId})`);
                return;
            }
        }

        lastLoadRef.current = {
            folderId: currentFolderId,
            providerId: providerId,
            timestamp: now,
            isLoading: true
        };

        console.log(`[FileSystem] Loading files... Folder: ${currentFolderId}, Provider: ${provider.constructor.name}`);
        // setIsLoading(true); // Don't block UI globally? Or use explicit state?
        // setAppState('loading-files'); // Optional

        try {
            let filesData = [];

            // 1. Special Views handling
            if (currentFolderId === 'favorites') {
                filesData = await provider.listStarred();
            } else if (currentFolderId === 'recent') {
                filesData = await provider.listRecent();
            } else if (currentFolderId === 'trash') {
                filesData = await provider.listTrash();
            } else if (currentFolderId && currentFolderId.startsWith('tag-')) {
                const tagId = currentFolderId.replace('tag-', '');
                filesData = await provider.listByTag(tagId);
            } else {
                // 2. Standard Folder / Root handling
                let fetchId = currentFolderId;
                let isConnectionRoot = false;

                // SPECIAL CASE: Connection Root
                if (activeWorkspaceObj?.connections?.some(c => c.id === currentFolderId)) {
                    fetchId = null; // 'root' for the provider
                    isConnectionRoot = true;
                }

                filesData = await provider.list(fetchId);

                // Fix: Override parentId if we are at connection root so App.jsx displays them
                if (isConnectionRoot && Array.isArray(filesData)) {
                    filesData.forEach(f => f.parentId = currentFolderId);
                }
            }

            console.log(`[FileSystem] Loaded ${filesData?.length} items.`);
            setFiles(filesData || []);
        } catch (error) {
            console.error("Erro ao carregar arquivos:", error);
            if (error.message && error.message.includes("Sessão Expirada")) {
                toast.error("Sessão expirada. Reconecte na aba Configurações.");
            } else {
                toast.error("Erro ao listar arquivos.");
            }
        } finally {
            setIsProcessing(false);
            lastLoadRef.current.isLoading = false;
        }
    }, [currentFolderId, provider, activeWorkspaceObj]);

    // Trigger Load whenever Provider or Folder changes
    useEffect(() => {
        loadFiles();
    }, [loadFiles]);


    // 2. Create Folder
    const createFolder = useCallback(async (name) => {
        if (!provider) return;
        setIsProcessing(true);
        try {
            const newFolder = await provider.createFolder(name, currentFolderId);
            setFiles(prev => [...prev, newFolder]);
            toast.success("Pasta criada!");
        } catch (error) {
            console.error("Erro ao criar pasta:", error);
            toast.error("Erro ao criar pasta.");
        } finally {
            setIsProcessing(false);
        }
    }, [currentFolderId, provider]);

    // 3. Soft Delete Files (Move to Local Trash)
    const deleteFiles = useCallback(async (ids) => {
        if (!provider) return;
        setIsProcessing(true);
        const timestamp = Date.now();
        const toastId = toast.loading("Movendo para lixeira...");

        try {
            // Check if we need to download content first (Remote Provider)
            const isRemote = provider.constructor.name === 'GoogleDriveProvider'; // Or other check

            if (isRemote) {
                // We need to fetch content for these files to "backup" them to local trash
                // This converts them to Local Files in the 'trash' state effectively.
                const itemsToBackup = files.filter(f => ids.includes(f.id));

                // We can't use db.files.update because these files might be remote-only representations in state?
                // Actually, 'files' state mixes local and remote if we navigated there?
                // If we are in Google Drive, 'files' are from Drive. They are NOT in IndexedDB yet (usually).
                // So we need to:
                // 1. Fetch content.
                // 2. Create new Local Records in IndexedDB with 'deletedAt' set.
                // 3. Trash/Delete on Remote.

                const backupPromises = [];

                // Helper to recursivelly scan and prepare items for backup
                const processBackupRecursive = async (item, localParentId) => {
                    // 1. Prepare Content
                    let content = item.content;
                    if (item.type !== 'folder' && !content && provider.getContent) {
                        try {
                            content = await provider.getContent(item.id);
                        } catch (e) {
                            console.warn(`Backup failed for ${item.name}`, e);
                            content = null;
                        }
                    }

                    // 2. Create Local Backup Record
                    const localBackup = {
                        ...item,
                        id: item.id,
                        workspaceId: activeWorkspace,
                        parentId: localParentId,
                        deletedAt: timestamp,
                        content: content,
                        originalProvider: 'google-drive'
                    };

                    backupPromises.push(db.files.put(localBackup));

                    // 3. If Folder, recurse
                    if (item.type === 'folder') {
                        try {
                            const children = await provider.list(item.id);
                            for (const child of children) {
                                await processBackupRecursive(child, item.id); // Child's parent is THIS folder's ID
                            }
                        } catch (e) {
                            console.error(`Failed to list children of ${item.name} for backup`, e);
                        }
                    }
                };

                for (const file of itemsToBackup) {
                    await processBackupRecursive(file, 'trash');
                }

                await Promise.all(backupPromises);
            } else {
                // Local Provider: Just update metadata
                await Promise.all(ids.map(id => db.files.update(id, { deletedAt: timestamp, parentId: 'trash' })));
            }

            // Update Provider (Trash in Cloud)
            if (provider.trash) {
                await provider.trash(ids);
            }

            // Update local state: Remove them from view (since they are now in trash)
            // If we are viewing 'trash', we might add them? 
            // Usually delete removes from current folder view.
            setFiles(prev => prev.filter(f => !ids.includes(f.id))); // Remove from view

            toast.success(`${ids.length} item(s) movido(s) para a lixeira.`);
        } catch (error) {
            console.error("Erro ao mover para lixeira:", error);
            toast.error("Erro ao excluir itens.");
        } finally {
            toast.dismiss(toastId);
            setIsProcessing(false);
        }
    }, [provider, files, activeWorkspace]);

    // 3.1 Restore Files from Trash
    const restoreFiles = useCallback(async (ids) => {
        setIsProcessing(true);
        try {
            await Promise.all(ids.map(id => db.files.update(id, { deletedAt: null })));
            setFiles(prev => prev.map(f => ids.includes(f.id) ? { ...f, deletedAt: null } : f));
            toast.success(`${ids.length} item(s) restaurado(s).`);
        } catch (error) {
            console.error("Erro ao restaurar:", error);
            toast.error("Erro ao restaurar itens.");
        } finally {
            setIsProcessing(false);
        }
    }, []);

    // 3.2 Permanent Delete (Empty Trash / Specific)
    const permanentDeleteFiles = useCallback(async (ids) => {
        if (!provider) return;
        setIsProcessing(true);
        try {
            // Delete from Provider (S3/Drive/FS)
            // Note: For now, our provider.delete() might need to be robust. 
            // We assume provider.delete() physically removes files.
            await provider.delete(ids);

            // Remove from DB
            await db.files.bulkDelete(ids);

            // Update local state
            setFiles(prev => prev.filter(f => !ids.includes(f.id)));

            toast.success(`${ids.length} item(s) deletado(s) permanentemente.`);
        } catch (error) {
            console.error("Erro ao deletar permanentemente:", error);
            toast.error("Erro ao deletar itens.");
        } finally {
            setIsProcessing(false);
        }
    }, [provider]);

    // 3.3 Empty Trash
    const emptyTrash = useCallback(async () => {
        const trashItems = files.filter(f => f.workspaceId === activeWorkspace && f.deletedAt);
        if (trashItems.length === 0) return;

        await permanentDeleteFiles(trashItems.map(f => f.id));
    }, [files, activeWorkspace, permanentDeleteFiles]);

    // 4. Rename File
    const renameFile = useCallback(async (id, newName) => {
        if (!provider) return;
        try {
            await provider.rename(id, newName);
            setFiles(prev => prev.map(f => f.id === id ? { ...f, name: newName } : f));
            toast.success("Renomeado com sucesso!");
        } catch (error) {
            console.error("Erro ao renomear ficheiro:", error);
            toast.error("Erro ao renomear.");
        }
    }, [provider]);

    // 5. Add Files (Upload)
    const addFiles = useCallback(async (newFiles) => {
        if (!provider) return;
        setIsProcessing(true);

        // Prepare files
        const preparedFiles = newFiles.map(f => ({
            ...f,
            parentId: f.parentId || currentFolderId,
            workspaceId: f.workspaceId || activeWorkspace
        }));

        try {
            // Save initial records (Fast)
            const savedFiles = await provider.saveFiles(preparedFiles);
            setFiles(prev => [...prev, ...savedFiles]);
            toast.success(`${newFiles.length} ficheiro(s) adicionado(s).`);

            // Trigger Background Processing
            savedFiles.forEach(savedFile => {
                // Find original blob content
                const original = newFiles.find(nf => nf.name === savedFile.name && nf.size === savedFile.size); // simpler match
                if (original && original.content instanceof Blob) {
                    processFileInBackground(savedFile, original.content);
                } else if (original && original.content instanceof File) {
                    processFileInBackground(savedFile, original.content);
                }
            });

        } catch (error) {
            console.error("Erro ao adicionar ficheiros:", error);
            toast.error("Erro ao salvar arquivos.");
        } finally {
            setIsProcessing(false);
        }
    }, [currentFolderId, activeWorkspace, provider, processFileInBackground]);

    // 6. Import Dropped Files (Recursive Folder Support)
    const importDroppedFiles = useCallback(async (items) => {
        const loadingToast = toast.loading("Processando arquivos...");
        setIsProcessing(true);
        const folderCache = {};
        const newFiles = [];
        const newFolders = [];
        const filesToProcess = []; // Store { record, blob }

        const ensureFolder = async (path, rootParentId) => {
            if (!path || path === '.') return rootParentId;
            if (folderCache[path]) return folderCache[path];
            const parts = path.split('/');
            let currentParent = rootParentId;
            let currentPath = '';
            for (const part of parts) {
                currentPath = currentPath ? `${currentPath}/${part}` : part;
                if (folderCache[currentPath]) { currentParent = folderCache[currentPath]; continue; }
                const existing = files.find(f => f.parentId === currentParent && f.name === part && f.type === 'folder');
                if (existing) { currentParent = existing.id; folderCache[currentPath] = existing.id; }
                else {
                    const folderId = `folder-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                    const folder = { id: folderId, parentId: currentParent, workspaceId: activeWorkspace, name: part, type: 'folder', size: '--', date: new Date().toLocaleDateString() };
                    newFolders.push(folder);
                    folderCache[currentPath] = folderId;
                    currentParent = folderId;
                }
            }
            return currentParent;
        };

        try {
            for (const item of items) {
                const lastSlash = item.path.lastIndexOf('/');
                const folderPath = lastSlash > -1 ? item.path.substring(0, lastSlash) : null;
                const fileName = lastSlash > -1 ? item.path.substring(lastSlash + 1) : item.path;

                let specificParentId = currentFolderId;
                if (folderPath) {
                    specificParentId = await ensureFolder(folderPath, currentFolderId); // eslint-disable-line
                }

                let content = item.file;
                // Only read text content for small files to avoid memory issues
                // Images and others are kept as Blob/File objects
                if (item.file.size < 2 * 1024 * 1024) { // < 2MB for text auto-read
                    if (
                        item.file.type.startsWith('text/') ||
                        item.file.type === 'application/json' ||
                        item.file.type === 'application/javascript' ||
                        item.file.name.endsWith('.md') ||
                        item.file.name.endsWith('.txt') ||
                        item.file.name.endsWith('.html') ||
                        item.file.name.endsWith('.css') ||
                        item.file.name.endsWith('.js') ||
                        item.file.name.endsWith('.jsx') ||
                        item.file.name.endsWith('.json')
                    ) {
                        content = await new Promise(r => {
                            const reader = new FileReader();
                            reader.onload = e => r(e.target.result);
                            reader.readAsText(item.file);
                        });
                    }
                    // We do NOT read images as DataURL anymore to save DB space and memory.
                    // Storing Blob is efficient in IndexedDB.
                    // Preview component will handle URL.createObjectURL(blob).
                }

                const newFileRecord = {
                    id: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                    parentId: specificParentId,
                    workspaceId: activeWorkspace,
                    name: fileName,
                    type: item.file.type.startsWith('image/') ? 'image' : item.file.type.includes('pdf') ? 'pdf' : 'file',
                    size: item.file.size > 1024 * 1024 ? (item.file.size / 1024 / 1024).toFixed(2) + ' MB' : (item.file.size / 1024).toFixed(2) + ' KB',
                    sizeRaw: item.file.size,
                    date: new Date().toLocaleDateString(),
                    content: content
                };
                newFiles.push(newFileRecord);
                filesToProcess.push({ record: newFileRecord, blob: item.file });
            }

            if (newFolders.length > 0) {
                if (provider) {
                    // Update folders with provider response (containing real IDs) if applicable
                    const savedFolders = await provider.saveFiles(newFolders);
                    if (savedFolders && savedFolders.length > 0) {
                        setFiles(prev => [...prev, ...savedFolders]);
                        // Also update folder cache if needed, but cache uses path -> id mapping.
                        // If ID changes, we might need to update cache or let it refresh?
                        // For drive, paths are not unique keys, IDs are.
                        // Complex: if we created a folder and got a new ID, subsequent file creations 
                        // in that folder (recursive upload) need the NEW ID.

                        // Recursive upload logic (ensureFolder) returns currentParent (local ID).
                        // If provider swaps it for a real ID, we must map OldID -> NewID for children.
                        const idMap = {};
                        newFolders.forEach((nf, i) => {
                            if (savedFolders[i]) idMap[nf.id] = savedFolders[i].id;
                        });

                        // Update parentIds in newFiles if they referred to temporary folder IDs
                        newFiles.forEach(nf => {
                            if (idMap[nf.parentId]) nf.parentId = idMap[nf.parentId];
                        });
                    } else {
                        setFiles(prev => [...prev, ...newFolders]);
                    }
                } else {
                    setFiles(prev => [...prev, ...newFolders]);
                }
            }

            if (newFiles.length > 0) {
                if (provider) {
                    const savedFiles = await provider.saveFiles(newFiles);
                    if (savedFiles && savedFiles.length > 0) {
                        setFiles(prev => [...prev, ...savedFiles]);

                        // Update filesToProcess with new IDs if needed for background processing?
                        // Background processing usually deals with thumbnails/content analysis.
                        // It uses 'record'. We should update 'record.id' to real ID.
                        // Assuming order is preserved.
                        savedFiles.forEach((sf, i) => {
                            if (filesToProcess[i]) filesToProcess[i].record.id = sf.id;
                        });
                    } else {
                        setFiles(prev => [...prev, ...newFiles]);
                    }
                } else {
                    setFiles(prev => [...prev, ...newFiles]);
                }
            }
            toast.dismiss(loadingToast);
            toast.success(`${newFiles.length} arquivos importados!`);

            // Trigger Background Processing
            filesToProcess.forEach(({ record, blob }) => {
                processFileInBackground(record, blob);
            });

        } catch (error) {
            console.error("Import failed:", error);
            toast.dismiss(loadingToast);
            toast.error("Falha na importação.");
        } finally {
            setIsProcessing(false);
        }
    }, [currentFolderId, activeWorkspace, files, provider, processFileInBackground]);

    // 7. Download File
    const downloadFile = useCallback(async (file) => {
        if (!file) return;

        // If folder, use Zip download
        if (file.type === 'folder') {
            return downloadFiles([file.id]);
        }

        let content = file.content;

        // Fetch content if missing
        if ((content === undefined || content === null) && provider) {
            const loadingToast = toast.loading(`Baixando ${file.name}...`);
            try {
                content = await provider.getContent(file.id);
                // We don't necessarily update state here, just download
                toast.dismiss(loadingToast);
            } catch (error) {
                console.error("Error downloading file content:", error);
                toast.dismiss(loadingToast);
                toast.error("Erro ao baixar arquivo.");
                return;
            }
        }

        let blob = null;
        if (content instanceof Blob || content instanceof File) {
            blob = content;
        } else if (typeof content === 'string') {
            blob = new Blob([content], { type: 'text/plain' });
            if (content.startsWith('data:')) {
                // Fetch data url to blob
                fetch(content).then(res => res.blob()).then(b => {
                    const url = URL.createObjectURL(b);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = file.name;
                    a.click();
                    URL.revokeObjectURL(url);
                });
                return;
            }
        } else {
            toast.error("Arquivo vazio ou inválido para download.");
            return;
        }

        if (blob) {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.name;
            a.click();
            URL.revokeObjectURL(url);
            toast.success("Download iniciado.");
        }
    }, [provider, toast]);

    // 7.1 Toggle Star (Favorites)
    const toggleStar = useCallback(async (file) => {
        if (!file) return;
        try {
            const newStatus = !file.isStarred;
            await db.files.update(file.id, { isStarred: newStatus });

            setFiles(prev => prev.map(f => f.id === file.id ? { ...f, isStarred: newStatus } : f));

            if (newStatus) toast.success("Adicionado aos Favoritos");
            else toast.success("Removido dos Favoritos");
        } catch (error) {
            console.error("Error toggling star:", error);
            toast.error("Erro ao atualizar favoritos.");
        }
    }, [setFiles, toast]);

    // Update Workspace Data (Settings)
    const updateWorkspaceData = async (newData) => {
        try {
            if (newData.workspaces) {
                await db.workspaces.bulkPut(newData.workspaces);
                setWorkspaces(newData.workspaces);
            }
            if (newData.files) {
                await db.files.bulkPut(newData.files);
                setFiles(newData.files);
            }
        } catch (error) {
            console.error("Erro ao atualizar dados do workspace:", error);
        }
    };

    // System Reset
    const resetSystem = async () => {
        try {
            await db.delete();
            localStorage.clear(); // Clear all prefs
            window.location.reload();
        } catch (error) {
            console.error("Erro ao resetar sistema:", error);
        }
    };

    // --- CLIPBOARD ACTIONS ---
    const pasteFiles = useCallback(async (items, action) => {
        if (!provider) return;
        if (!items || items.length === 0) return;

        const loadingToast = toast.loading(action === 'cut' ? "Movendo arquivos..." : "Copiando arquivos...");
        const newFiles = [];

        try {
            for (const item of items) {
                // Prepare new item
                let newItem = { ...item };
                newItem.id = `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                newItem.parentId = currentFolderId;
                newItem.workspaceId = activeWorkspace;
                newItem.date = new Date().toLocaleDateString(); // Update date

                // Handle Name Collision
                const existingName = files.find(f => f.parentId === currentFolderId && f.name === item.name);
                if (existingName) {
                    const nameParts = item.name.lastIndexOf('.') > 0
                        ? [item.name.substring(0, item.name.lastIndexOf('.')), item.name.substring(item.name.lastIndexOf('.'))]
                        : [item.name, ''];
                    newItem.name = `${nameParts[0]} (Cópia)${nameParts[1]}`;
                }

                // If Cut, we effectively want to move. 
                // However, providers might have efficient 'move' or we just 'copy & delete'.
                // For simplicity and safety across providers (S3/Drive), we'll treat as copy for now, 
                // then delete original if 'cut' success.
                // UNLESS it's the SAME workspace/provider, where we can just update parentId.

                // For now, let's treat everything as "Copy to new location".
                // TODO: Optimize 'Cut' within same provider to just update metadata.

                newFiles.push(newItem);
            }

            // Save new files
            const saved = await provider.saveFiles(newFiles);
            setFiles(prev => [...prev, ...saved]);

            // If Cut, delete originals
            if (action === 'cut') {
                await deleteFiles(items.map(i => i.id));
            }

            toast.dismiss(loadingToast);
            toast.success(action === 'cut' ? "Arquivos movidos!" : "Arquivos copiados!");
        } catch (error) {
            console.error("Paste failed:", error);
            toast.dismiss(loadingToast);
            toast.error("Erro ao colar arquivos.");
        }
    }, [provider, currentFolderId, activeWorkspace, files, deleteFiles]);

    // --- SEARCH & ROUTING ---
    // Hash is now updated directly inside navigate/navigateBack/navigateForward/navigateToPath.
    // No separate useEffect needed (which was causing infinite loops).


    // Hash Routing Listener (Source of Truth for "Back" button and Initial Load)
    useEffect(() => {
        const handleHashChange = async () => {
            const hash = window.location.hash; // #/ws/WSID/folder/FOLDERID
            if (!hash) return;

            if (hash.startsWith('#/ws/')) {
                const parts = hash.split('/');
                const wsId = parts[2];
                let folderId = parts[4];
                if (folderId === 'root') folderId = 'root'; // Keep explicit 'root' string for logic, or null? 
                // Let's standarize: Internal state uses null for root. URL uses 'root'.
                const targetFolderId = folderId === 'root' ? null : folderId;

                // 1. Switch Workspace if needed
                if (wsId && wsId !== activeWorkspace) {
                    setActiveWorkspace(wsId);
                    // Note: Changing activeWorkspace might trigger other effects. 
                    // ideally we should wait for that, but state updates are batched.
                }

                // 2. Resolve Path (Reconstruction)
                if (targetFolderId) {
                    // Handle Virtual Folders
                    if (targetFolderId === 'favorites') {
                        setCurrentPath([{ id: 'favorites', name: 'Favoritos' }]);
                        // History logic should be consistent?
                        return;
                    }
                    if (targetFolderId === 'recent') {
                        setCurrentPath([{ id: 'recent', name: 'Recentes' }]);
                        return;
                    }
                    if (targetFolderId === 'trash') {
                        setCurrentPath([{ id: 'trash', name: 'Lixeira' }]);
                        return;
                    }
                    if (targetFolderId.startsWith('tag-')) {
                        // We might need to fetch tag name?
                        // For now just show ID or generic.
                        setCurrentPath([{ id: targetFolderId, name: 'Tag' }]);
                        return;
                    }

                    // Handle Real Folders
                    // 1. Optimization: If we are already at this path (e.g. from navigate()), do nothing
                    if (currentPath.length > 0 && currentPath[currentPath.length - 1].id === targetFolderId) {
                        return;
                    }

                    // Check for Connections/Drives
                    const workspace = workspaces.find(w => w.id === wsId);
                    const connection = workspace?.connections?.find(c => c.id === targetFolderId);

                    if (connection) {
                        setCurrentPath([{ id: connection.id, name: connection.name }]);
                        return;
                    }

                    // 2. Try to find folder in current files (fast)
                    let targetFolder = files.find(f => f.id === targetFolderId && f.type === 'folder');

                    // 3. If not found, fetch from DB (Slow/Reload/Deep Link)
                    if (!targetFolder) {
                        try {
                            targetFolder = await db.files.get(targetFolderId);
                        } catch (err) {
                            console.error("Error fetching folder from DB:", err);
                        }
                    }

                    if (!targetFolder) {
                        // 404 - Folder truly not found
                        console.warn(`Folder ${targetFolderId} not found in state or DB.`);
                        // Only redirect if we are sure (e.g. DB lookup failed)
                        // window.location.hash = `#/ws/${wsId}/folder/root`; 
                        // Let's go to root safely
                        setCurrentPath([]);
                        return;
                    }

                    // 4. Build Breadcrumbs (Traverse Up)
                    const newPath = [];
                    let current = targetFolder;
                    let depth = 0;

                    while (current && depth < 20) { // Safety break
                        newPath.unshift({ id: current.id, name: current.name });

                        if (!current.parentId) break;

                        // Legacy/Stale Data Fix: Handle 'root' parent from old DB cache
                        if (current.parentId === 'root') {
                            const driveConn = workspace?.connections?.find(c => c.serviceId === 'google-drive');
                            if (driveConn) {
                                newPath.unshift({ id: driveConn.id, name: driveConn.name });
                                break;
                            }
                        }

                        // Check if parentId is a connection
                        const parentConnection = workspace?.connections?.find(c => c.id === current.parentId);
                        if (parentConnection) {
                            newPath.unshift({ id: parentConnection.id, name: parentConnection.name });
                            break; // We reached the root (connection)
                        }

                        // Try to find parent in files or DB
                        let parent = files.find(f => f.id === current.parentId);
                        if (!parent) {
                            try {
                                parent = await db.files.get(current.parentId);
                            } catch (e) {
                                // ignore
                            }
                        }

                        current = parent;
                        depth++;
                    }

                    setCurrentPath(newPath);

                } else {
                    // Root
                    setCurrentPath([]);
                }
            }
        };

        // Call on mount to handle initial URL
        if (files.length > 0) {
            handleHashChange();
        }

        window.addEventListener('hashchange', handleHashChange);
        return () => window.removeEventListener('hashchange', handleHashChange);
    }, [activeWorkspace, files]); // Added files dependency to re-run when files load


    // Update Hash during programmatic Navigation
    // We modify the 'navigate' functions to update Hash, 
    // AND we remove the useEffect that auto-updates hash from state (to avoid loops).
    // ... See next edit for 'navigate' function updates.



    const downloadFiles = useCallback(async (fileIds) => {
        if (!fileIds || fileIds.length === 0) return;

        const toastId = toast.loading(`Preparando download de ${fileIds.length} arquivos...`);
        setIsProcessing(true);

        try {
            const zip = new JSZip();

            // Helper for recursion
            const processItem = async (item, currentZipFolder) => {
                if (!item) return;

                if (item.type === 'folder') {
                    const newZipFolder = currentZipFolder.folder(item.name);
                    // Fetch children
                    // We must use provider.list because children might not be in state
                    if (provider && typeof provider.list === 'function') {
                        try {
                            // Note: We might need to handle pagination if folders are huge, 
                            // but generic list() usually gives first page. 
                            // For simplicity, we assume generic list returns reasonable amount or we loop tokens.
                            // But provider.list signature varies?
                            // IndexedDBProject.list(folderId) -> array or object?
                            // GoogleDriveProvider.list(folderId) -> { files: [] }
                            // Let's normalize.

                            let children = [];
                            const result = await provider.list(item.id);

                            if (Array.isArray(result)) {
                                children = result;
                            } else if (result && Array.isArray(result.files)) {
                                children = result.files;
                            }

                            for (const child of children) {
                                await processItem(child, newZipFolder);
                            }
                        } catch (err) {
                            console.error(`Error listing folder ${item.name}:`, err);
                        }
                    }
                } else {
                    // It's a file
                    try {
                        let content = item.content;
                        if ((content === undefined || content === null) && provider) {
                            content = await provider.getContent(item.id);
                        }

                        if (content) {
                            currentZipFolder.file(item.name, content);
                        }
                    } catch (err) {
                        console.error(`Error downloading file ${item.name}:`, err);
                    }
                }
            };

            let successCount = 0;

            for (const id of fileIds) {
                // Find file in state or fetch if needed (usually in state if selected)
                let file = files.find(f => f.id === id);
                if (!file) {
                    // Try getting from DB or Provider if we have a way? 
                    // For downloadFiles(ids), ids usually come from selection in current view.
                    // But if deep fetch needed?
                    if (db && db.files) {
                        try {
                            file = await db.files.get(id);
                        } catch (e) { /* ignore */ }
                    }
                    // If still not found and we have provider.get?
                    if (db && db.files) {
                        try {
                            file = await db.files.get(id);
                        } catch (e) { /* ignore */ }
                    }
                }
                if (file) {
                    await processItem(file, zip);
                    successCount++;
                }
            }

            if (successCount > 0) {
                const content = await zip.generateAsync({ type: "blob" });
                saveAs(content, `download-${new Date().getTime()}.zip`);
                toast.success("Download concluído!");
            } else {
                toast.error("Nenhum arquivo válido para download.");
            }

        } catch (error) {
            console.error("Zip download failed:", error);
            toast.error("Erro ao criar arquivo Zip.");
        } finally {
            toast.dismiss(toastId);
            setIsProcessing(false);
        }
    }, [files, provider, toast, db]);

    // 8. Move Files
    const moveFiles = useCallback(async (filesToMove, target) => {
        // target: { folderId, workspaceId, connectionId }
        if (!filesToMove || filesToMove.length === 0 || !target) return;

        setIsProcessing(true);
        const toastId = toast.loading(`Movendo ${filesToMove.length} itens...`);

        try {
            // 1. Resolve Target Provider
            let targetProvider = provider;
            let targetWs = workspaces.find(w => w.id === target.workspaceId);

            // If target is in a different context (different workspace or connection)
            // We need to instantiate the correct provider.
            // Logic similar to 'provider' useMemo.
            if (target.connectionId) {
                // It's a connection (Drive, etc)
                const conn = targetWs?.connections?.find(c => c.id === target.connectionId);
                if (conn && conn.serviceId === 'google-drive') {
                    targetProvider = new GoogleDriveProvider(target.workspaceId, conn.token);
                } else if (conn) {
                    // Other providers...
                    targetProvider = getProvider(targetWs); // Fallback?
                }
            } else if (target.workspaceId !== activeWorkspace) {
                // Different local workspace
                targetProvider = getProvider(targetWs);
            }

            // Check if Source Provider == Target Provider
            // We can check class name or workspaceId + connectionId comparison
            const isSameProvider = (
                provider.workspaceId === targetProvider.workspaceId &&
                provider.constructor.name === targetProvider.constructor.name &&
                // Ideally check connection ID too if multiple drives?
                // For now, assume if same workspace and type, same provider instance/scope.
                // But if moving from Drive A to Drive B in same workspace?
                // provider usually holds token.
                provider.token === targetProvider.token
            );

            if (isSameProvider) {
                // Optimized Move
                await provider.move(filesToMove.map(f => f.id), target.folderId);

                // Update Local State if source is visible
                setFiles(prev => prev.map(f => filesToMove.find(tm => tm.id === f.id) ? { ...f, parentId: target.folderId } : f));
                // Note: If target folder is also visible (e.g. expanded tree), we might need to refresh?
                // But effectively they disappear from current view if we are looking at source folder.

                toast.success("Arquivos movidos!");
            } else {
                // Cross-Provider Compability (Move = Copy Recursive + Delete)

                // 1. Copy (Upload using addFiles logic but to target)
                const itemsToUpload = [];

                // Helper to recursivelly scan and prepare items
                const processItemRecursive = async (item, targetParentId) => {
                    // 1. Prepare Item
                    const newId = `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

                    let content = item.content;
                    if (item.type !== 'folder' && !content && provider.getContent) {
                        try {
                            content = await provider.getContent(item.id);
                        } catch (e) {
                            console.warn(`Failed to fetch content for ${item.name}`, e);
                        }
                    }

                    const newItem = {
                        ...item,
                        id: newId,
                        parentId: targetParentId,
                        workspaceId: target.workspaceId,
                        content: content
                    };
                    itemsToUpload.push(newItem);

                    // 2. If Folder, recurse
                    if (item.type === 'folder') {
                        try {
                            const children = await provider.list(item.id);
                            for (const child of children) {
                                await processItemRecursive(child, newId);
                            }
                        } catch (e) {
                            console.error(`Failed to list children of ${item.name}`, e);
                        }
                    }
                };

                for (const file of filesToMove) {
                    await processItemRecursive(file, target.folderId);
                }

                // Use targetProvider.saveFiles
                await targetProvider.saveFiles(itemsToUpload);

                // 2. Delete from Source
                await deleteFiles(filesToMove.map(f => f.id)); // Soft delete? Or permanent?
                // Usually "Move" implies disappearing from source. 
                // Using 'deleteFiles' moves to trash.
                // Ideally we should permanently delete or offer option.
                // Let's use permanentDelete because we have a copy.
                await permanentDeleteFiles(filesToMove.map(f => f.id));

                toast.success("Arquivos movidos (entre provedores)!");
            }

        } catch (error) {
            console.error("Move failed:", error);
            toast.error("Erro ao mover arquivos.");
        } finally {
            toast.dismiss(toastId);
            setIsProcessing(false);
        }
    }, [provider, workspaces, activeWorkspace, deleteFiles, permanentDeleteFiles]);

    // 9. Copy Files
    const copyFiles = useCallback(async (filesToCopy, target) => {
        if (!filesToCopy || filesToCopy.length === 0 || !target) return;

        setIsProcessing(true);
        const toastId = toast.loading(`Copiando ${filesToCopy.length} itens...`);

        try {
            // 1. Resolve Target Provider (Same logic as Move)
            let targetProvider = provider;
            let targetWs = workspaces.find(w => w.id === target.workspaceId);

            if (target.connectionId) {
                const conn = targetWs?.connections?.find(c => c.id === target.connectionId);
                if (conn && conn.serviceId === 'google-drive') {
                    targetProvider = new GoogleDriveProvider(target.workspaceId, conn.token);
                } else if (conn) targetProvider = getProvider(targetWs);
            } else if (target.workspaceId !== activeWorkspace) {
                targetProvider = getProvider(targetWs);
            }

            const isSameProvider = (
                provider.workspaceId === targetProvider.workspaceId &&
                provider.constructor.name === targetProvider.constructor.name &&
                provider.token === targetProvider.token
            );

            if (isSameProvider) {
                await provider.copy(filesToCopy.map(f => f.id), target.folderId);
                toast.success("Arquivos copiados!");
                // If we are copying into CURRENT folder, we need to refresh local state
                if (target.folderId === currentFolderId) {
                    loadFiles(); // Re-fetch to see copies
                }
            } else {
                // Cross-Provider: Download -> Upload (Recursive)
                const itemsToUpload = [];

                // Helper to recursivelly scan and prepare items
                const processItemRecursive = async (item, targetParentId) => {
                    // 1. Prepare Item
                    const newId = `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

                    let content = item.content;
                    if (item.type !== 'folder' && !content && provider.getContent) {
                        try {
                            content = await provider.getContent(item.id);
                        } catch (e) {
                            console.warn(`Failed to fetch content for ${item.name}`, e);
                        }
                    }

                    const newItem = {
                        ...item,
                        id: newId, // Temporary ID for batch resolution
                        parentId: targetParentId,
                        workspaceId: target.workspaceId,
                        content: content
                    };
                    itemsToUpload.push(newItem);

                    // 2. If Folder, recurse
                    if (item.type === 'folder') {
                        // We need to list children of THIS item from the SOURCE provider
                        try {
                            const children = await provider.list(item.id);
                            for (const child of children) {
                                await processItemRecursive(child, newId); // Pass temp ID as parent
                            }
                        } catch (e) {
                            console.error(`Failed to list children of ${item.name}`, e);
                        }
                    }
                };

                // Process all selected root items
                for (const file of filesToCopy) {
                    await processItemRecursive(file, target.folderId);
                }

                // Upload all
                const saved = await targetProvider.saveFiles(itemsToUpload);

                // If target is current, add to state (root items only?)
                // Actually saveFiles returns everything. We should probably only add roots or trigger reload.
                // Simpler: if target is current folder, just reload or add all?
                // Adding all might duplicate if we are in root. 
                // Let's just reloadFiles if we are in the target folder.
                if (target.folderId === currentFolderId && target.workspaceId === activeWorkspace) {
                    loadFiles();
                }
                toast.success("Arquivos copiados (entre provedores)!");
            }
        } catch (error) {
            console.error("Copy failed:", error);
            toast.error("Erro ao copiar arquivos.");
        } finally {
            toast.dismiss(toastId);
            setIsProcessing(false);
        }
    }, [provider, workspaces, activeWorkspace, currentFolderId, loadFiles]);

    return {
        appState, setAppState,
        workspaces, activeWorkspace, activeWorkspaceObj,
        files: safeFiles, setFiles,
        currentPath, historyIndex, history,
        previewFile, setPreviewFile,
        currentFolderId,
        navigate, navigateBreadcrumb, navigateBack, navigateForward, navigateToPath, navigateUp,
        switchWorkspace, createWorkspace, openLocalFolder, updateWorkspaceData, resetSystem,
        createFolder, deleteFiles, renameFile, addFiles, importDroppedFiles, downloadFile,
        pasteFiles,
        isProcessing,
        toggleStar,
        moveFiles,
        copyFiles,
        restoreFiles, permanentDeleteFiles, emptyTrash, downloadFiles,
        loadSystem,
        db, // Expose db for components like TagManager
        provider // Export provider for advanced use if needed
    };
}
