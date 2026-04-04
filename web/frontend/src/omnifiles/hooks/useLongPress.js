import { useRef, useCallback } from 'react';

export const useLongPress = (
    onLongPress,
    onClick,
    { shouldPreventDefault = true, delay = 500 } = {}
) => {
    const timeout = useRef();
    const target = useRef();
    const longPressTriggered = useRef(false);

    const start = useCallback(
        (event) => {
            longPressTriggered.current = false;
            if (shouldPreventDefault && event.target) {
                event.target.addEventListener('touchend', preventDefault, { passive: false });
                target.current = event.target;
            }
            timeout.current = setTimeout(() => {
                longPressTriggered.current = true;
                onLongPress(event);
            }, delay);
        },
        [onLongPress, delay, shouldPreventDefault]
    );

    const clear = useCallback(
        (event, shouldTriggerClick = true) => {
            if (timeout.current) {
                clearTimeout(timeout.current);
                timeout.current = null;
            }

            // Only fire onClick if it was a short click (not a long press)
            if (shouldTriggerClick && !longPressTriggered.current && onClick) {
                onClick(event);
            }

            if (shouldPreventDefault && target.current) {
                target.current.removeEventListener('touchend', preventDefault);
            }
        },
        [shouldPreventDefault, onClick]
    );

    return {
        onMouseDown: (e) => start(e),
        onTouchStart: (e) => start(e),
        onMouseUp: (e) => clear(e),
        onMouseLeave: (e) => clear(e, false),
        onTouchEnd: (e) => clear(e)
    };
};

const preventDefault = (e) => {
    if (!e.touches) return;
    if (e.touches.length < 2 && e.preventDefault) {
        e.preventDefault();
    }
};
