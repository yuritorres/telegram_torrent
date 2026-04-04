import React, { useState, useEffect } from 'react';
import { Folder, HardDrive, X, FileMinus, Copy, ChevronRight, ChevronDown, Monitor, Rocket } from 'lucide-react';
import { getProvider } from '../../providers/ProviderFactory';
import { GoogleDriveProvider } from '../../providers/GoogleDriveProvider';
import PropTypes from 'prop-types';

export const MoveCopyModal = ({ isOpen, onClose, filesToMove, workspaces, onMove, onCopy }) => {
    const [selectedTarget, setSelectedTarget] = useState(null); // { workspaceId, connectionId, folderId, name }
    const [expandedNodes, setExpandedNodes] = useState({});
    const [treeData, setTreeData] = useState({}); // Cache loaded children: { 'ws-id': [], 'conn-id': [], 'folder-id': [] }

    // Reset when improved
    useEffect(() => {
        if (isOpen) {
            setSelectedTarget(null);
            setExpandedNodes({});
            // Initial load of workspaces is implicit via props, but we might want to load roots
        }
    }, [isOpen]);

    if (!isOpen) return null;

    const toggleExpand = async (nodeId, providerResolver) => {
        const isExpanded = !!expandedNodes[nodeId];
        setExpandedNodes(prev => ({ ...prev, [nodeId]: !isExpanded }));

        if (!isExpanded && !treeData[nodeId]) {
            // Load children
            try {
                if (typeof providerResolver !== 'function') return;
                const provider = providerResolver();
                if (!provider) return;

                // Adjust ID for provider (remove prefix if needed?)
                // Helper to extract real ID from our composite node ID
                // Node ID scheme:
                // Workspace: ws-{id}
                // Connection: conn-{id}
                // Folder: folder-{id} (might duplicate if same ID in diff provider?)
                // Better: unique keys in treeData.

                // Let's rely on the node structure passed.
                // providerResolver returns the correct provider instance.
                // we pass the folder ID (or null for root).

                let folderId = null;
                if (nodeId.startsWith('folder-')) folderId = nodeId; // Real ID
                // If connection, folderId is 'root' (or null)
                // If workspace, folderId is null (local root)

                const items = await provider.list(folderId); // This might return files too
                const folders = items.filter(i => i.type === 'folder');

                setTreeData(prev => ({ ...prev, [nodeId]: folders }));
            } catch (err) {
                console.error("Error loading tree node:", err);
            }
        }
    };

    const handleSelect = (target) => {
        setSelectedTarget(target);
    };

    const renderTree = (nodes, parentId, depth = 0) => {
        return nodes.map(node => {
            const nodeId = node.id;
            const isExpanded = !!expandedNodes[nodeId];
            const hasChildren = treeData[nodeId] && treeData[nodeId].length > 0;
            const isLoaded = !!treeData[nodeId];
            const isSelected = selectedTarget?.folderId === nodeId || (selectedTarget?.workspaceId === node.workspaceId && !selectedTarget?.folderId && !selectedTarget?.connectionId && node.type === 'workspace');

            // Determine Provider Resolver for this node
            const resolveProvider = () => {
                // If node is workspace -> Local Provider
                // If node is connection -> Connection Provider
                // If node is folder -> need to know context.
                // We pass context down?
                return null; // Placeholder, logic in recursive caller
            };

            return (
                <div key={nodeId} style={{ paddingLeft: `${depth * 12}px` }}>
                    <div
                        className={`flex items-center gap-2 p-1.5 rounded cursor-pointer hover:bg-slate-700/50 ${isSelected ? 'bg-blue-600/20 text-blue-300' : 'text-slate-400'}`}
                        onClick={() => handleSelect(node)}
                    >
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                node.onToggle();
                            }}
                            className="p-0.5 hover:bg-slate-700 rounded"
                        >
                            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        </button>
                        {node.icon}
                        <span className="text-sm truncate select-none">{node.name}</span>
                    </div>
                    {isExpanded && (
                        <div>
                            {isLoaded ? (
                                treeData[nodeId].length > 0 ? (
                                    treeData[nodeId].map(child => (
                                        <FolderNode
                                            key={child.id}
                                            folder={child}
                                            workspaceId={node.originalWorkspaceId || node.workspaceId}
                                            connectionId={node.originalConnectionId || node.connectionId}
                                            depth={depth + 1}
                                            onToggle={toggleExpand}
                                            onSelect={handleSelect}
                                            selectedTarget={selectedTarget}
                                            expandedNodes={expandedNodes}
                                            treeData={treeData}
                                            token={node.token} // Pass token for drive
                                        />
                                    ))
                                ) : <div className="pl-6 py-1 text-xs text-slate-600 italic">Vazio</div>
                            ) : (
                                <div className="pl-6 py-1 text-xs text-slate-600 animate-pulse">Carregando...</div>
                            )}
                        </div>
                    )}
                </div>
            );
        });
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-2xl flex flex-col max-h-[85vh]">
                <div className="p-4 border-b border-slate-700 flex justify-between items-center">
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Copy size={20} className="text-blue-400" />
                        Mover ou Copiar
                    </h2>
                    <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-4 bg-slate-800/50">
                    <div className="text-sm text-slate-400 mb-2">Itens selecionados ({filesToMove.length}):</div>
                    <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto">
                        {filesToMove.map(f => (
                            <div key={f.id} className="bg-slate-800 border border-slate-700 px-2 py-1 rounded text-xs text-slate-300 flex items-center gap-2">
                                {f.type === 'folder' ? <Folder size={12} /> : <FileMinus size={12} />}
                                <span className="truncate max-w-[150px]">{f.name}</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-4 min-h-[300px]">
                    <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Selecione o Destino</div>

                    {/* Workspace Roots */}
                    {workspaces.map(ws => (
                        <WorkspaceRoot
                            key={ws.id}
                            workspace={ws}
                            onToggle={toggleExpand}
                            onSelect={handleSelect}
                            selectedTarget={selectedTarget}
                            expandedNodes={expandedNodes}
                            treeData={treeData}
                        />
                    ))}
                </div>

                <div className="p-4 border-t border-slate-700 bg-slate-800/30 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={() => selectedTarget && onCopy(filesToMove, selectedTarget)}
                        disabled={!selectedTarget}
                        className="px-4 py-2 text-sm bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        <Copy size={16} />
                        Clonar aqui
                    </button>
                    <button
                        onClick={() => selectedTarget && onMove(filesToMove, selectedTarget)}
                        disabled={!selectedTarget}
                        className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors ring-1 ring-white/10 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        <Rocket size={16} />
                        Mover para cá
                    </button>
                </div>
            </div>
        </div>
    );
};

// Sub-components to handle recursion and provider context

const WorkspaceRoot = ({ workspace, onToggle, onSelect, selectedTarget, expandedNodes, treeData }) => {
    const isExpanded = !!expandedNodes[workspace.id];

    // Virtual "Local" Node inside workspace
    const localNodeId = `${workspace.id}-local`;

    return (
        <div className="mb-2">
            <div
                className="flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-slate-800"
                onClick={() => onToggle(workspace.id)} // Expanding workspace just shows connections + local
            >
                {isExpanded ? <ChevronDown size={14} className="text-slate-500" /> : <ChevronRight size={14} className="text-slate-500" />}
                <div className={`w-4 h-4 rounded-sm ${workspace.color || 'bg-blue-600'}`}></div>
                <span className="text-sm font-medium text-slate-200">{workspace.name}</span>
            </div>

            {isExpanded && (
                <div className="pl-4 border-l border-slate-800 ml-2 mt-1 space-y-1">
                    {/* Local Files System Root */}
                    <div
                        className={`flex items-center gap-2 p-1.5 rounded cursor-pointer hover:bg-slate-700/50 ${selectedTarget?.folderId === null && selectedTarget?.workspaceId === workspace.id && !selectedTarget?.connectionId ? 'bg-blue-600/20 text-blue-300' : 'text-slate-400'}`}
                        onClick={() => onSelect({ workspaceId: workspace.id, connectionId: null, folderId: null, name: 'Arquivos Locais' })}
                    >
                        <button
                            onClick={(e) => { e.stopPropagation(); onToggle(localNodeId, () => getProvider(workspace)) }}
                            className="p-0.5 hover:bg-slate-700 rounded"
                        >
                            {expandedNodes[localNodeId] ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        </button>
                        <HardDrive size={16} className="text-green-400" />
                        <span className="text-sm">Arquivos Locais</span>
                    </div>
                    {expandedNodes[localNodeId] && (
                        <div className="pl-4">
                            {treeData[localNodeId] ? (
                                treeData[localNodeId].map(child => (
                                    <FolderNode
                                        key={child.id}
                                        folder={child}
                                        workspaceId={workspace.id}
                                        connectionId={null}
                                        depth={0}
                                        onToggle={onToggle}
                                        onSelect={onSelect}
                                        selectedTarget={selectedTarget}
                                        expandedNodes={expandedNodes}
                                        treeData={treeData}
                                        token={null}
                                    />
                                ))
                            ) : <div className="text-xs text-slate-600 pl-6 animate-pulse">Carregando...</div>}
                            {treeData[localNodeId] && treeData[localNodeId].length === 0 && <div className="text-xs text-slate-600 pl-6 italic">Vazio</div>}
                        </div>
                    )}

                    {/* Connections */}
                    {workspace.connections && workspace.connections.map(conn => (
                        <ConnectionRoot
                            key={conn.id}
                            connection={conn}
                            workspaceId={workspace.id}
                            onToggle={onToggle}
                            onSelect={onSelect}
                            selectedTarget={selectedTarget}
                            expandedNodes={expandedNodes}
                            treeData={treeData}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};

const ConnectionRoot = ({ connection, workspaceId, onToggle, onSelect, selectedTarget, expandedNodes, treeData }) => {
    const nodeId = connection.id;
    const isExpanded = !!expandedNodes[nodeId];
    const isSelected = selectedTarget?.connectionId === connection.id && selectedTarget?.folderId === connection.id; // Root of connection is folderId=connectionId

    const resolveProvider = () => {
        // Google Drive
        if (connection.serviceId === 'google-drive') {
            return new GoogleDriveProvider(workspaceId, connection.token);
        }
        return null;
    };

    return (
        <div>
            <div
                className={`flex items-center gap-2 p-1.5 rounded cursor-pointer hover:bg-slate-700/50 ${isSelected ? 'bg-blue-600/20 text-blue-300' : 'text-slate-400'}`}
                onClick={() => onSelect({ workspaceId, connectionId: connection.id, folderId: connection.id, name: connection.name })}
            >
                <button
                    onClick={(e) => { e.stopPropagation(); onToggle(nodeId, resolveProvider) }}
                    className="p-0.5 hover:bg-slate-700 rounded"
                >
                    {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>
                <Monitor size={16} className="text-blue-400" />
                <span className="text-sm truncate">{connection.name}</span>
            </div>
            {isExpanded && (
                <div className="pl-4">
                    {treeData[nodeId] ? (
                        treeData[nodeId].map(child => (
                            <FolderNode
                                key={child.id}
                                folder={child}
                                workspaceId={workspaceId}
                                connectionId={connection.id}
                                depth={0}
                                onToggle={onToggle}
                                onSelect={onSelect}
                                selectedTarget={selectedTarget}
                                expandedNodes={expandedNodes}
                                treeData={treeData}
                                token={connection.token}
                            />
                        ))
                    ) : <div className="text-xs text-slate-600 pl-6 animate-pulse">Carregando...</div>}
                </div>
            )}
        </div>
    );
};

const FolderNode = ({ folder, workspaceId, connectionId, depth, onToggle, onSelect, selectedTarget, expandedNodes, treeData, token }) => {
    const nodeId = folder.id;
    const isExpanded = !!expandedNodes[nodeId];
    const isSelected = selectedTarget?.folderId === folder.id;

    const resolveProvider = () => {
        if (connectionId) {
            // Re-instantiate provider using token (passed down or found?)
            // We need service type too. Assuming Drive for now if token present?
            // Or better, pass provider creator.
            // For now, simpler: pass token.
            return new GoogleDriveProvider(workspaceId, token);
        }
        return getProvider({ type: 'local', id: workspaceId }); // Defaults to IndexedDB
    };

    return (
        <div style={{ paddingLeft: '12px' }}>
            <div
                className={`flex items-center gap-2 p-1.5 rounded cursor-pointer hover:bg-slate-700/50 ${isSelected ? 'bg-blue-600/20 text-blue-300' : 'text-slate-400'}`}
                onClick={() => onSelect({ workspaceId, connectionId, folderId: folder.id, name: folder.name })}
            >
                <button
                    onClick={(e) => { e.stopPropagation(); onToggle(nodeId, resolveProvider) }}
                    className="p-0.5 hover:bg-slate-700 rounded"
                >
                    {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>
                <Folder size={16} className={isSelected ? 'text-blue-400' : 'text-slate-500'} />
                <span className="text-sm truncate select-none">{folder.name}</span>
            </div>
            {isExpanded && (
                <div>
                    {treeData[nodeId] ? (
                        treeData[nodeId].map(child => (
                            <FolderNode
                                key={child.id}
                                folder={child}
                                workspaceId={workspaceId}
                                connectionId={connectionId}
                                depth={depth + 1}
                                onToggle={onToggle}
                                onSelect={onSelect}
                                selectedTarget={selectedTarget}
                                expandedNodes={expandedNodes}
                                treeData={treeData}
                                token={token}
                            />
                        ))
                    ) : <div className="text-xs text-slate-600 pl-6 animate-pulse">Carregando...</div>}
                </div>
            )}
        </div>
    );
};

MoveCopyModal.propTypes = {
    isOpen: PropTypes.bool.isRequired,
    onClose: PropTypes.func.isRequired,
    filesToMove: PropTypes.array.isRequired,
    workspaces: PropTypes.array.isRequired,
    onMove: PropTypes.func.isRequired,
    onCopy: PropTypes.func.isRequired
};
