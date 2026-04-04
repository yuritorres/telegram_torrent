import Dexie from 'dexie';

export class OmniFilesDatabase extends Dexie {
    constructor() {
        super('OmniFilesDB');

        this.version(1).stores({
            workspaces: '&id, name',
            files: '&id, parentId, workspaceId'
        });

        this.version(2).stores({
            files: '&id, parentId, workspaceId, name'
        });

        this.version(3).stores({
            files: '&id, parentId, workspaceId, name, isStarred'
        });

        this.version(4).stores({
            tags: '&id, name',
            files: '&id, parentId, workspaceId, name, isStarred, *tags'
        });

        this.version(5).stores({
            files: '&id, parentId, workspaceId, name, isStarred, *tags, deletedAt'
        });

        this.version(6).stores({
            tags: '&id, name',
            files: '&id, parentId, workspaceId, name, isStarred, *tags, deletedAt'
        });
    }

    async initializeDefaults() {
        const workspaceCount = await this.workspaces.count();
        if (workspaceCount === 0) {
            const defaultWsId = `ws-${Date.now()}`;
            await this.workspaces.add({
                id: defaultWsId,
                name: 'Meu Workspace',
                type: 'local',
                color: 'bg-blue-600',
                connections: [
                    {
                        id: `conn-${Date.now()}`,
                        serviceId: 'browser',
                        name: 'Navegador',
                        used: '0',
                        total: '500MB'
                    }
                ]
            });
            return defaultWsId;
        }
        return null;
    }
}

export const db = new OmniFilesDatabase();
