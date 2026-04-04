import { FileSystemProvider } from './FileSystemProvider';
import { db } from '../db';
import toast from 'react-hot-toast';

export class IndexedDBProvider extends FileSystemProvider {
    constructor(workspaceId) {
        super(workspaceId);
    }

    async initialize() {
        return await db.initializeDefaults();
    }

    async list(parentId) {
        let query = { workspaceId: this.workspaceId };
        if (parentId !== undefined) query.parentId = parentId;
        return await db.files.where(query).toArray();
    }

    async listAll() {
        return await db.files.where('workspaceId').equals(this.workspaceId).toArray();
    }

    async get(fileId) {
        return await db.files.get(fileId);
    }

    async createFolder(name, parentId) {
        const newFolder = {
            id: `folder-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            parentId: parentId,
            workspaceId: this.workspaceId,
            name,
            type: 'folder',
            size: '--',
            date: new Date().toLocaleDateString()
        };
        await db.files.put(newFolder);
        return newFolder;
    }

    async saveFiles(files) {
        const preparedFiles = files.map(f => ({
            ...f,
            id: f.id || `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            workspaceId: this.workspaceId,
        }));

        await db.files.bulkPut(preparedFiles);
        return preparedFiles;
    }

    async delete(ids) {
        await db.files.bulkDelete(ids);
    }

    async rename(id, newName) {
        await db.files.update(id, { name: newName });
    }

    async move(ids, targetFolderId) {
        await db.files.where('id').anyOf(ids).modify({ parentId: targetFolderId });
        return ids;
    }

    async copy(ids, targetFolderId) {
        const files = await db.files.where('id').anyOf(ids).toArray();
        const newFiles = files.map(f => ({
            ...f,
            id: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            parentId: targetFolderId,
            date: new Date().toLocaleDateString(),
            name: f.name
        }));
        await db.files.bulkAdd(newFiles);
        return newFiles;
    }

    async getContent(id) {
        const file = await db.files.get(id);
        return file ? file.content : null;
    }

    async listStarred() {
        return await db.files
            .where({ workspaceId: this.workspaceId })
            .filter(f => f.isStarred && !f.deletedAt)
            .toArray();
    }

    async listRecent() {
        return await db.files
            .where('workspaceId').equals(this.workspaceId)
            .filter(f => !f.deletedAt && f.type !== 'folder')
            .toArray();
    }

    async listTrash() {
        return await db.files
            .where('workspaceId').equals(this.workspaceId)
            .filter(f => !!f.deletedAt)
            .toArray();
    }

    async listByTag(tagId) {
        return await db.files
            .where('workspaceId').equals(this.workspaceId)
            .filter(f => f.tags && f.tags.includes(tagId) && !f.deletedAt)
            .toArray();
    }
}
