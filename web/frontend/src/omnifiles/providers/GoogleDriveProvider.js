import { FileSystemProvider } from './FileSystemProvider';
import { GOOGLE_CONFIG } from '../config/google';

export class GoogleDriveProvider extends FileSystemProvider {
    constructor(workspaceId, token, connectionId) {
        super(workspaceId);
        this.token = token;
        this.connectionId = connectionId;
    }

    async list(parentId) {
        const query = parentId
            ? `'${parentId}' in parents and trashed = false`
            : "'root' in parents and trashed = false";

        console.log(`[Drive] List Query: ${query}, Token: ${this.token?.substring(0, 10)}...`);
        const response = await fetch(`https://www.googleapis.com/drive/v3/files?q=${encodeURIComponent(query)}&fields=files(id, name, mimeType, size, modifiedTime, iconLink, thumbnailLink)&pageSize=100`, {
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        });

        if (!response.ok) {
            const errorBody = await response.text();
            console.error(`[Drive] API Error: ${response.status}`, errorBody);

            if (response.status === 401) {
                throw new Error("Sessão Expirada. Por favor, reconecte sua conta Google no Painel de Configurações.");
            }

            if (response.status === 403 && errorBody.includes("accessNotConfigured")) {
                throw new Error("A API do Google Drive não está ativada no seu projeto do Google Cloud. Ative-a em: console.developers.google.com");
            }

            throw new Error(`Drive API Error: ${response.status}`);
        }

        const data = await response.json();
        console.log(`[Drive] Files Found: ${data.files?.length}`, data);

        return data.files.map(f => ({
            id: f.id,
            parentId: (parentId === 'root' || parentId === this.connectionId || !parentId) ? this.connectionId : parentId,
            workspaceId: this.workspaceId,
            name: f.name,
            type: this.mapMimeType(f.mimeType),
            size: f.size ? this.formatSize(f.size) : '--',
            date: new Date(f.modifiedTime).toLocaleDateString(),
            mimeType: f.mimeType,
            thumbnail: f.thumbnailLink,
            icon: f.iconLink
        }));
    }

