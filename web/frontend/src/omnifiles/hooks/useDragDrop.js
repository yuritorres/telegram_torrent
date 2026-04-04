import { useState, useCallback } from 'react';

// Helper to scan files and folders recursively
const scanFiles = async (item, path = '') => {
    if (item.isFile) {
        return new Promise((resolve) => {
            item.file((file) => {
                resolve([{ file, path: path + file.name }]);
            });
        });
    } else if (item.isDirectory) {
        const dirReader = item.createReader();
        const entries = await new Promise((resolve) => {
            dirReader.readEntries((entries) => resolve(entries));
        });

        const results = await Promise.all(
            entries.map(entry => scanFiles(entry, path + item.name + '/'))
        );
        return results.flat();
    }
    return [];
};

export function useDragDrop(onDropFiles) {
    const [isDragging, setIsDragging] = useState(false);

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback(async (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const items = e.dataTransfer.items;
        if (items && items.length > 0) {
            const promises = [];
            for (let i = 0; i < items.length; i++) {
                const item = items[i].webkitGetAsEntry();
                if (item) {
                    promises.push(scanFiles(item));
                } else if (items[i].kind === 'file') {
                    // Fallback for non-webkit or if webkitGetAsEntry fails?
                    // actually items[i].getAsFile() returns File, no path.
                    // But webkitGetAsEntry is standard for structure.
                    // If it returns null, we skip?
                }
            }

            try {
                const results = await Promise.all(promises);
                const allFiles = results.flat();
                if (allFiles.length > 0) {
                    onDropFiles(allFiles); // Calls importDroppedFiles with [{file, path}]
                }
            } catch (err) {
                console.error("Failed to scan dropped files:", err);
            }
        } else if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            // Fallback for browsers not supporting items API (rare now)
            // Just treat as flat files
            const files = Array.from(e.dataTransfer.files).map(f => ({ file: f, path: f.name }));
            onDropFiles(files);
        }
    }, [onDropFiles]);

    return { isDragging, handleDragOver, handleDragLeave, handleDrop };
}
