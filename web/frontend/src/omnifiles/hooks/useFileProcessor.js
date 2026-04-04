import { useEffect, useRef, useCallback } from 'react';

export const useFileProcessor = () => {
    const workerRef = useRef(null);
    const pendingPromises = useRef(new Map());

    useEffect(() => {
        // Initialize Worker
        // Note: Vite handles worker imports with ?worker suffix or new Worker() constructor with relative path.
        // We need to point to the file location correctly.
        workerRef.current = new Worker(new URL('../workers/fileProcessor.worker.js', import.meta.url), { type: 'module' });

        workerRef.current.onmessage = (e) => {
            const { type, id, payload, error } = e.data;
            if (pendingPromises.current.has(id)) {
                const { resolve, reject } = pendingPromises.current.get(id);
                pendingPromises.current.delete(id);

                if (type === 'ERROR') {
                    reject(new Error(error));
                } else {
                    resolve(payload);
                }
            }
        };

        return () => {
            // Cleanup: terminate worker when hook unmounts? 
            // Better to keep it alive if global, but here it's per hook usage.
            // If used in useFileSystem (global), it persists.
            if (workerRef.current) workerRef.current.terminate();
        };
    }, []);

    const processFile = useCallback((file, taskType = 'HASH') => {
        return new Promise((resolve, reject) => {
            if (!workerRef.current) {
                reject(new Error("Worker not initialized"));
                return;
            }

            const id = `${taskType}-${file.name}-${Date.now()}-${Math.random()}`;
            pendingPromises.current.set(id, { resolve, reject });

            workerRef.current.postMessage({ id, file, type: taskType });
        });
    }, []);

    return {
        calculateHash: (file) => processFile(file, 'HASH'),
        generateThumbnail: (file) => processFile(file, 'THUMBNAIL')
    };
};
