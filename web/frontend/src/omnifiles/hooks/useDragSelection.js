import { useState, useRef, useCallback, useEffect } from 'react';

export const useDragSelection = (onSelectRange) => {
    const [isSelecting, setIsSelecting] = useState(false);
    const [startPoint, setStartPoint] = useState(null);
    const [endPoint, setEndPoint] = useState(null);
    const containerRef = useRef(null);

    const handleMouseDown = useCallback((e) => {
        // Only left click
        if (e.button !== 0) return;

        // Ensure we are clicking on the container or a non-interactive child
        // (Interactive children should stopPropagation)

        const container = containerRef.current;
        if (!container) return;

        const rect = container.getBoundingClientRect();
        const x = e.clientX - rect.left + container.scrollLeft;
        const y = e.clientY - rect.top + container.scrollTop;

        setStartPoint({ x, y });
        setEndPoint({ x, y });
        setIsSelecting(true);
    }, []);

    const handleMouseMove = useCallback((e) => {
        if (!isSelecting || !startPoint) return;

        if (!containerRef.current) return;

        const rect = containerRef.current.getBoundingClientRect();
        // Calculate relative coordinates including scroll
        const x = e.clientX - rect.left + containerRef.current.scrollLeft;
        const y = e.clientY - rect.top + containerRef.current.scrollTop;

        setEndPoint({ x, y });
    }, [isSelecting, startPoint]);

    const handleMouseUp = useCallback(() => {
        if (isSelecting) {
            setIsSelecting(false);
            if (onSelectRange && startPoint && endPoint) {
                // Calculate selection rectangle
                const box = {
                    left: Math.min(startPoint.x, endPoint.x),
                    top: Math.min(startPoint.y, endPoint.y),
                    width: Math.abs(endPoint.x - startPoint.x),
                    height: Math.abs(endPoint.y - startPoint.y)
                };

                // Trigger selection logic (passed from parent)
                // We pass the box, parent calculates intersection
                onSelectRange(box);
            }
            setStartPoint(null);
            setEndPoint(null);
        }
    }, [isSelecting, startPoint, endPoint, onSelectRange]);

    // Attach global listeners for move/up to handle dragging outside container
    useEffect(() => {
        if (isSelecting) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
        }
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isSelecting, handleMouseMove, handleMouseUp]);

    const selectionBox = isSelecting && startPoint && endPoint ? {
        left: Math.min(startPoint.x, endPoint.x),
        top: Math.min(startPoint.y, endPoint.y),
        width: Math.abs(endPoint.x - startPoint.x),
        height: Math.abs(endPoint.y - startPoint.y)
    } : null;

    return {
        isSelecting,
        selectionBox,
        containerRef,
        handleMouseDown
    };
};
