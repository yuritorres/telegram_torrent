import { useState } from 'react';
import { Briefcase, ArrowRight } from 'lucide-react';

export const WorkspaceSetup = ({ onNext }) => {
    const [name, setName] = useState('');
    return (
        <div className="fixed inset-0 bg-slate-950 flex flex-col items-center justify-center p-6 z-50 animate-in fade-in duration-500">
            <div className="max-w-md w-full text-center">
                <div className="inline-flex p-4 bg-blue-600/20 rounded-2xl mb-6 ring-1 ring-blue-500/50">
                    <Briefcase size={48} className="text-blue-400" />
                </div>
                <h1 className="text-3xl font-bold text-white mb-2">Bem-vindo ao OmniFiles</h1>
                <p className="text-slate-400 mb-8">Para começar, vamos criar o seu primeiro Workspace para organizar os seus ficheiros.</p>
                <div className="text-left mb-6">
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Nome do Workspace</label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Ex: Pessoal, Trabalho, Projetos..."
                        className="w-full bg-slate-900 border border-slate-700 rounded-xl p-4 text-white placeholder-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
                        autoFocus
                        onKeyDown={(e) => e.key === 'Enter' && name && onNext(name)}
                    />
                </div>
                <button
                    onClick={() => name && onNext(name)}
                    disabled={!name}
                    className="w-full py-4 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-xl shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-2 group"
                >
                    <span>Continuar</span><ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                </button>
            </div>
        </div>
    );
};
