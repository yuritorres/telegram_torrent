import { useState, useEffect, useCallback } from 'react';
import { db } from '../db';
import toast from 'react-hot-toast';

export const useTags = () => {
    const [tags, setTags] = useState([]);

    // Load tags on mount
    useEffect(() => {
        const loadTags = async () => {
            const allTags = await db.tags.toArray();
            setTags(allTags);
        };
        loadTags();
    }, []);

    const addTag = useCallback(async (name, color) => {
        const newTag = {
            id: `tag-${Date.now()}`,
            name,
            color
        };
        try {
            await db.tags.add(newTag);
            setTags(prev => [...prev, newTag]);
            toast.success("Tag criada!");
            return newTag;
        } catch (error) {
            console.error("Erro ao criar tag:", error);
            toast.error("Erro ao criar tag.");
        }
    }, []);

    const updateTag = useCallback(async (id, updates) => {
        try {
            await db.tags.update(id, updates);
            setTags(prev => prev.map(t => t.id === id ? { ...t, ...updates } : t));
            toast.success("Tag atualizada!");
        } catch (error) {
            console.error("Erro ao atualizar tag:", error);
            toast.error("Erro ao atualizar tag.");
        }
    }, []);

    const deleteTag = useCallback(async (id) => {
        try {
            await db.tags.delete(id);
            setTags(prev => prev.filter(t => t.id !== id));
            // Optional: Remove this tag from all files?
            // For now, let's leave valid references in files, 
            // but normally we should cleanup. 
            // Performing bulk update on all files with this tag might be expensive.
            // Let's defer cleanup for now or do it if it becomes an issue.
            toast.success("Tag removida!");
        } catch (error) {
            console.error("Erro ao remover tag:", error);
            toast.error("Erro ao remover tag.");
        }
    }, []);

    const toggleFileTag = useCallback(async (file, tagId) => {
        if (!file) return;
        const currentTags = file.tags || [];
        let newTags;
        let action;

        if (currentTags.includes(tagId)) {
            newTags = currentTags.filter(t => t !== tagId);
            action = 'removed';
        } else {
            newTags = [...currentTags, tagId];
            action = 'added';
        }

        try {
            await db.files.update(file.id, { tags: newTags });
            // Note: This won't automatically update 'files' state in useFileSystem 
            // unless we trigger a refresh or useFileSystem observes DB changes.
            // usage: component calls this, then maybe calls a refreshFile in useFileSystem?
            // Or useFileSystem should export a generic updateFile?
            return newTags;
        } catch (error) {
            console.error("Erro ao alterar tag do arquivo:", error);
            toast.error("Erro ao atualizar tags.");
            throw error;
        }
    }, []);

    return {
        tags,
        addTag,
        updateTag,
        deleteTag,
        toggleFileTag
    };
};
