
import React from 'react';
import { X, FileText, Image, Folder, Tag, Calendar, Database, HardDrive, Info } from 'lucide-react';
import { formatBytes, formatDate } from '../../utils/formatters';
import PropTypes from 'prop-types';

export const DetailsPanel = ({ isOpen, onClose, selectedFiles, tags, onToggleTag }) => {
    if (!isOpen) return null;

    const file = selectedFiles.length === 1 ? selectedFiles[0] : null;
    const isMultiple = selectedFiles.length > 1;

    const getIcon = (type) => {
        if (type === 'folder') return <Folder className="text-blue-400" size={48} />;
        if (type === 'image') return <Image className="text-purple-400" size={48} />;
        return <FileText className="text-slate-400" size={48} />;
    };

    return (
        <aside className="w-80 bg-slate-900 border-l border-slate-700 h-full flex flex-col shadow-xl absolute right-0 top-0 z-40 transition-transform duration-300">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-700 bg-slate-800/50">
                <h3 className="font-semibold text-slate-200 flex items-center gap-2">
                    <Info size={18} className="text-blue-400" /> Detalhes
                </h3>
                <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
                    <X size={20} />
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {selectedFiles.length === 0 ? (
                    <div className="text-center text-slate-500 mt-10">
                        <p>Nenhum item selecionado</p>
                    </div>
                ) : isMultiple ? (
                    <div className="text-center">
                        <div className="bg-slate-800/50 rounded-lg p-6 mb-4 inline-block">
                            <Database size={48} className="text-blue-400 mx-auto opacity-50" />
                        </div>
                        <h2 className="text-xl font-bold text-white mb-1">{selectedFiles.length} itens</h2>
                        <p className="text-slate-400 text-sm">selecionados</p>
                    </div>
                ) : (
                    <>
                        {/* File Preview/Icon */}
                        <div className="flex flex-col items-center justify-center py-4">
                            <div className="bg-slate-800 rounded-xl p-6 mb-4 shadow-lg ring-1 ring-slate-700/50">
                                {file.thumbnail ? (
                                    <img src={file.thumbnail} alt={file.name} className="w-32 h-32 object-cover rounded-md" />
                                ) : (
                                    getIcon(file.type)
                                )}
                            </div>
                            <h2 className="text-lg font-bold text-center text-white break-words w-full px-2">{file.name}</h2>
                        </div>

                        {/* Properties */}
                        <div className="space-y-4">
                            <div className="bg-slate-800/30 rounded-lg p-4 space-y-3 border border-slate-700/50">
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-500 text-xs uppercase font-bold flex items-center gap-1">
                                        <HardDrive size={12} /> Tipo
                                    </span>
                                    <span className="text-slate-300 text-sm">{file.type || 'Desconhecido'}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-500 text-xs uppercase font-bold flex items-center gap-1">
                                        <Database size={12} /> Tamanho
                                    </span>
                                    <span className="text-slate-300 text-sm">
                                        {formatBytes(file.sizeRaw || 0)}
                                        <span className="text-slate-600 text-xs ml-1">({file.size})</span>
                                    </span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-500 text-xs uppercase font-bold flex items-center gap-1">
                                        <Calendar size={12} /> Modificado
                                    </span>
                                    <span className="text-slate-300 text-sm">{file.date}</span>
                                </div>
                            </div>

                            {/* Tags Section */}
                            <div>
                                <h4 className="text-slate-400 text-xs font-bold uppercase mb-3 flex items-center gap-2">
                                    <Tag size={12} /> Etiquetas
                                </h4>
                                <div className="flex flex-wrap gap-2">
                                    {tags.map(tag => {
                                        const isSelected = file.tags && file.tags.includes(tag.id);
                                        return (
                                            <button
                                                key={tag.id}
                                                onClick={() => onToggleTag(file, tag.id)}
                                                className={`
                                                    px-2 py-1 rounded-full text-xs font-medium border transition-all
                                                    ${isSelected
                                                        ? 'bg-opacity-20 border-opacity-50 text-white'
                                                        : 'bg-transparent border-slate-700 text-slate-500 hover:border-slate-500'}
                                                `}
                                                style={{
                                                    backgroundColor: isSelected ? tag.color : 'transparent',
                                                    borderColor: isSelected ? tag.color : undefined
                                                }}
                                            >
                                                {tag.name}
                                            </button>
                                        );
                                    })}
                                    {tags.length === 0 && (
                                        <p className="text-slate-600 text-xs italic">Nenhuma tag criada.</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </aside>
    );
};

DetailsPanel.propTypes = {
    isOpen: PropTypes.bool.isRequired,
    onClose: PropTypes.func.isRequired,
    selectedFiles: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        type: PropTypes.string,
        size: PropTypes.string,
        sizeRaw: PropTypes.number,
        date: PropTypes.string,
        thumbnail: PropTypes.string,
        tags: PropTypes.array
    })).isRequired,
    tags: PropTypes.array.isRequired,
    onToggleTag: PropTypes.func.isRequired
};
