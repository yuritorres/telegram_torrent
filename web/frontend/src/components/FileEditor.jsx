import { useState, useEffect, useRef } from 'react';
import { 
  FileText, Save, X, Plus, Search, Trash2, Download, 
  Upload, FolderPlus, Edit2, Check, AlertCircle 
} from 'lucide-react';
import Editor from '@monaco-editor/react';
import axios from '../utils/axios';

export default function FileEditor() {
  const [files, setFiles] = useState([]);
  const [currentFile, setCurrentFile] = useState(null);
  const [content, setContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showNewFileDialog, setShowNewFileDialog] = useState(false);
  const [newFileName, setNewFileName] = useState('');
  const [newFileType, setNewFileType] = useState('text');
  const [notification, setNotification] = useState(null);
  const editorRef = useRef(null);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get('/api/editor/files');
      setFiles(response.data.files || []);
    } catch (error) {
      console.error('Error loading files:', error);
      showNotification('Erro ao carregar arquivos', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const loadFile = async (fileId) => {
    setIsLoading(true);
    try {
      const response = await axios.get(`/api/editor/files/${fileId}`);
      setContent(response.data.content);
      setCurrentFile({ ...response.data.metadata, file_id: fileId });
    } catch (error) {
      console.error('Error loading file:', error);
      showNotification('Erro ao carregar arquivo', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const saveFile = async () => {
    if (!currentFile) return;
    
    setIsSaving(true);
    try {
      const response = await axios.put(`/api/editor/files/${currentFile.file_id}`, { content });
      showNotification('Arquivo salvo no Telegram!', 'success');
      setCurrentFile(response.data.file);
      loadFiles();
    } catch (error) {
      console.error('Error saving file:', error);
      showNotification('Erro ao salvar arquivo', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const createFile = async () => {
    if (!newFileName.trim()) {
      showNotification('Digite um nome para o arquivo', 'error');
      return;
    }

    setIsSaving(true);
    try {
      const response = await axios.post('/api/editor/files', {
        filename: newFileName,
        content: '// Novo arquivo\n// Edite aqui...\n',
        file_type: newFileType
      });
      
      showNotification('Arquivo criado e salvo no Telegram!', 'success');
      setShowNewFileDialog(false);
      setNewFileName('');
      loadFiles();
      loadFile(response.data.file.file_id);
    } catch (error) {
      console.error('Error creating file:', error);
      showNotification('Erro ao criar arquivo', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const deleteFile = async (fileId) => {
    if (!confirm('Deseja realmente excluir este arquivo do Telegram?')) return;

    try {
      await axios.delete(`/api/editor/files/${fileId}`);
      showNotification('Arquivo excluído do Telegram', 'success');
      if (currentFile?.file_id === fileId) {
        setCurrentFile(null);
        setContent('');
      }
      loadFiles();
    } catch (error) {
      console.error('Error deleting file:', error);
      showNotification('Erro ao excluir arquivo', 'error');
    }
  };

  const searchFiles = async () => {
    if (!searchQuery.trim()) {
      loadFiles();
      return;
    }

    try {
      const response = await axios.get(`/api/editor/files/search/${encodeURIComponent(searchQuery)}`);
      setFiles(response.data.files || []);
    } catch (error) {
      console.error('Error searching files:', error);
    }
  };

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const getLanguage = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    const languageMap = {
      'js': 'javascript',
      'jsx': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'py': 'python',
      'json': 'json',
      'html': 'html',
      'css': 'css',
      'md': 'markdown',
      'yml': 'yaml',
      'yaml': 'yaml',
      'xml': 'xml',
      'sql': 'sql',
      'sh': 'shell',
      'txt': 'plaintext'
    };
    return languageMap[ext] || 'plaintext';
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
  };

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      {/* Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 ${
          notification.type === 'success' ? 'bg-green-600' : 
          notification.type === 'error' ? 'bg-red-600' : 'bg-blue-600'
        }`}>
          {notification.type === 'success' && <Check size={20} />}
          {notification.type === 'error' && <AlertCircle size={20} />}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Sidebar - File List */}
      <div className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <FileText size={24} />
              Editor de Arquivos
            </h2>
            <button
              onClick={() => setShowNewFileDialog(true)}
              className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              title="Novo arquivo"
            >
              <Plus size={20} />
            </button>
          </div>

          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Buscar arquivos..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchFiles()}
              className="w-full px-4 py-2 pl-10 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
            />
            <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
          </div>
        </div>

        {/* File List */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-gray-400">Carregando...</div>
          ) : files.length === 0 ? (
            <div className="p-4 text-center text-gray-400">
              Nenhum arquivo encontrado
            </div>
          ) : (
            <div className="divide-y divide-gray-700">
              {files.map((file) => (
                <div
                  key={file.file_id}
                  className={`p-4 hover:bg-gray-700 cursor-pointer transition-colors ${
                    currentFile?.file_id === file.file_id ? 'bg-gray-700' : ''
                  }`}
                  onClick={() => loadFile(file.file_id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{file.filename}</div>
                      <div className="text-sm text-gray-400 mt-1">
                        {formatFileSize(file.file_size)}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDate(file.updated_at)}
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteFile(file.file_id);
                      }}
                      className="p-1 hover:bg-red-600 rounded transition-colors"
                      title="Excluir"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-4 border-t border-gray-700 text-xs text-gray-400">
          💾 Arquivos salvos no Telegram
        </div>
      </div>

      {/* Editor Area */}
      <div className="flex-1 flex flex-col">
        {currentFile ? (
          <>
            {/* Editor Header */}
            <div className="bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileText size={20} />
                <div>
                  <div className="font-medium">{currentFile.filename}</div>
                  <div className="text-xs text-gray-400">
                    Última atualização: {formatDate(currentFile.updated_at)}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={saveFile}
                  disabled={isSaving}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg flex items-center gap-2 transition-colors"
                >
                  <Save size={18} />
                  {isSaving ? 'Salvando...' : 'Salvar no Telegram'}
                </button>
                <button
                  onClick={() => {
                    setCurrentFile(null);
                    setContent('');
                  }}
                  className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Monaco Editor */}
            <div className="flex-1">
              <Editor
                height="100%"
                language={getLanguage(currentFile.filename)}
                value={content}
                onChange={(value) => setContent(value || '')}
                theme="vs-dark"
                options={{
                  fontSize: 14,
                  minimap: { enabled: true },
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  tabSize: 2,
                  wordWrap: 'on'
                }}
                onMount={(editor) => {
                  editorRef.current = editor;
                }}
              />
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <FileText size={64} className="mx-auto mb-4 opacity-50" />
              <p className="text-lg">Selecione um arquivo para editar</p>
              <p className="text-sm mt-2">ou crie um novo arquivo</p>
            </div>
          </div>
        )}
      </div>

      {/* New File Dialog */}
      {showNewFileDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-96 border border-gray-700">
            <h3 className="text-xl font-bold mb-4">Novo Arquivo</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Nome do arquivo</label>
                <input
                  type="text"
                  value={newFileName}
                  onChange={(e) => setNewFileName(e.target.value)}
                  placeholder="exemplo.txt"
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Tipo</label>
                <select
                  value={newFileType}
                  onChange={(e) => setNewFileType(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                >
                  <option value="text">Texto</option>
                  <option value="code">Código</option>
                  <option value="markdown">Markdown</option>
                  <option value="json">JSON</option>
                  <option value="yaml">YAML</option>
                </select>
              </div>
            </div>

            <div className="flex gap-2 mt-6">
              <button
                onClick={createFile}
                disabled={isSaving}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg transition-colors"
              >
                {isSaving ? 'Criando...' : 'Criar'}
              </button>
              <button
                onClick={() => {
                  setShowNewFileDialog(false);
                  setNewFileName('');
                }}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
