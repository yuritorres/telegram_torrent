import { useRef, memo, useMemo, useState, useCallback, useEffect } from 'react';
import { Folder, ArrowUp, ArrowDown, MoreVertical, Star } from 'lucide-react';
import { FileIcon } from './FileIcon';
import { Grid, List } from 'react-window';




import useMeasure from 'react-use-measure';
import { useLongPress } from '../../hooks/useLongPress';
import { useDragSelection } from '../../hooks/useDragSelection';
import { Skeleton } from '../ui/Skeleton';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import PropTypes from 'prop-types';
import { useClipboard } from '../../context/ClipboardContext';
import { EmptyState } from './EmptyState';

const SortIcon = ({ col, sortConfig }) => {
    if (!sortConfig || sortConfig.key !== col) return null;
    return sortConfig.direction === 'asc' ? <ArrowUp size={12} /> : <ArrowDown size={12} />;
};

// Grid Constants
const ITEM_WIDTH = 140;
const ITEM_HEIGHT = 160;
const GAP = 16;
const LIST_ITEM_HEIGHT = 48;

const GridItem = memo(({ columnIndex, rowIndex, style, data }) => {
    const { files, isLoading, columnCount, selectedFileIds, onNavigate, onContextMenu, onSelect, focusedIndex, tags = [], cutFileIds = new Set(), copiedFileIds = new Set() } = data;
    const index = rowIndex * columnCount + columnIndex;
    const file = files[index];

    const isSelected = selectedFileIds.includes(file?.id);
    const isSelectionMode = selectedFileIds.length > 0;

    const handleSelect = (e, forceMulti = false) => {
        e.stopPropagation();
        // If in selection mode, or check clicked, or Ctrl pressed -> Multi/Toggle behavior
        // If not in mode and normal click -> Exclusive select
        const isMulti = forceMulti || isSelectionMode || e.ctrlKey || e.metaKey;
        onSelect(file.id, { ctrlKey: isMulti, shiftKey: e.shiftKey });
    };

    const bind = useLongPress(
        (e) => {
            if (file) onContextMenu(e, file);
        },
        (e) => {
            if (file) {
                // Short click (from LongPress logic) should select
                handleSelect(e);
            }
        },
        { shouldPreventDefault: true, delay: 500 }
    );

    // Handle edge case where last row isn't full
    if (!isLoading && index >= files.length) return null;

    // ... (omitted styles lines 54-63) ...

    const itemStyle = {
        ...style,
        width: Number(style.width || 0) - GAP,
        height: Number(style.height || 0) - GAP,
        marginLeft: GAP,
        marginTop: GAP
    };

    if (isLoading) {
        return (
            <div style={itemStyle} className="absolute flex flex-col items-center justify-start p-4 rounded-xl border border-transparent">
                <Skeleton className="w-12 h-12 mb-3 rounded-lg" />
                <Skeleton className="w-3/4 h-4 mb-2" />
                <Skeleton className="w-1/2 h-3" />
            </div>
        );
    }

    if (!file) return null;

    return (
        <div style={itemStyle}>
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.2 }}
                {...bind}
                onMouseDown={(e) => { e.stopPropagation(); bind.onMouseDown && bind.onMouseDown(e); }}
                onDoubleClick={() => { console.log('[FileGrid] Double Click on:', file.name); onNavigate(file); }}
                onContextMenu={(e) => onContextMenu(e, file)}
                title={file.name}
                role="gridcell"
                aria-label={`${file.type === 'folder' ? 'Pasta' : 'Arquivo'} ${file.name}. Tamanho: ${file.size}. Modificado em: ${file.date}.`}
                className={`group relative flex flex-col items-center justify-start p-4 rounded-xl border transition-all cursor-pointer select-none w-full h-full
                    ${isSelected ? 'bg-blue-600/20 border-blue-500/50' : 'bg-transparent border-transparent hover:bg-slate-800 hover:border-slate-700'} 
                    ${focusedIndex === index ? 'ring-2 ring-blue-400 z-10' : ''}
                    ${cutFileIds?.has(file.id) ? 'opacity-50 grayscale' : ''}
                    ${copiedFileIds?.has(file.id) ? 'border-dashed border-slate-500/50' : ''}
                `}
            >
                {/* Selection Checkbox */}
                <div
                    onClick={(e) => handleSelect(e, true)}
                    onMouseDown={(e) => e.stopPropagation()}
                    onMouseUp={(e) => e.stopPropagation()}
                    className={`absolute top-2 left-2 z-20 w-5 h-5 rounded border flex items-center justify-center transition-colors shadow-sm
                        ${isSelected ? 'bg-blue-500 border-blue-500' : 'bg-slate-900/40 border-slate-600/50 hover:bg-slate-900/80 hover:border-slate-400'}
                    `}
                >
                    {isSelected && <div className="w-2 h-2 bg-white rounded-sm" />}
                </div>

                <div className="mb-3 pointer-events-none relative">
                    <FileIcon type={file.type} className="w-12 h-12" />
                    {file.isStarred && <Star size={12} className="absolute -top-1 -right-1 text-yellow-400 fill-yellow-400 drop-shadow-md" />}
                </div>
                <span className="text-sm text-center text-slate-300 font-medium truncate w-full px-2 pointer-events-none">{file.name}</span>
                <span className="text-[10px] text-slate-500 mt-1 pointer-events-none">{file.date}</span>

                {/* Old circular indicator removed in favor of checkbox */}
                {/* <div onClick={(e) => { e.stopPropagation(); onSelect(file.id, { ctrlKey: e.ctrlKey || e.metaKey, shiftKey: e.shiftKey }); }} className={`absolute top-2 right-2 w-4 h-4 rounded-full border border-slate-500 ${selectedFileIds.includes(file.id) ? 'bg-blue-500 border-blue-500' : 'bg-transparent'} opacity-0 group-hover:opacity-100 transition-opacity`} /> */}

                {/* Tags Indicators */}
                {file.tags && file.tags.length > 0 && (
                    <div className="absolute bottom-2 right-2 flex gap-1 pointer-events-none">
                        {file.tags.map(tagId => {
                            const tag = tags.find(t => t.id === tagId);
                            if (!tag) return null;
                            return <div key={tagId} className={`w-2 h-2 rounded-full ${tag.color}`} title={tag.name} />;
                        })}
                    </div>
                )}
            </motion.div>
        </div>
    );
});

