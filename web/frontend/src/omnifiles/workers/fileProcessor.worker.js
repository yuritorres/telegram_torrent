/* eslint-disable no-restricted-globals */

// Web Worker for file processing (Hashing & Thumbnails)

self.onmessage = async (e) => {
    const { id, file, type } = e.data;

    try {
        if (type === 'HASH') {
            const hash = await calculateHash(file);
            self.postMessage({ type: 'HASH_RESULT', id, payload: hash });
        } else if (type === 'THUMBNAIL') {
            const thumbnail = await generateThumbnail(file);
            self.postMessage({ type: 'THUMBNAIL_RESULT', id, payload: thumbnail });
        }
    } catch (error) {
        self.postMessage({ type: 'ERROR', id, error: error.message });
    }
};

async function calculateHash(file) {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
}

async function generateThumbnail(file) {
    // Basic thumbnail generation using ImageBitmap
    // This is efficient and works in workers.
    try {
        const bitmap = await createImageBitmap(file);

        // Define max dimensions
        const MAX_WIDTH = 300;
        const MAX_HEIGHT = 300;

        let width = bitmap.width;
        let height = bitmap.height;

        if (width > height) {
            if (width > MAX_WIDTH) {
                height *= MAX_WIDTH / width;
                width = MAX_WIDTH;
            }
        } else {
            if (height > MAX_HEIGHT) {
                width *= MAX_HEIGHT / height;
                height = MAX_HEIGHT;
            }
        }

        // Use OffscreenCanvas if available
        if (typeof OffscreenCanvas !== 'undefined') {
            const canvas = new OffscreenCanvas(width, height);
            const ctx = canvas.getContext('2d');
            ctx.drawImage(bitmap, 0, 0, width, height);
            const blob = await canvas.convertToBlob({ type: 'image/jpeg', quality: 0.7 });
            return blob;
        } else {
            // Fallback? Workers usually support OffscreenCanvas in modern browsers.
            return null;
        }
    } catch (err) {
        console.error("Thumbnail error", err);
        return null; // Silent fail for non-images or errors
    }
}
