import { Folder, Cloud, HardDrive, Zap, ArrowRight, Sparkles } from 'lucide-react';

export const WelcomeScreen = ({ onStart, onQuickStart }) => {
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
            {/* Animated background */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl animate-pulse" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/3 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
            </div>

            <div className="relative z-10 max-w-2xl w-full">
                {/* Logo */}
                <div className="text-center mb-12">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400 shadow-2xl shadow-blue-500/30 mb-6">
                        <Folder size={40} className="text-white" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-3 tracking-tight">
                        Omni<span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">Files</span>
                    </h1>
                    <p className="text-slate-400 text-lg max-w-md mx-auto">
                        Gerencie seus arquivos de forma inteligente, rápida e segura.
                    </p>
                </div>

                {/* Action Cards */}
                <div className="space-y-4">
                    {/* Quick Start */}
                    <button
                        onClick={onQuickStart}
                        className="w-full group relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 to-cyan-500 p-[1px] transition-all hover:shadow-2xl hover:shadow-blue-500/20"
                    >
                        <div className="rounded-2xl bg-gradient-to-r from-blue-600 to-cyan-500 px-6 py-5 flex items-center gap-4">
                            <div className="p-3 rounded-xl bg-white/20 backdrop-blur-sm">
                                <Zap size={24} className="text-white" />
                            </div>
                            <div className="flex-1 text-left">
                                <h3 className="text-lg font-semibold text-white">Início Rápido</h3>
                                <p className="text-blue-100/80 text-sm">Crie um workspace padrão e comece imediatamente.</p>
                            </div>
                            <ArrowRight size={20} className="text-white/70 group-hover:text-white group-hover:translate-x-1 transition-all" />
                        </div>
                    </button>

                    {/* Custom Setup */}
                    <button
                        onClick={onStart}
                        className="w-full group rounded-2xl border border-slate-700/50 bg-slate-800/40 backdrop-blur-sm hover:bg-slate-800/70 hover:border-slate-600 px-6 py-5 flex items-center gap-4 transition-all"
                    >
                        <div className="p-3 rounded-xl bg-slate-700/50">
                            <Sparkles size={24} className="text-purple-400" />
                        </div>
                        <div className="flex-1 text-left">
                            <h3 className="text-lg font-semibold text-white">Configuração Personalizada</h3>
                            <p className="text-slate-400 text-sm">Escolha nome, conexões e personalize o seu workspace.</p>
                        </div>
                        <ArrowRight size={20} className="text-slate-500 group-hover:text-slate-300 group-hover:translate-x-1 transition-all" />
                    </button>
                </div>

                {/* Features */}
                <div className="mt-10 grid grid-cols-3 gap-4">
                    {[
                        { icon: HardDrive, label: 'Arquivos Locais', desc: 'File System API' },
                        { icon: Cloud, label: 'Nuvem', desc: 'Google Drive, S3' },
                        { icon: Folder, label: 'Organizado', desc: 'Tags & Favoritos' }
                    ].map(({ icon: Icon, label, desc }) => (
                        <div key={label} className="text-center p-4 rounded-xl bg-slate-800/30 border border-slate-700/30">
                            <Icon size={20} className="text-slate-400 mx-auto mb-2" />
                            <p className="text-sm font-medium text-slate-300">{label}</p>
                            <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
                        </div>
                    ))}
                </div>

                {/* Version */}
                <p className="text-center text-slate-600 text-xs mt-8">
                    OmniFiles v1.0 — Crom Project
                </p>
            </div>
        </div>
    );
};