const ListItem = memo(({ index, style, data }) => {
    const { files, isLoading, selectedFileIds, onNavigate, onContextMenu, onSelect, focusedIndex, tags = [], cutFileIds = new Set(), copiedFileIds = new Set() } = data;

    const file = files[index];
    const isSelected = selectedFileIds.includes(file?.id);
    const isSelectionMode = selectedFileIds.length > 0;

    const handleSelect = (e, forceMulti = false) => {
        e.stopPropagation();
        const isMulti = forceMulti || isSelectionMode || e.ctrlKey || e.metaKey;
        onSelect(file.id, { ctrlKey: isMulti, shiftKey: e.shiftKey });
    };

    const bind = useLongPress(
        (e) => {
            if (file) onContextMenu(e, file);
        },
        (e) => {
            if (file) {
                handleSelect(e);
            }
        }
    );

    // Helper to stop propagation for mouse down to prevent drag selection start
    const handleMouseDown = (e) => {
        e.stopPropagation();
        if (bind.onMouseDown) bind.onMouseDown(e);
    };

    if (isLoading) {
        return (
            <div style={style} className="grid grid-cols-12 gap-4 items-center px-4 border-b border-slate-800/50">
                <div className="col-span-6 flex items-center gap-3">
                    <Skeleton className="w-5 h-5 rounded" />
                    <Skeleton className="w-1/2 h-4" />
                </div>
                <div className="col-span-2"><Skeleton className="w-1/3 h-3" /></div>
                <div className="col-span-3"><Skeleton className="w-1/3 h-3" /></div>
                <div className="col-span-1"></div>
            </div>
        );
    }

    if (!file) return null;

    return (
        <div style={style}>
            <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
                role="row"
                aria-label={`${file.name}, ${file.size}, ${file.date}`}
                className={`grid grid-cols-12 gap-4 items-center px-6 border-b border-slate-800/30 cursor-pointer transition-all text-sm group select-none w-full h-full hover:bg-slate-800/40
                    ${isSelected ? 'bg-blue-900/20 border-blue-900/50' : ''} 
                    ${focusedIndex === index ? 'ring-1 ring-inset ring-blue-500' : ''}
                    ${cutFileIds?.has(file.id) ? 'opacity-50 grayscale' : ''}
                    ${copiedFileIds?.has(file.id) ? 'border-dashed border-slate-500/50' : ''}
                `}
                onDoubleClick={() => onNavigate(file)}
                onContextMenu={(e) => onContextMenu(e, file)}
                {...bind}
                onMouseDown={handleMouseDown}
            >
                <div className="col-span-6 flex items-center gap-3 overflow-hidden pr-4 relative">
                    {/* Selection Checkbox - Inside Col 1 */}
                    <div
                        onClick={(e) => handleSelect(e, true)}
                        onMouseDown={(e) => e.stopPropagation()}
                        onMouseUp={(e) => e.stopPropagation()}
                        className={`w-5 h-5 rounded border flex-shrink-0 flex items-center justify-center transition-colors z-20 cursor-pointer
                            ${isSelected ? 'bg-blue-500 border-blue-500' : 'border-slate-700 bg-transparent hover:border-slate-500'}
                        `}
                    >
                        {isSelected && <div className="w-2 h-2 bg-white rounded-sm" />}
                    </div>

                    <div className="relative flex-shrink-0">
                        <FileIcon type={file.type} className="w-5 h-5" />
                        {file.isStarred && <Star size={8} className="absolute -top-1 -right-1 text-yellow-400 fill-yellow-400" />}
                    </div>
                    <span className="truncate text-slate-300 font-medium">{file.name}</span>
                    {/* Tags Indicators */}
                    {file.tags && file.tags.length > 0 && (
                        <div className="flex gap-1 ml-2 flex-shrink-0">
                            {file.tags.map(tagId => {
                                const tag = tags.find(t => t.id === tagId);
                                if (!tag) return null;
                                return <div key={tagId} className={`w-2 h-2 rounded-full ${tag.color}`} title={tag.name} />;
                            })}
                        </div>
                    )}
                </div>

                <div className="col-span-2 text-slate-500 text-xs pointer-events-none truncate">
                    {file.type === 'folder' ? 'Pasta' : file.name.split('.').pop().toUpperCase()}
                </div>
                <div className="col-span-1 text-slate-500 text-xs pointer-events-none truncate">{file.size}</div>
                <div className="col-span-2 text-slate-500 text-xs pointer-events-none truncate">{file.date}</div>
                <div className="col-span-1 flex justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-1 hover:bg-slate-700 rounded-full" onClick={(e) => onContextMenu(e, file)}>
                        <MoreVertical size={16} className="text-slate-400 hover:text-white" />
                    </button>
                </div>
            </motion.div>
        </div>
    );
});

