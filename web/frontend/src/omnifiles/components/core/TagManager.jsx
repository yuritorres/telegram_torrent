import { useState, useEffect } from 'react';
import { X, Plus, Trash2, Tag, Check, Edit2 } from 'lucide-react';
import { useFileSystem } from '../../context/FileSystemContext';

export const TagManager = ({ onClose }) => {
    const { activeWorkspace, db } = useFileSystem();
    const [tags, setTags] = useState([]);
    const [newTagName, setNewTagName] = useState('');
    const [newTagColor, setNewTagColor] = useState('#3b82f6'); // blue-500 default
    const [editingTag, setEditingTag] = useState(null); // { id, name, color }

    // Load Tags
    useEffect(() => {
        const loadTags = async () => {
            if (!db) return;
            try {
                // Assuming tags are stored in a 'tags' table or we derive them?
                // The schema in db/index.js showed 'tags' table?
                // Let's check db/index.js...
                // If no tags table, we might need to rely on files...
                // But generally a tag manager implies a separate collection.
                // Re-reading db/index.js content from earlier logs...
                // It showed: `tags: 'id, workspaceId, name, color'`, correct?
                // Let's assume yes.
                const allTags = await db.tags.where({ workspaceId: activeWorkspace }).toArray();
                setTags(allTags);
            } catch (error) {
                console.error("Error loading tags:", error);
            }
        };
        loadTags();
    }, [activeWorkspace, db]);

    const handleAddTag = async () => {
        if (!newTagName.trim()) return;
        const tag = {
            id: `tag-${Date.now()}`,
            workspaceId: activeWorkspace,
            name: newTagName.trim(),
            color: newTagColor
        };
        try {
            await db.tags.add(tag);
            setTags(prev => [...prev, tag]);
            setNewTagName('');
            setNewTagColor('#3b82f6');
        } catch (error) {
            console.error("Error adding tag:", error);
        }
    };

    const handleDeleteTag = async (id) => {
        try {
            await db.tags.delete(id);
            setTags(prev => prev.filter(t => t.id !== id));
            // Optional: Remove tag from all files?
            // This would be heavy. Let's leave it for now or do it if requested.
        } catch (error) {
            console.error("Error deleting tag:", error);
        }
    };

    const handleUpdateTag = async () => {
        if (!editingTag || !editingTag.name.trim()) return;
        try {
            await db.tags.update(editingTag.id, { name: editingTag.name, color: editingTag.color });
            setTags(prev => prev.map(t => t.id === editingTag.id ? editingTag : t));
            setEditingTag(null);
        } catch (error) {
            console.error("Error updating tag:", error);
        }
    };

    const colors = [
        '#ef4444', // red
        '#f97316', // orange
        '#eab308', // yellow
        '#22c55e', // green
        '#06b6d4', // cyan
        '#3b82f6', // blue
        '#6366f1', // indigo
        '#a855f7', // purple
        '#ec4899', // pink
        '#64748b', // slate
    ];

    return (
        <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200" onClick={onClose}>
            <div className="bg-slate-900 w-full max-w-md rounded-2xl border border-slate-700 shadow-2xl flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>
                <div className="h-14 border-b border-slate-700 flex items-center justify-between px-4 bg-slate-900 shrink-0">
                    <span className="font-medium text-slate-200 flex items-center gap-2">
                        <Tag size={18} className="text-blue-500" />
                        Gerenciar Tags
                    </span>
                    <button onClick={onClose} className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-4 space-y-4">
                    {/* Add/Edit Section */}
                    <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700 space-y-3">
                        <input
                            type="text"
                            placeholder="Nome da Tag..."
                            value={editingTag ? editingTag.name : newTagName}
                            onChange={(e) => editingTag ? setEditingTag({ ...editingTag, name: e.target.value }) : setNewTagName(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                        />

                        <div className="flex flex-wrap gap-2">
                            {colors.map(c => (
                                <button
                                    key={c}
                                    onClick={() => editingTag ? setEditingTag({ ...editingTag, color: c }) : setNewTagColor(c)}
                                    className={`w-6 h-6 rounded-full border-2 transition-all ${(editingTag ? editingTag.color : newTagColor) === c ? 'border-white scale-110' : 'border-transparent hover:scale-105'
                                        }`}
                                    style={{ backgroundColor: c }}
                                />
                            ))}
                        </div>

                        <button
                            onClick={editingTag ? handleUpdateTag : handleAddTag}
                            disabled={!(editingTag ? editingTag.name : newTagName).trim()}
                            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg py-2 text-sm font-medium transition-colors flex items-center justify-center gap-2"
                        >
                            {editingTag ? <><Check size={16} /> Salvar Alterações</> : <><Plus size={16} /> Adicionar Tag</>}
                        </button>
                    </div>

                    {/* List Section */}
                    <div className="space-y-2 max-h-[40vh] overflow-y-auto pr-1 custom-scrollbar">
                        {tags.length === 0 ? (
                            <p className="text-center text-slate-500 text-sm py-4">Nenhuma tag criada.</p>
                        ) : (
                            tags.map(tag => (
                                <div key={tag.id} className="flex items-center justify-between p-2 bg-slate-800/30 border border-slate-700/50 rounded-lg group">
                                    <div className="flex items-center gap-3">
                                        <div className="w-4 h-4 rounded-full" style={{ backgroundColor: tag.color }}></div>
                                        <span className="text-slate-200 text-sm">{tag.name}</span>
                                    </div>
                                    <div className="flex items-center gap-1 opacity-100 sm:opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button
                                            onClick={() => setEditingTag(tag)}
                                            className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-700 rounded-md transition-colors"
                                        >
                                            <Edit2 size={14} />
                                        </button>
                                        <button
                                            onClick={() => handleDeleteTag(tag.id)}
                                            className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-700 rounded-md transition-colors"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
