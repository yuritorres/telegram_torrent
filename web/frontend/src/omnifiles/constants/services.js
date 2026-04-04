import { HardDrive, Laptop, Cloud, Database, Server } from 'lucide-react';

export const SERVICE_CATALOG = [
    { id: 'browser', name: 'Navegador Local', icon: HardDrive, color: 'text-emerald-400', desc: 'Ficheiros temporários neste navegador' },
    { id: 'local-fs', name: 'Sistema de Ficheiros', icon: Laptop, color: 'text-blue-400', desc: 'Acesso direto a uma pasta do PC' },
    { id: 'google-drive', name: 'Google Drive', icon: Cloud, color: 'text-blue-500', desc: 'Armazenamento na nuvem do Google' },
    { id: 'dropbox', name: 'Dropbox', icon: Database, color: 'text-indigo-500', desc: 'Sincronização de ficheiros', comingSoon: true },
    { id: 'aws-s3', name: 'AWS S3', icon: Server, color: 'text-orange-500', desc: 'Object storage para developers', comingSoon: true },
];
