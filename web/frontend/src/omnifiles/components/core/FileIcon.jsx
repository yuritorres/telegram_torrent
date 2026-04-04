import { Folder, File, FileText, Image, Video } from 'lucide-react';

export const FileIcon = ({ type, className }) => {
    switch (type) {
        case 'folder': return <Folder className={`${className} text-yellow-500 fill-yellow-500/20`} />;
        case 'image': return <Image className={`${className} text-purple-400`} />;
        case 'video': return <Video className={`${className} text-red-400`} />;
        case 'pdf': return <FileText className={`${className} text-red-500`} />;
        case 'text': return <FileText className={`${className} text-slate-400`} />;
        default: return <File className={`${className} text-slate-400`} />;
    }
};