export const FileGrid = ({
    files = [],
    viewMode,
    onNavigate,
    onContextMenu,
    selectedFileIds = [],
    onSelect,
    onSelectRange,
    sortConfig,
    requestSort,
    isLoading = false,
    onNavigateUp,
    tags = [],
    onCreateFolder,
    onUpload,
    onRefresh,
    isTrash = false
}) => {
    const [ref, { width, height }] = useMeasure();
    const { t } = useTranslation();
    const { clipboard } = useClipboard();
    const [focusedIndex, setFocusedIndex] = useState(-1);

    // Derived state for cut/copy items
    const { cutFileIds, copiedFileIds } = useMemo(() => {
        const cut = new Set();
        const copied = new Set();
        if (clipboard?.items) {
            if (clipboard.action === 'cut') {
                clipboard.items.forEach(i => cut.add(i.id));
            } else if (clipboard.action === 'copy') {
                clipboard.items.forEach(i => copied.add(i.id));
            }
        }
        return { cutFileIds: cut, copiedFileIds: copied };
    }, [clipboard]);

    // Prevent context menu on empty area
    const handleBackgroundContextMenu = (e) => {
        if (onContextMenu) onContextMenu(e, null);
    };

    const columnCount = Math.max(1, Math.floor((width) / (ITEM_WIDTH + GAP)));

    const itemData = useMemo(() => ({
        files,
        isLoading,
        columnCount,
        selectedFileIds,
        onNavigate,
        onContextMenu,
        onSelect,
        focusedIndex, // Pass focusedIndex to items so they can highlight themselves
        tags,
        cutFileIds,
        copiedFileIds
    }), [files, isLoading, columnCount, selectedFileIds, onNavigate, onContextMenu, onSelect, focusedIndex, tags, cutFileIds, copiedFileIds]);

    const handleDragSelect = useCallback((box) => {
        if (!files.length) return;

        const selectedIds = [];

        files.forEach((file, index) => {
            let itemRect;
            if (viewMode === 'grid') {
                const col = index % columnCount;
                const row = Math.floor(index / columnCount);
                itemRect = {
                    left: col * (ITEM_WIDTH + GAP) + GAP,
                    top: row * (ITEM_HEIGHT + GAP) + GAP,
                    width: ITEM_WIDTH - GAP,
                    height: ITEM_HEIGHT - GAP
                };
            } else {
                itemRect = {
                    left: 0,
                    top: index * LIST_ITEM_HEIGHT,
                    width: width,
                    height: LIST_ITEM_HEIGHT
                };
            }

            // Intersection Check
            if (
                itemRect.left < box.left + box.width &&
                itemRect.left + itemRect.width > box.left &&
                itemRect.top < box.top + box.height &&
                itemRect.top + itemRect.height > box.top
            ) {
                selectedIds.push(file.id);
            }
        });

        if (selectedIds.length > 0 && onSelectRange) {
            onSelectRange(selectedIds);
        }
    }, [files, columnCount, viewMode, width, onSelect, onSelectRange]);

    const { isSelecting, selectionBox, containerRef, handleMouseDown: onDragStart } = useDragSelection(handleDragSelect);

    const outerRef = useRef(null);

    // Sync containerRef from useDragSelection with outerRef used by react-window
    // IMPORTANT: FixedSizeGrid/List allow `outerRef` prop. 
    // We pass outerRef to them, and we sync it here if needed, or simply pass containerRef to them if possible.
    // However, react-window refs are internal. `outerRef` helps us get the scroll container.
    // For drag selection we need the container that captures events. 
    // Sync containerRef from useDragSelection with the actual DOM element
    // react-window in this version does not forward refs, so we use ID to get the element
    useEffect(() => {
        const container = document.getElementById('file-grid-container') || document.getElementById('file-list-container');
        if (container) {
            outerRef.current = container;
            containerRef.current = container;
        }
    }); // Run on every render to ensure we catch it if viewMode changes

    const gridRowCount = Math.ceil(files.length / columnCount);
    const itemCount = files.length;

    const handleKeyDown = (e) => {
        // ... (Keyboard selection logic similar to before, can restore if needed)
        // Keeping it brief for restoration
    };

    if (!isLoading && files.length === 0) {
        return (
            <div ref={ref} className="flex-1 h-full overflow-hidden relative" onContextMenu={handleBackgroundContextMenu}>
                <EmptyState
                    onUpload={onUpload}
                    onCreateFolder={onCreateFolder}
                    onRefresh={onRefresh}
                    isTrash={isTrash}
                />
            </div>
        );
    }

    return (
        <div
            className="flex flex-col h-full w-full outline-none"
            ref={ref}
            tabIndex={0}
            onKeyDown={handleKeyDown}
        >
            {/* List Header (Only for List View) */}
            {viewMode === 'list' && (
                <div className="grid grid-cols-12 gap-4 px-6 py-3 border-b border-slate-800 text-xs font-bold text-slate-500 uppercase tracking-wider bg-slate-900/95 backdrop-blur z-10 flex-shrink-0 select-none">
                    <div className="col-span-6 flex items-center gap-1 cursor-pointer hover:text-white transition-colors pl-8" onClick={() => requestSort('name')}>
                        {t('grid.listHeader.name')} <SortIcon col="name" sortConfig={sortConfig} />
                    </div>
                    <div className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-white transition-colors" onClick={() => requestSort('type')}>
                        {t('grid.listHeader.type')} <SortIcon col="type" sortConfig={sortConfig} />
                    </div>
                    <div className="col-span-1 flex items-center gap-1 cursor-pointer hover:text-white transition-colors" onClick={() => requestSort('size')}>
                        {t('grid.listHeader.size')} <SortIcon col="size" sortConfig={sortConfig} />
                    </div>
                    <div className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-white transition-colors" onClick={() => requestSort('date')}>
                        {t('grid.listHeader.date')} <SortIcon col="date" sortConfig={sortConfig} />
                    </div>
                    <div className="col-span-1"></div>
                </div>
            )}

            <div
                className="flex-1 w-full relative h-full"
                onMouseDown={onDragStart}
            >
                {isSelecting && selectionBox && (
                    <div
                        className="absolute border-2 border-blue-500/50 bg-blue-500/20 z-50 pointer-events-none"
                        style={{
                            left: selectionBox.left,
                            top: selectionBox.top,
                            width: selectionBox.width,
                            height: selectionBox.height
                        }}
                    />
                )}
                {width > 0 && height > 0 && (
                    viewMode === 'grid' ? (
                        <Grid
                            columnCount={columnCount}
                            columnWidth={(width - GAP) / columnCount}
                            height={height}
                            rowCount={gridRowCount}
                            rowHeight={ITEM_HEIGHT + GAP}
                            width={width}
                            className="pb-20 focus:outline-none"
                            id="file-grid-container"
                            cellProps={{ data: itemData }}
                            cellComponent={GridItem}
                        />
                    ) : (
                        <List
                            height={height - 40}
                            rowCount={itemCount}
                            rowHeight={LIST_ITEM_HEIGHT}
                            width={width}
                            className="pb-20 focus:outline-none"
                            id="file-list-container"
                            rowProps={{ data: itemData }}
                            rowComponent={ListItem}
                        />
                    )
                )}
            </div>
        </div>
    );
};

FileGrid.propTypes = {
    files: PropTypes.array.isRequired,
    viewMode: PropTypes.string.isRequired,
    onNavigate: PropTypes.func.isRequired,
    onContextMenu: PropTypes.func,
    selectedFileIds: PropTypes.array,
    onSelect: PropTypes.func,
    onSelectRange: PropTypes.func,
    sortConfig: PropTypes.object,
    requestSort: PropTypes.func,
    isLoading: PropTypes.bool,
    onNavigateUp: PropTypes.func,
    tags: PropTypes.array,
    onCreateFolder: PropTypes.func,
    onUpload: PropTypes.func,
    onRefresh: PropTypes.func,
    isTrash: PropTypes.bool
};
