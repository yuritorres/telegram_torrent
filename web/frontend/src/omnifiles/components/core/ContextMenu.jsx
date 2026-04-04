import { useRef, useEffect } from 'react';
import { Folder, Upload, RefreshCw, ExternalLink, Edit2, Trash2, Info, Star, Tag, Check, Copy, Scissors, Clipboard, RotateCcw, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const ContextMenu = ({ x, y, target, tags = [], onClose, onAction, selectedCount = 1, isTrash = false, hasClipboard = false }) => {
    const menuRef = useRef(null);
    const { t } = useTranslation();

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                onClose();
            }
        };
        const handleCloseEvents = () => onClose();

        document.addEventListener('mousedown', handleClickOutside);
        window.addEventListener('scroll', handleCloseEvents, true);
        window.addEventListener('resize', handleCloseEvents);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
            window.removeEventListener('scroll', handleCloseEvents, true);
            window.removeEventListener('resize', handleCloseEvents);
        };
    }, [onClose]);

    // Position Adjustment
    const style = { top: y, left: x };
    if (x + 220 > window.innerWidth) style.left = x - 220;
    if (y + 300 > window.innerHeight) style.top = Math.max(10, y - 300);

    const MenuItem = ({ icon: Icon, label, onClick, className = '', danger = false }) => (
        <button onClick={onClick} className={`w-full text-left px-4 py-2 text-sm flex items-center gap-2 transition-colors ${danger ? 'text-red-400 hover:bg-red-900/30 hover:text-red-300' : 'text-slate-300 hover:bg-slate-700 hover:text-white'} ${className}`}>
            <Icon size={14} /> {label}
        </button>
    );

    const Divider = () => <div className="h-px bg-slate-700 my-1" />;

    // Empty area context menu (no target)
    if (!target) {
        return (
            <div ref={menuRef} style={style} className="fixed z-[100] w-52 bg-slate-800 border border-slate-700 rounded-lg shadow-2xl context-menu-anim py-1">
                <MenuItem icon={Folder} label={t('ctx.newFolder', 'Nova Pasta')} onClick={() => onAction('new-folder')} />
                <MenuItem icon={Upload} label={t('ctx.upload', 'Carregar Arquivos')} onClick={() => onAction('upload')} />
                {hasClipboard && (
                    <>
                        <Divider />
                        <MenuItem icon={Clipboard} label={t('ctx.paste', 'Colar')} onClick={() => onAction('paste')} />
                    </>
                )}
                <Divider />
                <MenuItem icon={RefreshCw} label={t('ctx.refresh', 'Atualizar')} onClick={() => onAction('refresh')} />
            </div>
        );
    }

    const isMulti = selectedCount > 1;

    // Trash context menu
    if (isTrash) {
        return (
            <div ref={menuRef} style={style} className="fixed z-[100] w-52 bg-slate-800 border border-slate-700 rounded-lg shadow-2xl context-menu-anim py-1">
                <MenuItem icon={RotateCcw} label={t('ctx.restore', 'Restaurar')} onClick={() => onAction('restore', target)} />
                <Divider />
                <MenuItem icon={Trash2} label={t('ctx.deletePermanent', 'Excluir Permanentemente')} onClick={() => onAction('delete-forever', target)} danger />
                <Divider />
                <MenuItem icon={AlertTriangle} label={t('ctx.emptyTrash', 'Esvaziar Lixeira')} onClick={() => onAction('empty-trash', target)} danger />
            </div>
        );
    }

    return (
        <div ref={menuRef} style={style} className="fixed z-[100] w-52 bg-slate-800 border border-slate-700 rounded-lg shadow-2xl context-menu-anim py-1">
            {!isMulti && (
                <MenuItem icon={ExternalLink} label={t('ctx.open', 'Abrir')} onClick={() => onAction('open', target)} className="font-medium" />
            )}

            <MenuItem icon={Upload} label={isMulti ? `${t('ctx.download', 'Baixar')} ZIP (${selectedCount})` : t('ctx.download', 'Baixar')} onClick={() => onAction('download', target)} className="[&>svg]:rotate-180" />

            <Divider />

            {/* Clipboard Actions */}
            <MenuItem icon={Copy} label={t('ctx.copy', 'Copiar')} onClick={() => onAction('copy', target)} />
            <MenuItem icon={Scissors} label={t('ctx.cut', 'Recortar')} onClick={() => onAction('cut', target)} />
            {hasClipboard && (
                <MenuItem icon={Clipboard} label={t('ctx.paste', 'Colar')} onClick={() => onAction('paste', target)} />
            )}

            <MenuItem icon={ExternalLink} label={t('ctx.moveTo', 'Mover para...')} onClick={() => onAction('move-to', target)} />

            <Divider />

            {!isMulti && (
                <MenuItem icon={Edit2} label={t('ctx.rename', 'Renomear')} onClick={() => onAction('rename', target)} />
            )}

            <MenuItem icon={Trash2} label={`${t('ctx.delete', 'Deletar')}${isMulti ? ` (${selectedCount})` : ''}`} onClick={() => onAction('delete', target)} danger />

            <Divider />

            <MenuItem icon={Check} label={t('ctx.select', 'Selecionar')} onClick={() => onAction('select', target)} />
            <MenuItem icon={Check} label={t('ctx.selectAll', 'Selecionar Tudo')} onClick={() => onAction('select-all')} />

            <Divider />

            {!isMulti && (
                <MenuItem icon={Info} label={t('ctx.properties', 'Propriedades')} onClick={() => onAction('properties', target)} />
            )}

            {/* Tags Submenu */}
            <div className="relative group/tags">
                <button className="w-full text-left px-4 py-2 text-sm text-slate-400 hover:bg-slate-700 hover:text-white flex items-center gap-2 justify-between">
                    <span className="flex items-center gap-2"><Tag size={14} /> Tags</span>
                    <span className="text-xs">▶</span>
                </button>
                <div className="absolute left-full top-0 ml-1 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-xl hidden group-hover/tags:block py-1">
                    {tags.length === 0 && <div className="px-4 py-2 text-xs text-slate-500 italic">Nenhuma tag criada</div>}
                    {tags.map(tag => {
                        const hasTag = target.tags && target.tags.includes(tag.id);
                        return (
                            <button
                                key={tag.id}
                                onClick={() => onAction({ type: 'toggle-tag', tagId: tag.id }, target)}
                                className="w-full text-left px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 hover:text-white flex items-center gap-2"
                            >
                                <div className={`w-3 h-3 rounded-full ${tag.color}`}></div>
                                <span className="flex-1 truncate">{tag.name}</span>
                                {hasTag && <Check size={14} className="text-emerald-400" />}
                            </button>
                        );
                    })}
                </div>
            </div>

            <MenuItem
                icon={Star}
                label={isMulti ? t('ctx.star', 'Favoritar Seleção') : (target.isStarred ? 'Remover dos Favoritos' : 'Adicionar aos Favoritos')}
                onClick={() => onAction('star', target)}
                className="text-yellow-500 hover:text-yellow-400"
            />
        </div>
    );
};
