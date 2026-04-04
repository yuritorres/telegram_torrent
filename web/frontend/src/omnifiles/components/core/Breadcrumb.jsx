import React from 'react';
import { Server, ChevronRight } from 'lucide-react';

export const Breadcrumb = ({ path, onNavigate }) => (
    <div className="flex items-center text-sm text-slate-400 px-2 bg-slate-800 rounded-md border border-slate-700 h-8 flex-1 mx-4 overflow-hidden">
        <div className="flex items-center cursor-pointer hover:bg-slate-700 px-1 rounded transition-colors flex-shrink-0" onClick={() => onNavigate(-1)}>
            <Server size={14} className="mr-2 text-slate-300" /><span className="text-slate-300">Origem</span>
        </div>
        {path.map((folder, idx) => (
            <React.Fragment key={folder.id}>
                <ChevronRight size={14} className="mx-1 text-slate-600 flex-shrink-0" />
                <span onClick={() => onNavigate(idx)} className="hover:bg-slate-700 px-1 rounded cursor-pointer transition-colors whitespace-nowrap">{folder.name}</span>
            </React.Fragment>
        ))}
    </div>
);
