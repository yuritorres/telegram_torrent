const Skeleton = ({ className, ...props }) => {
    return (
        <div
            className={`animate-pulse bg-slate-800/50 rounded-md ${className}`}
            {...props}
        />
    );
};

export { Skeleton };
