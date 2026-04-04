import { useState, useCallback } from 'react';

export function useSelection() {
    const [selectedFileIds, setSelectedFileIds] = useState([]);
    const [lastSelectedId, setLastSelectedId] = useState(null);

    const toggleSelection = useCallback((id, multiSelect = false) => {
        if (multiSelect) {
            setSelectedFileIds(prev => {
                const isSelected = prev.includes(id);
                if (isSelected) {
                    return prev.filter(i => i !== id);
                } else {
                    return [...prev, id];
                }
            });
            setLastSelectedId(id);
        } else {
            setSelectedFileIds([id]);
            setLastSelectedId(id);
        }
    }, []);

    const selectRange = useCallback((ids) => {
        setSelectedFileIds(ids);
    }, []);

    const clearSelection = useCallback(() => {
        setSelectedFileIds([]);
        setLastSelectedId(null);
    }, []);

    return { selectedFileIds, setSelectedFileIds, toggleSelection, clearSelection, selectRange, lastSelectedId };
}