    async get(fileId) {
        const response = await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}?fields=id,name,mimeType,size,modifiedTime`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });

        if (!response.ok) {
            const errorBody = await response.text();
            console.error(`[Drive] get() Error: ${response.status}`, errorBody);
            throw new Error(`Drive API Error: ${response.status}`);
        }

        return await response.json();
    }

    async debugDownload(id) {
        console.log(`[Drive] debugDownload(${id}) called`);
        let meta;
        try {
            meta = await this.get(id);
            console.log(`[Drive] Metadata parsed:`, meta);
        } catch (e) {
            console.error('[Drive] getContent: metadata fetch failed', e);
            return null;
        }

        if (!meta || !meta.mimeType) {
            console.error('[Drive] getContent: invalid metadata', meta);
            return null;
        }

        if (meta.mimeType.startsWith('application/vnd.google-apps.')) {
            console.log(`[Drive] Exporting Google Doc: ${meta.mimeType}`);
            if (meta.mimeType.includes('document')) {
                const res = await fetch(`https://www.googleapis.com/drive/v3/files/${id}/export?mimeType=text/plain`, {
                    headers: { 'Authorization': `Bearer ${this.token}` }
                });
                console.log(`[Drive] Export status: ${res.status}`);
                if (!res.ok) {
                    console.error(`[Drive] Export failed: ${res.status}`);
                    return null;
                }
                return await res.text();
            }
            console.warn(`[Drive] Unsupported Google Doc type: ${meta.mimeType}`);
            return "Visualização não disponível para arquivos nativos do Google (planilhas/slides).";
        }

        console.log(`[Drive] Downloading normal file (alt=media)...`);
        const response = await fetch(`https://www.googleapis.com/drive/v3/files/${id}?alt=media`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });

        console.log(`[Drive] Download status: ${response.status}`);
        if (!response.ok) {
            console.error(`[Drive] Download failed: ${response.status}`);
            return null;
        }

        if (meta.mimeType.startsWith('text/') || meta.name.endsWith('.js') || meta.name.endsWith('.json') || meta.name.endsWith('.md')) {
            console.log(`[Drive] Reading as text...`);
            return await response.text();
        }

        console.log(`[Drive] Reading as blob...`);
        const blob = await response.blob();
        console.log(`[Drive] Blob received:`, blob);
        return blob;
    }

    mapMimeType(mime) {
        if (mime === 'application/vnd.google-apps.folder') return 'folder';
        if (mime.startsWith('image/')) return 'image';
        if (mime.includes('pdf')) return 'pdf';
        if (mime.includes('javascript') || mime.includes('json') || mime.includes('html')) return 'code';
        if (mime.startsWith('text/')) return 'text';
        if (mime.startsWith('application/vnd.google-apps.')) return 'gdoc';
        return 'file';
    }

    formatSize(bytes) {
        if (!bytes) return '0 B';
        const k = 1024;
        const s = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + s[i];
    }

    async createFolder(name, parentId) {
        const actualParent = (parentId && (parentId.startsWith('conn-') || parentId === this.connectionId)) ? 'root' : (parentId || 'root');

        const metadata = {
            name: name,
            mimeType: 'application/vnd.google-apps.folder',
            parents: [actualParent]
        };

        const response = await fetch('https://www.googleapis.com/drive/v3/files', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(metadata)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Drive Create Folder Error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        return {
            id: data.id,
            name: data.name,
            type: 'folder',
            parentId: parentId,
            workspaceId: this.workspaceId,
            date: new Date().toLocaleDateString(),
            size: '--'
        };
    }

    async delete(ids) {
        for (const id of ids) {
            await fetch(`https://www.googleapis.com/drive/v3/files/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${this.token}` }
            });
        }
    }

    async trash(ids) {
        for (const id of ids) {
            await fetch(`https://www.googleapis.com/drive/v3/files/${id}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ trashed: true })
            });
        }
    }

    async rename(id, newName) {
        await fetch(`https://www.googleapis.com/drive/v3/files/${id}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: newName })
        });
    }

    async move(ids, targetFolderId) {
        const target = (targetFolderId && !targetFolderId.startsWith('conn-')) ? targetFolderId : 'root';

        for (const id of ids) {
            const res = await fetch(`https://www.googleapis.com/drive/v3/files/${id}?fields=parents`, {
                headers: { 'Authorization': `Bearer ${this.token}` }
            });
            const data = await res.json();
            const previousParents = data.parents ? data.parents.join(',') : '';

            await fetch(`https://www.googleapis.com/drive/v3/files/${id}?addParents=${target}&removeParents=${previousParents}`, {
                method: 'PATCH',
                headers: { 'Authorization': `Bearer ${this.token}` }
            });
        }
        return ids;
    }

    async copy(ids, targetFolderId) {
        const target = (targetFolderId && !targetFolderId.startsWith('conn-')) ? targetFolderId : 'root';
        const newFiles = [];

        for (const id of ids) {
            const res = await fetch(`https://www.googleapis.com/drive/v3/files/${id}/copy`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ parents: [target] })
            });
            const data = await res.json();
            newFiles.push({
                id: data.id,
                name: data.name,
                mimeType: data.mimeType,
                parentId: targetFolderId,
                workspaceId: this.workspaceId,
            });
        }
        return newFiles;
    }

    async saveFiles(files) {
        const uploaded = [];
        const idMap = {};

        for (const file of files) {
            let targetParentId = file.parentId;
            if (idMap[targetParentId]) {
                targetParentId = idMap[targetParentId];
            }

            const actualParent = (targetParentId && targetParentId.startsWith('conn-')) ? 'root' : (targetParentId || 'root');

            const metadata = {
                name: file.name,
                parents: [actualParent]
            };

            if (file.type === 'folder') {
                metadata.mimeType = 'application/vnd.google-apps.folder';
            }

            const formData = new FormData();
            formData.append('metadata', new Blob([JSON.stringify(metadata)], { type: 'application/json' }));

            if (file.type !== 'folder') {
                let contentBlob = file.content;
                if (typeof contentBlob === 'string') {
                    contentBlob = new Blob([contentBlob], { type: 'text/plain' });
                } else if (!(contentBlob instanceof Blob) && !(contentBlob instanceof File)) {
                    contentBlob = new Blob([''], { type: 'text/plain' });
                }
                formData.append('file', contentBlob);
            }

            const response = await fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                },
                body: formData
            });

            if (!response.ok) {
                console.error(`Upload error for ${file.name}:`, await response.text());
                continue;
            }

            const data = await response.json();

            if (file.id) {
                idMap[file.id] = data.id;
            }

            uploaded.push({
                id: data.id,
                name: data.name,
                type: this.mapMimeType(data.mimeType),
                parentId: file.parentId,
                workspaceId: this.workspaceId,
                date: new Date().toLocaleDateString(),
                size: this.formatSize(data.size || file.sizeRaw || 0),
                content: file.content
            });
        }
        return uploaded;
    }

    async _performList(query) {
        console.log(`[Drive] Query: ${query}`);
        const response = await fetch(`https://www.googleapis.com/drive/v3/files?q=${encodeURIComponent(query)}&fields=files(id, name, mimeType, size, modifiedTime, iconLink, thumbnailLink)&pageSize=100`, {
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        });

        if (!response.ok) {
            const errorBody = await response.text();
            console.error(`[Drive] API Error: ${response.status}`, errorBody);
            throw new Error(`Drive API Error: ${response.status}`);
        }

        const data = await response.json();
        return data.files.map(f => ({
            id: f.id,
            parentId: 'root',
            workspaceId: this.workspaceId,
            name: f.name,
            type: this.mapMimeType(f.mimeType),
            size: f.size ? this.formatSize(f.size) : '--',
            date: new Date(f.modifiedTime).toLocaleDateString(),
            mimeType: f.mimeType,
            thumbnail: f.thumbnailLink,
            icon: f.iconLink
        }));
    }

    async listStarred() {
        return await this._performList("starred = true and trashed = false");
    }

    async listRecent() {
        return await this._performList("trashed = false and mimeType != 'application/vnd.google-apps.folder' order by modifiedTime desc");
    }

    async listTrash() {
        return await this._performList("trashed = true");
    }

    async listByTag(tagId) {
        return [];
    }
}
