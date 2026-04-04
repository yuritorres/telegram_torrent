/**
 * Abstract implementation of a File System Provider.
 * All providers (IndexedDB, Google Drive, S3, Local FS) must extend this class.
 */
export class FileSystemProvider {
    constructor(workspaceId) {
        this.workspaceId = workspaceId;
    }

    /**
     * List files in a folder.
     * @param {string} parentId - The ID of the parent folder.
     * @returns {Promise<Array>} - List of files/folders.
     */
    async list(parentId) {
        throw new Error('Method not implemented.');
    }

    /**
     * Create a new folder.
     * @param {string} name - Name of the folder.
     * @param {string} parentId - Parent folder ID.
     * @returns {Promise<Object>} - The created folder object.
     */
    async createFolder(name, parentId) {
        throw new Error('Method not implemented.');
    }

    /**
     * Save/Upload files.
     * @param {Array<Object>} files - List of file objects to save.
     * @returns {Promise<Array>} - List of saved file objects with IDs.
     */
    async saveFiles(files) {
        throw new Error('Method not implemented.');
    }

    /**
     * Delete files/folders.
     * @param {Array<string>} ids - List of IDs to delete.
     * @returns {Promise<void>}
     */
    async delete(ids) {
        throw new Error('Method not implemented.');
    }

    /**
     * Rename a file/folder.
     * @param {string} id - ID of the item.
     * @param {string} newName - New name.
     * @returns {Promise<void>}
     */
    async rename(id, newName) {
        throw new Error('Method not implemented.');
    }

    /**
     * Get a specific file's content (if not already loaded).
     * @param {string} id - File ID.
     * @returns {Promise<Blob|string>}
     */
    async getContent(id) {
        throw new Error('Method not implemented.');
    }

    /**
     * List starred files (Favorites).
     * @returns {Promise<Array>}
     */
    async listStarred() {
        throw new Error('Method not implemented.');
    }

    /**
     * List recent files.
     * @returns {Promise<Array>}
     */
    async listRecent() {
        throw new Error('Method not implemented.');
    }

    /**
     * List trashed files.
     * @returns {Promise<Array>}
     */
    async listTrash() {
        throw new Error('Method not implemented.');
    }

    /**
     * List files by tag.
     * @param {string} tagId
     * @returns {Promise<Array>}
     */
    async listByTag(tagId) {
        throw new Error('Method not implemented.');
    }
}
