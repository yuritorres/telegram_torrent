import { FileSystemProvider } from './FileSystemProvider';

export class LocalFileSystemProvider extends FileSystemProvider {
    constructor(workspaceId, directoryHandle) {
        super(workspaceId);
        this.directoryHandle = directoryHandle;
    }

    async verifyPermission(handle, readWrite = false) {
        if (!handle) return false;
        const options = {};
        if (readWrite) {
            options.mode = 'readwrite';
        }

        if ((await handle.queryPermission(options)) === 'granted') {
            return true;
        }

        if ((await handle.requestPermission(options)) === 'granted') {
            return true;
        }

        return false;
    }

    async list(parentId) {
        if (!this.directoryHandle) throw new Error("No directory handle");
        return await this.listAll();
    }

    async listAll() {
        if (!this.verifyPermission(this.directoryHandle)) {
            throw new Error("Permission denied");
        }

        const files = [];
        const processHandle = async (handle, path = '') => {
            for await (const entry of handle.values()) {
                const entryPath = path ? `${path}/${entry.name}` : entry.name;

                if (entry.kind === 'file') {
                    const fileData = await entry.getFile();
                    files.push({
                        id: entryPath,
                        parentId: path || null,
                        workspaceId: this.workspaceId,
                        name: entry.name,
                        type: this.getType(entry.name),
                        size: this.formatSize(fileData.size),
                        date: new Date(fileData.lastModified).toLocaleDateString(),
                        handle: entry
                    });
                } else if (entry.kind === 'directory') {
                    files.push({
                        id: entryPath,
                        parentId: path || null,
                        workspaceId: this.workspaceId,
                        name: entry.name,
                        type: 'folder',
                        size: '--',
                        date: new Date().toLocaleDateString(),
                        handle: entry
                    });
                    await processHandle(entry, entryPath);
                }
            }
        };

        await processHandle(this.directoryHandle);
        return files;
    }

    getType(name) {
        if (name.endsWith('.js') || name.endsWith('.jsx')) return 'javascript';
        if (name.endsWith('.html')) return 'html';
        if (name.endsWith('.css')) return 'css';
        if (name.endsWith('.json')) return 'json';
        if (name.endsWith('.md')) return 'markdown';
        if (name.match(/\.(jpg|jpeg|png|gif|webp)$/i)) return 'image';
        return 'file';
    }

    formatSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async getContent(id) {
        const parts = id.split('/');
        let currentHandle = this.directoryHandle;

        for (let i = 0; i < parts.length; i++) {
            const part = parts[i];
            if (i === parts.length - 1) {
                const fileHandle = await currentHandle.getFileHandle(part);
                const file = await fileHandle.getFile();

                if (file.type.startsWith('text/') ||
                    file.name.match(/\.(js|jsx|json|md|html|css|txt)$/)) {
                    return await file.text();
                }
                return file;
            } else {
                currentHandle = await currentHandle.getDirectoryHandle(part);
            }
        }
        return null;
    }

    async _traverseToHandle(pathId) {
        if (!pathId) return this.directoryHandle;
        const parts = pathId.split('/');
        let handle = this.directoryHandle;
        for (const part of parts) {
            handle = await handle.getDirectoryHandle(part);
        }
        return handle;
    }

    async createFolder(name, parentId) {
        try {
            const parentHandle = await this._traverseToHandle(parentId);
            await parentHandle.getDirectoryHandle(name, { create: true });

            const folderPath = parentId ? `${parentId}/${name}` : name;
            return {
                id: folderPath,
                parentId: parentId || null,
                workspaceId: this.workspaceId,
                name,
                type: 'folder',
                size: '--',
                date: new Date().toLocaleDateString()
            };
        } catch (error) {
            console.error('LocalFS createFolder error:', error);
            throw error;
        }
    }

    async saveFiles(files) {
        const results = [];
        for (const f of files) {
            try {
                if (f.type === 'folder') {
                    const parentHandle = await this._traverseToHandle(f.parentId);
                    await parentHandle.getDirectoryHandle(f.name, { create: true });
                    results.push(f);
                } else if (f.content) {
                    const parentHandle = await this._traverseToHandle(f.parentId);
                    const fileHandle = await parentHandle.getFileHandle(f.name, { create: true });
                    const writable = await fileHandle.createWritable();
                    await writable.write(f.content);
                    await writable.close();
                    results.push(f);
                }
            } catch (err) {
                console.error(`LocalFS saveFile error for ${f.name}:`, err);
            }
        }
        return results;
    }

    async delete(ids) {
        for (const id of ids) {
            try {
                const parts = id.split('/');
                const name = parts.pop();
                const parentPath = parts.join('/') || null;
                const parentHandle = await this._traverseToHandle(parentPath);
                await parentHandle.removeEntry(name, { recursive: true });
            } catch (err) {
                console.error(`LocalFS delete error for ${id}:`, err);
            }
        }
    }

    async rename(id, newName) {
        try {
            const parts = id.split('/');
            const oldName = parts.pop();
            const parentPath = parts.join('/') || null;
            const parentHandle = await this._traverseToHandle(parentPath);

            const oldFileHandle = await parentHandle.getFileHandle(oldName);
            const oldFile = await oldFileHandle.getFile();

            const newFileHandle = await parentHandle.getFileHandle(newName, { create: true });
            const writable = await newFileHandle.createWritable();
            await writable.write(await oldFile.arrayBuffer());
            await writable.close();

            await parentHandle.removeEntry(oldName);
        } catch (err) {
            console.error(`LocalFS rename error:`, err);
            throw err;
        }
    }
}
