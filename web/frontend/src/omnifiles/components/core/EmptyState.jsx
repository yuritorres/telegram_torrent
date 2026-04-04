import { FolderPlus, Upload, RefreshCw, FolderOpen } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const EmptyState = ({ onUpload, onCreateFolder, onRefresh, onOpenLocal, isTrash = false }) => {
    const { t } = useTranslation();

    if (isTrash) {
        return (
            <div className="flex flex-col items-center justify-center py-20 animate-in fade-in zoom-in duration-300">
                <div className="w-24 h-24 bg-slate-800 rounded-full flex items-center justify-center mb-6">
                    <FolderOpen size={48} className="text-slate-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-300 mb-2">{t('grid.emptyTrashTitle', 'A Lixeira está vazia')}</h3>
                <p className="text-slate-500 max-w-sm text-center">
                    {t('grid.emptyTrashDesc', 'Arquivos excluídos aparecerão aqui.')}
                </p>
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center justify-center py-20 animate-in fade-in zoom-in duration-300">
            <div className="w-24 h-24 bg-slate-800 rounded-full flex items-center justify-center mb-6">
                <FolderOpen size={48} className="text-slate-600" />
            </div>
            <h3 className="text-xl font-bold text-slate-300 mb-2">{t('grid.emptyTitle', 'Esta pasta está vazia')}</h3>
            <p className="text-slate-500 max-w-sm text-center mb-8">
                {t('grid.emptyDesc', 'Comece por adicionar ficheiros ou criar uma nova organização.')}
            </p>

            <div className="flex flex-wrap gap-4 justify-center">
                <button
                    onClick={onUpload}
                    className="flex items-center gap-2 px-5 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-all hover:scale-105 shadow-lg shadow-blue-900/20"
                >
                    <Upload size={20} />
                    {t('ctx.upload', 'Carregar Arquivos')}
                </button>
                <button
                    onClick={onCreateFolder}
                    className="flex items-center gap-2 px-5 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-medium transition-all hover:scale-105 border border-slate-700"
                >
                    <FolderPlus size={20} />
                    {t('ctx.newFolder', 'Nova Pasta')}
                </button>
                {/* <button 
                    onClick={onOpenLocal}
                    className="flex items-center gap-2 px-5 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-medium transition-all hover:scale-105 border border-slate-700"
                >
                    <FolderOpen size={20} />
                    {t('sidebar.openLocalFolder', 'Abrir Local')}
                </button> */}
            </div>

            <button
                onClick={onRefresh}
                className="mt-8 text-slate-500 hover:text-slate-400 text-sm flex items-center gap-2 transition-colors"
            >
                <RefreshCw size={14} />
                {t('ctx.refresh', 'Atualizar Lista')}
            </button>
        </div>
    );
};
