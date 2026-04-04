import { IndexedDBProvider } from './IndexedDBProvider';
import { LocalFileSystemProvider } from './LocalFileSystemProvider';
import { GoogleDriveProvider } from './GoogleDriveProvider';
import { S3Provider } from './S3Provider';

export const getProvider = (workspace) => {
    if (!workspace) return null;

    switch (workspace.type) {
        case 's3':
            return new S3Provider(workspace.id, workspace.config);
        case 'gdrive':
            return new GoogleDriveProvider(workspace.id, workspace.token);
        case 'local-fs':
            return new LocalFileSystemProvider(workspace.id, workspace.handle);
        case 'local':
        default:
            return new IndexedDBProvider(workspace.id);
    }
};
