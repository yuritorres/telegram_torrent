import { FileSystemProvider } from './FileSystemProvider';
import { S3Client, ListObjectsV2Command, PutObjectCommand, DeleteObjectCommand, GetObjectCommand, CopyObjectCommand } from "@aws-sdk/client-s3";

export class S3Provider extends FileSystemProvider {
    constructor(workspaceId, config) {
        super(workspaceId);
        this.config = config;
        this.client = new S3Client({
            region: config.region,
            credentials: {
                accessKeyId: config.accessKeyId,
                secretAccessKey: config.secretAccessKey
            }
        });
    }

    async list(parentId) {
        const prefix = parentId ? (parentId.endsWith('/') ? parentId : `${parentId}/`) : '';

        const command = new ListObjectsV2Command({
            Bucket: this.config.bucket,
            Prefix: prefix,
            Delimiter: '/'
        });

        try {
            const data = await this.client.send(command);
            const files = [];

            if (data.CommonPrefixes) {
                data.CommonPrefixes.forEach(p => {
                    const name = p.Prefix.split('/').filter(Boolean).pop();
                    files.push({
                        id: p.Prefix,
                        parentId: parentId || null,
                        workspaceId: this.workspaceId,
                        name: name,
                        type: 'folder',
                        size: '--',
                        date: '--',
                        mimeType: 'application/x-directory'
                    });
                });
            }

            if (data.Contents) {
                data.Contents.forEach(obj => {
                    if (obj.Key === prefix) return;

                    const name = obj.Key.split('/').pop();
                    files.push({
                        id: obj.Key,
                        parentId: parentId || null,
                        workspaceId: this.workspaceId,
                        name: name,
                        type: this.getType(name),
                        size: this.formatSize(obj.Size),
                        date: new Date(obj.LastModified).toLocaleDateString(),
                        mimeType: 'application/octet-stream'
                    });
                });
            }

            return files;
        } catch (error) {
            console.error("S3 List Error:", error);
            throw new Error(`S3 Error: ${error.message}`);
        }
    }

    async get(fileId) {
        const command = new GetObjectCommand({
            Bucket: this.config.bucket,
            Key: fileId
        });
        const response = await this.client.send(command);
        return response;
    }

    async getContent(id) {
        try {
            const response = await this.get(id);
            const str = await response.Body.transformToString();
            return str;
        } catch (error) {
            console.error("S3 GetContent Error", error);
            throw error;
        }
    }

    async saveFiles(files) {
        const results = [];
        for (const file of files) {
            try {
                let key = file.parentId ? `${file.parentId}${file.name}` : file.name;
                if (file.parentId && !file.parentId.endsWith('/') && !key.includes('/')) {
                    key = `${file.parentId}/${file.name}`;
                }

                const command = new PutObjectCommand({
                    Bucket: this.config.bucket,
                    Key: key,
                    Body: file.content
                });

                await this.client.send(command);
                results.push({ id: key, name: file.name, status: 'uploaded' });
            } catch (error) {
                console.error("S3 Upload Error", error);
                throw error;
            }
        }
        return results;
    }

    async createFolder(name, parentId) {
        const prefix = parentId ? (parentId.endsWith('/') ? parentId : `${parentId}/`) : '';
        const key = `${prefix}${name}/`;

        const command = new PutObjectCommand({
            Bucket: this.config.bucket,
            Key: key,
            Body: ''
        });

        await this.client.send(command);
        return {
            id: key,
            name: name,
            type: 'folder',
            parentId: parentId || null,
            workspaceId: this.workspaceId
        };
    }

    async delete(ids) {
        for (const id of ids) {
            const command = new DeleteObjectCommand({
                Bucket: this.config.bucket,
                Key: id
            });
            await this.client.send(command);
        }
    }

    async rename(id, newName) {
        const oldKey = id;
        const pathParts = oldKey.split('/');
        pathParts.pop();
        const newKey = [...pathParts, newName].join('/');

        try {
            const copyCommand = new CopyObjectCommand({
                Bucket: this.config.bucket,
                CopySource: `${this.config.bucket}/${oldKey}`,
                Key: newKey
            });
            await this.client.send(copyCommand);

            const deleteCommand = new DeleteObjectCommand({
                Bucket: this.config.bucket,
                Key: oldKey
            });
            await this.client.send(deleteCommand);
        } catch (error) {
            console.error("S3 Rename Error", error);
            throw error;
        }
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
}
