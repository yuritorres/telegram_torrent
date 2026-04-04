
export const formatBytes = (bytes, decimals = 2) => {
    if (!+bytes) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
};

export const formatDate = (dateString) => {
    if (!dateString) return '-';
    // If it's already "Hoje" or specific string, return as is
    if (dateString === 'Hoje' || dateString === 'Ontem') return dateString;

    // Try to parse if it's a date object or timestamp
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return dateString; // Return original if not valid date
        return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
    } catch (e) {
        return dateString;
    }
};
