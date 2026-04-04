import React from 'react';
import { Skeleton } from '../ui/Skeleton';

export const SidebarSkeleton = () => {
    return (
        <aside className="w-[260px] flex flex-col border-r border-slate-800 bg-slate-900/50 backdrop-blur-sm relative h-screen">
            <div className="p-4 border-b border-slate-800">
                <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2 block">Workspace</div>
                {/* Workspace Dropdown Skeleton */}
                <Skeleton className="w-full h-10 rounded-lg" />
            </div>

            <div className="flex-1 py-4 px-3 space-y-6">
                {/* Favorites Section */}
                <div>
                    <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-2 mb-2">Favorites</div>
                    <div className="space-y-2">
                        <Skeleton className="w-full h-8 rounded-md" />
                        <Skeleton className="w-full h-8 rounded-md" />
                    </div>
                </div>

                {/* Connections Section */}
                <div>
                    <div className="flex items-center justify-between px-2 mb-2">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Connections</div>
                    </div>
                    <div className="space-y-2">
                        <Skeleton className="w-full h-10 rounded-lg" />
                        <Skeleton className="w-full h-10 rounded-lg" />
                        <Skeleton className="w-full h-10 rounded-lg" />
                    </div>
                </div>
            </div>
        </aside>
    );
};
