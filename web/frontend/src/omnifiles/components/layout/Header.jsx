import React from 'react';
import { ArrowLeft, ArrowRight, Search, Plus, LayoutGrid, List as ListIcon, Menu, PanelLeft, Info, Tag, Folder, FolderPlus, FilePlus, Upload, X } from 'lucide-react';
import { Breadcrumb } from '../core/Breadcrumb';
import { useTranslation } from 'react-i18next';
import PropTypes from 'prop-types';

export const Header = ({
    currentPath,
    onNavigateBreadcrumb,
    onBack,
    onForward,
    historyIndex,
    historyLength,
    searchQuery,
    setSearchQuery,
    onCreateFolder,
    onCreateFile,
    onUpload,
    viewMode,
    setViewMode,
    onToggleSidebar,
    isSidebarOpen,
    isProcessing,
    showDetails,
    onToggleDetails,
    onOpenTagManager,
    selectedCount = 0,
    onClearSelection
}) => {
    const { t } = useTranslation();

    const [isMenuOpen, setIsMenuOpen] = React.useState(false);
    const menuRef = React.useRef(null);
    const fileInputRef = React.useRef(null);
    const folderInputRef = React.useRef(null);

    React.useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setIsMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleMenuAction = (action) => {
        setIsMenuOpen(false);
        switch (action) {
            case 'new-folder': onCreateFolder(); break;
            case 'new-file': onCreateFile && onCreateFile(); break;
            case 'upload-file': fileInputRef.current?.click(); break;
            case 'upload-folder': folderInputRef.current?.click(); break;
        }
    };

    // Selection Mode UI
    if (selectedCount > 0) {
        return (
            <header className="h-14 border-b border-blue-900/50 flex items-center px-4 justify-between bg-blue-900/20 backdrop-blur z-20 relative gap-4">
                <div className="flex items-center gap-4 text-blue-200">
                    <button onClick={onClearSelection} className="p-2 hover:bg-blue-800/50 rounded-full transition-colors" title={t('header.clearSelection', 'Desmarcar')}>
                        <X size={20} />
                    </button>
                    <span className="font-medium text-lg">
                        {selectedCount} {selectedCount === 1 ? t('header.selectedItem', 'selecionado') : t('header.selectedItems', 'selecionados')}
                    </span>
                </div>

                <div className="flex items-center gap-2">
                    {/* Add quick actions here like Trash, Move, etc? For now just X */}
                </div>
            </header>
        );
    }

    return (
        <header className="h-14 border-b border-slate-800 flex items-center px-4 justify-between bg-slate-900/95 backdrop-blur z-20 relative gap-4">
            {/* Hidden Inputs */}
            <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                multiple
                onChange={onUpload}
            />
            <input
                type="file"
                ref={folderInputRef}
                className="hidden"
                webkitdirectory=""
                directory=""
                multiple
                onChange={onUpload}
            />

            <div className="flex items-center gap-1 text-slate-400 mr-2 flex-shrink-0">
                <button
                    onClick={onToggleSidebar}
                    className={`p-1.5 hover:bg-slate-800 rounded-md mr-2 text-slate-400 hover:text-white transition-colors ${!isSidebarOpen ? 'text-blue-500' : ''}`}
                    title={isSidebarOpen ? "Fechar Menu" : "Abrir Menu"}
                >
                    <PanelLeft size={18} />
                </button>
                <div className="h-4 w-[1px] bg-slate-800 mx-1"></div>
                <button onClick={onBack} disabled={historyIndex <= 0} className="p-1.5 hover:bg-slate-800 rounded-md disabled:opacity-30"><ArrowLeft size={18} /></button>
                <button onClick={onForward} disabled={historyIndex >= historyLength - 1} className="p-1.5 hover:bg-slate-800 rounded-md disabled:opacity-30"><ArrowRight size={18} /></button>
            </div>

            <Breadcrumb path={currentPath} onNavigate={onNavigateBreadcrumb} />

            <div className="relative mx-2 hidden md:block">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <DebouncedInput
                    value={searchQuery}
                    onChange={setSearchQuery}
                    placeholder={t('header.searchPlaceholder')}
                    className="bg-slate-800 border-slate-700 border text-sm rounded-md pl-9 pr-4 py-1.5 w-64 focus:border-blue-500 outline-none text-slate-200"
                />
            </div>

            <div className="flex items-center gap-2 border-l border-slate-800 pl-4 flex-shrink-0">

                {/* Dropdown Menu */}
                <div className="relative" ref={menuRef}>
                    <button
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                        className={`flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded shadow-sm transition-colors ${isMenuOpen ? 'bg-blue-500' : ''}`}
                    >
                        <Plus size={14} />
                        <span>Novo</span>
                    </button>

                    {isMenuOpen && (
                        <div className="absolute right-0 top-full mt-2 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-xl py-1 z-50 animate-in fade-in zoom-in-95 duration-100">
                            <button onClick={() => handleMenuAction('new-folder')} className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 hover:text-white flex items-center gap-2">
                                <Folder size={16} className="text-blue-400" /> {t('header.newFolder', 'Nova Pasta')}
                            </button>
                            <button onClick={() => handleMenuAction('new-file')} className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 hover:text-white flex items-center gap-2">
                                <FilePlus size={16} className="text-emerald-400" /> {t('header.newFile', 'Novo Arquivo')}
                            </button>
                            <div className="h-px bg-slate-700 my-1"></div>
                            <button onClick={() => handleMenuAction('upload-file')} className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 hover:text-white flex items-center gap-2">
                                <Upload size={16} className="text-slate-400" /> {t('header.uploadFile', 'Upload Arquivo')}
                            </button>
                            <button onClick={() => handleMenuAction('upload-folder')} className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 hover:text-white flex items-center gap-2">
                                <FolderPlus size={16} className="text-slate-400" /> {t('header.uploadFolder', 'Upload Pasta')}
                            </button>
                        </div>
                    )}
                </div>

                <div className="flex bg-slate-800 rounded-md p-1 border border-slate-700">
                    <button onClick={() => setViewMode('grid')} className={`p-1.5 rounded ${viewMode === 'grid' ? 'bg-slate-600 text-white' : 'text-slate-400'}`}><LayoutGrid size={16} /></button>
                    <button onClick={() => setViewMode('list')} className={`p-1.5 rounded ${viewMode === 'list' ? 'bg-slate-600 text-white' : 'text-slate-400'}`}><ListIcon size={16} /></button>
                </div>
                <button
                    onClick={onOpenTagManager}
                    className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400"
                    title="Gerenciar Tags"
                >
                    <Tag size={18} />
                </button>
                <button
                    onClick={onToggleDetails}
                    className={`p-1.5 rounded-md hover:bg-slate-800 border border-transparent ${showDetails ? 'bg-slate-800 text-blue-400 border-blue-500/30' : 'text-slate-400'}`}
                    title="Detalhes"
                >
                    <Info size={18} />
                </button>
            </div>

            {/* Global Progress Bar */}
            {isProcessing && (
                <div className="absolute bottom-0 left-0 w-full h-[2px] bg-slate-800 overflow-hidden">
                    <div className="h-full bg-blue-500 animate-progress-indeterminate origin-left"></div>
                </div>
            )}
        </header>
    );
};

