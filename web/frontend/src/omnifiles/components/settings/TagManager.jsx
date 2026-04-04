import React, { useState } from 'react';
import { Plus, X, Trash2, Edit2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const COLORS = [
    { name: 'Red', value: 'bg-red-500' },
    { name: 'Orange', value: 'bg-orange-500' },
    { name: 'Amber', value: 'bg-amber-500' },
    { name: 'Yellow', value: 'bg-yellow-500' },
    { name: 'Lime', value: 'bg-lime-500' },
    { name: 'Green', value: 'bg-green-500' },
    { name: 'Emerald', value: 'bg-emerald-500' },
    { name: 'Teal', value: 'bg-teal-500' },
    { name: 'Cyan', value: 'bg-cyan-500' },
    { name: 'Sky', value: 'bg-sky-500' },
    { name: 'Blue', value: 'bg-blue-500' },
    { name: 'Indigo', value: 'bg-indigo-500' },
    { name: 'Violet', value: 'bg-violet-500' },
    { name: 'Purple', value: 'bg-purple-500' },
    { name: 'Fuchsia', value: 'bg-fuchsia-500' },
    { name: 'Pink', value: 'bg-pink-500' },
    { name: 'Rose', value: 'bg-rose-500' }
];

export const TagManager = ({ tags, onAddTag, onUpdateTag, onDeleteTag }) => {
    const { t } = useTranslation();
    const [isCreating, setIsCreating] = useState(false);
    const [editingTag, setEditingTag] = useState(null);
    const [tagName, setTagName] = useState('');
    const [tagColor, setTagColor] = useState(COLORS[10].value); // Default Blue

    const resetForm = () => {
        setTagName('');
        setTagColor(COLORS[10].value);
        setIsCreating(false);
        setEditingTag(null);
    };

    const handleSubmit = () => {
        if (!tagName.trim()) return;

        if (editingTag) {
            onUpdateTag(editingTag.id, { name: tagName, color: tagColor });
        } else {
            onAddTag(tagName, tagColor);
        }
        resetForm();
    };

    const startEdit = (tag) => {
        setEditingTag(tag);
        setTagName(tag.name);
        setTagColor(tag.color);
        setIsCreating(true);
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-white">Gerenciar Tags</h3>
                {!isCreating && (
                    <button
                        onClick={() => setIsCreating(true)}
                        className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-md text-sm transition-colors"
                    >
                        <Plus size={16} /> Nova Tag
                    </button>
                )}
            </div>

            {isCreating && (
                <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 animate-in fade-in slide-in-from-top-2">
                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs text-slate-400 mb-1 uppercase tracking-wider">Nome da Tag</label>
                            <input
                                type="text"
                                value={tagName}
                                onChange={(e) => setTagName(e.target.value)}
                                className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                placeholder="Ex: Projetos, Importante..."
                                autoFocus
                            />
                        </div>
                        <div>
                            <label className="block text-xs text-slate-400 mb-2 uppercase tracking-wider">Cor</label>
                            <div className="flex flex-wrap gap-2">
                                {COLORS.map(c => (
                                    <button
                                        key={c.name}
                                        onClick={() => setTagColor(c.value)}
                                        className={`w-6 h-6 rounded-full transition-all ${c.value} ${tagColor === c.value ? 'ring-2 ring-white scale-110' : 'hover:scale-105 opacity-80 hover:opacity-100'}`}
                                        title={c.name}
                                    />
                                ))}
                            </div>
                        </div>
                        <div className="flex justify-end gap-2 pt-2">
                            <button
                                onClick={resetForm}
                                className="px-3 py-1.5 text-slate-400 hover:text-white text-sm"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleSubmit}
                                disabled={!tagName.trim()}
                                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-md text-sm"
                            >
                                {editingTag ? 'Salvar Alterações' : 'Criar Tag'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {tags.length === 0 && !isCreating && (
                    <div className="col-span-2 text-center py-8 text-slate-500 italic">
                        Nenhuma tag criada.
                    </div>
                )}
                {tags.map(tag => (
                    <div key={tag.id} className="flex items-center justify-between p-3 bg-slate-800/50 border border-slate-700/50 rounded-lg group hover:border-slate-600 transition-colors">
                        <div className="flex items-center gap-3">
                            <div className={`w-3 h-3 rounded-full ${tag.color}`}></div>
                            <span className="text-slate-200 font-medium">{tag.name}</span>
                        </div>
                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={() => startEdit(tag)} className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-700 rounded">
                                <Edit2 size={14} />
                            </button>
                            <button
                                onClick={() => {
                                    if (window.confirm('Tem certeza? Isso removerá a tag de todos os arquivos.')) {
                                        onDeleteTag(tag.id);
                                    }
                                }}
                                className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-700 rounded"
                            >
                                <Trash2 size={14} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
