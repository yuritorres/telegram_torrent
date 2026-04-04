import { X, Download, FileText, Image as ImageIcon } from 'lucide-react';
import { useState, useEffect } from 'react';
import DOMPurify from 'dompurify';

export const FilePreviewModal = ({ file, onClose }) => {
    const [contentUrl, setContentUrl] = useState(null);
    const [isLargeFile, setIsLargeFile] = useState(false);
    const [textContent, setTextContent] = useState('');

    useEffect(() => {
        if (!file) return;

        // Reset state
        setContentUrl(null);
        setIsLargeFile(false);
        setTextContent('');

        if (file.content instanceof Blob || file.content instanceof File) {
            if (file.type === 'image' || file.type === 'pdf' || file.name.endsWith('.pdf')) {
                const url = URL.createObjectURL(file.content);
                setContentUrl(url);
                return () => URL.revokeObjectURL(url);
            } else {
                // Try to read as text if small (< 2MB)
                if (file.size < 2 * 1024 * 1024) {
                    const reader = new FileReader();
                    reader.onload = (e) => setTextContent(e.target.result);
                    reader.onerror = () => setIsLargeFile(true);
                    reader.readAsText(file.content);
                } else {
                    setIsLargeFile(true);
                }
            }
        } else if (typeof file.content === 'string') {
            if (file.content.startsWith('data:image')) {
                setContentUrl(file.content);
            } else {
                setTextContent(file.content);
            }
        }
    }, [file]);

    const handleDownload = () => {
        if (!file) return;

        let blob = null;
        if (file.content instanceof Blob || file.content instanceof File) {
            blob = file.content;
        } else if (typeof file.content === 'string') {
            blob = new Blob([file.content], { type: 'text/plain' });
            if (file.content.startsWith('data:')) {
                fetch(file.content).then(res => res.blob()).then(b => {
                    const url = URL.createObjectURL(b);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = file.name;
                    a.click();
                    URL.revokeObjectURL(url);
                });
                return;
            }
        }

        if (blob) {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.name;
            a.click();
            URL.revokeObjectURL(url);
        }
    };

    if (!file) return null;

    return (
        <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200" onClick={onClose}>
            <div className="bg-slate-900 w-[95%] md:w-full max-w-5xl h-[85vh] md:h-[80vh] rounded-2xl border border-slate-700 shadow-2xl flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>
                <div className="h-14 border-b border-slate-700 flex items-center justify-between px-4 bg-slate-900 shrink-0">
                    <div className="flex items-center gap-2 overflow-hidden">
                        {file.type === 'image' ? <ImageIcon size={18} className="text-blue-400" /> : <FileText size={18} className="text-slate-400" />}
                        <span className="font-medium text-slate-200 truncate pr-4">{file.name}</span>
                        <span className="text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full">{file.size}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleDownload}
                            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors flex items-center gap-2"
                            title="Baixar"
                        >
                            <Download size={20} />
                            <span className="hidden sm:inline text-sm">Baixar</span>
                        </button>
                        <div className="w-px h-6 bg-slate-800 mx-1"></div>
                        <button onClick={onClose} className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
                            <X size={20} />
                        </button>
                    </div>
                </div>

                <div className="flex-1 bg-slate-950/50 relative overflow-hidden flex items-center justify-center">
                    {file.type === 'image' ? (
                        <div className="w-full h-full flex items-center justify-center p-4">
                            <img src={contentUrl || file.content} className="max-h-full max-w-full object-contain shadow-2xl" alt={file.name} />
                        </div>
                    ) : (file.type === 'pdf' || file.name.endsWith('.pdf')) ? (
                        <div className="w-full h-full p-4">
                            {contentUrl ? (
                                <iframe src={contentUrl} className="w-full h-full rounded-xl border border-slate-700 bg-white" title={file.name}></iframe>
                            ) : (
                                <div className="w-full h-full flex items-center justify-center">
                                    <div className="bg-slate-800/50 p-8 rounded-2xl border border-slate-700 inline-flex flex-col items-center text-center">
                                        <FileText size={64} className="text-slate-600 mb-4" />
                                        <h3 className="text-xl font-medium text-slate-200 mb-2">Carregando visualização...</h3>
                                        <p className="text-slate-400 mb-6 max-w-md">
                                            Se a visualização não carregar, faça o download do arquivo.
                                        </p>
                                        <button
                                            onClick={handleDownload}
                                            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-colors flex items-center gap-2"
                                        >
                                            <Download size={20} />
                                            Baixar PDF
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : isLargeFile ? (
                        <div className="text-center p-8">
                            <div className="bg-slate-800/50 p-8 rounded-2xl border border-slate-700 inline-flex flex-col items-center">
                                <FileText size={64} className="text-slate-600 mb-4" />
                                <h3 className="text-xl font-medium text-slate-200 mb-2">Pré-visualização não disponível</h3>
                                <p className="text-slate-400 mb-6 max-w-md">
                                    Este arquivo é muito grande ou está em formato binário. <br />
                                    Por favor faça o download para visualizar.
                                </p>
                                <button
                                    onClick={handleDownload}
                                    className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-colors flex items-center gap-2"
                                >
                                    <Download size={20} />
                                    Baixar Arquivo ({file.size})
                                </button>
                            </div>
                        </div>
                    ) : file.name.endsWith('.html') ? (
                        <div
                            className="w-full h-full overflow-auto p-4 custom-scrollbar bg-white text-black"
                            dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(textContent || file.content) }}
                        />
                    ) : (
                        <div className="w-full h-full overflow-auto p-4 custom-scrollbar bg-slate-900">
                            <pre className="text-slate-300 text-sm font-mono whitespace-pre-wrap break-words">{textContent || "Carregando conteúdo..."}</pre>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