const DebouncedInput = ({ value: initialValue, onChange, ...props }) => {
    const [value, setValue] = React.useState(initialValue);

    React.useEffect(() => {
        setValue(initialValue);
    }, [initialValue]);

    React.useEffect(() => {
        const timeout = setTimeout(() => {
            onChange(value);
        }, 300);
        return () => clearTimeout(timeout);
    }, [value, onChange]);

    return (
        <input {...props} value={value} onChange={e => setValue(e.target.value)} />
    );
};

Header.propTypes = {
    currentPath: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired
    })).isRequired,
    onNavigateBreadcrumb: PropTypes.func.isRequired,
    onBack: PropTypes.func.isRequired,
    onForward: PropTypes.func.isRequired,
    historyIndex: PropTypes.number.isRequired,
    historyLength: PropTypes.number.isRequired,
    searchQuery: PropTypes.string.isRequired,
    setSearchQuery: PropTypes.func.isRequired,
    onCreateFolder: PropTypes.func.isRequired,
    onCreateFile: PropTypes.func, // Optional?
    onUpload: PropTypes.func, // Optional?
    viewMode: PropTypes.oneOf(['grid', 'list']).isRequired,
    setViewMode: PropTypes.func.isRequired,
    onToggleSidebar: PropTypes.func.isRequired,
    isSidebarOpen: PropTypes.bool.isRequired,
    isProcessing: PropTypes.bool,
    showDetails: PropTypes.bool,
    onToggleDetails: PropTypes.func
};

DebouncedInput.propTypes = {
    value: PropTypes.string.isRequired,
    onChange: PropTypes.func.isRequired
};
